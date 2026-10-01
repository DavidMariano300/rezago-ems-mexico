"""Distancia de cada localidad al plantel de media superior más cercano.

Salidas:
  datos/limpio/distancia_localidad.csv   una fila por localidad
  datos/limpio/distancia_municipal.csv   agregado municipal, ponderado por 15-17

POR QUÉ ESTA VARIABLE Y NO "AULAS DISPONIBLES"

La matriz de consistencia del proyecto operacionaliza la infraestructura escolar
como alumnos por docente y aulas disponibles. Son indicadores de la CALIDAD de
la escuela a la que ya asistes, y ninguno captura el obstáculo que en Guerrero
manda: que la escuela quede lejos. Un municipio de La Montaña puede tener
excelente razón de alumnos por docente en su única preparatoria y a la vez tener
la mitad de sus adolescentes a dos horas de camino de ella.

La distancia se construye a nivel LOCALIDAD, que es donde vive la gente, y se
agrega al municipio ponderando por población de 15 a 17 años. Así un municipio
grande con una prepa en la cabecera y cincuenta rancherías aisladas no queda
descrito por el promedio simple de sus localidades.

SUPUESTOS, TODOS CONSERVADORES

- Distancia geodésica (línea recta), no por carretera. En la sierra de Guerrero
  el tiempo real de traslado es mucho mayor que la línea recta, así que esta
  medida SUBESTIMA el obstáculo. Es un sesgo hacia el cero: si de todas formas
  aparece un efecto, no es por exageración de la variable.
- Un plantel se ubica en el centroide de su localidad, que es la precisión que
  da el F911 (reporta clave de localidad, no domicilio georreferenciado).
- Se consideran planteles de TODO el estado, sin importar el municipio, porque
  un adolescente cruza el límite municipal si la prepa de al lado está más
  cerca. Restringir al propio municipio inventaría distancias.
- El INEGI reserva la población de 15-17 de 1,421 localidades muy pequeñas por
  confidencialidad. Para no descartarlas se imputa con la razón municipal
  P_15A17/POBTOT, y se reporta cuánta población queda imputada.

Uso:
    .venv/bin/python src/04_distancia.py
"""

from __future__ import annotations

import re
import zipfile

import numpy as np
import pandas as pd

from carga import CRUDO, LIMPIO, RAIZ, f911_ems
from municipios import a_panel, cve_inegi

CICLO_REFERENCIA = "2023-2024"
RADIO_TIERRA_KM = 6371.0
UMBRALES_KM = (5, 10, 20)

_DMS = re.compile(r"(\d+)°(\d+)'([\d.]+)\"\s*([NSEWO])")


def dms_a_decimal(s: pd.Series) -> pd.Series:
    """Convierte 99°53'11.608\" W a grados decimales con signo.

    El ITER usa O de Oeste en algunos productos y W en otros; se aceptan ambas.
    """
    ext = s.astype(str).str.strip().str.extract(_DMS)
    dec = (pd.to_numeric(ext[0], errors="coerce")
           + pd.to_numeric(ext[1], errors="coerce") / 60
           + pd.to_numeric(ext[2], errors="coerce") / 3600)
    return dec.where(~ext[3].isin(["S", "W", "O"]), -dec)


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Distancia geodésica entre dos conjuntos de puntos, en km (matriz n×m)."""
    la1, lo1 = np.radians(lat1)[:, None], np.radians(lon1)[:, None]
    la2, lo2 = np.radians(lat2)[None, :], np.radians(lon2)[None, :]
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def localidades() -> pd.DataFrame:
    with zipfile.ZipFile(CRUDO / "inegi_iter_guerrero_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig", low_memory=False)

    # LOC 0000 es total municipal; 9998/9999 son agregados de localidades de una
    # y dos viviendas, que no tienen ubicación y no pueden entrar al cálculo.
    d = d[(d.MUN != "000") & (d.LOC != "0000") & (~d.LOC.isin(["9998", "9999"]))].copy()

    out = pd.DataFrame({
        "cve_inegi": cve_inegi(d.ENTIDAD, d.MUN).values,
        "cve_loc": d.LOC.str.zfill(4).values,
        "nom_loc": d.NOM_LOC.values,
        "lat": dms_a_decimal(d.LATITUD).values,
        "lon": dms_a_decimal(d.LONGITUD).values,
        "pob_total": pd.to_numeric(d.POBTOT.replace({"*": None, "N/D": None}),
                                   errors="coerce").values,
        "pob_15a17": pd.to_numeric(d.P_15A17.replace({"*": None, "N/D": None}),
                                   errors="coerce").values,
    })

    # Imputación de la población reservada, con la razón 15-17/total del municipio.
    razon = (out.groupby("cve_inegi")
             .apply(lambda g: g.pob_15a17.sum() / max(g.pob_total.sum(), 1),
                    include_groups=False)
             .rename("razon_mun"))
    out = out.merge(razon, on="cve_inegi", how="left")
    out["pob_15a17_imputada"] = out.pob_15a17.isna()
    out["pob_15a17_est"] = out.pob_15a17.fillna(out.pob_total * out.razon_mun)
    return out.drop(columns=["razon_mun"])


def planteles() -> pd.DataFrame:
    e = f911_ems(CICLO_REFERENCIA)
    p = e[e.alumnos > 0][["cv_mun", "cv_loc", "entidad"]].copy()
    p["cve_inegi"] = cve_inegi(p.entidad, p.cv_mun)
    p["cve_loc"] = p.cv_loc.str.zfill(4)
    return p[["cve_inegi", "cve_loc"]].drop_duplicates()


def main() -> int:
    loc = localidades()
    pl = planteles()

    # Las coordenadas de los planteles se toman de la localidad donde están.
    sede = pl.merge(loc[["cve_inegi", "cve_loc", "lat", "lon", "nom_loc"]],
                    on=["cve_inegi", "cve_loc"], how="left")
    sin_coord = sede.lat.isna().sum()
    sede = sede.dropna(subset=["lat", "lon"])

    print(f"Localidades de Guerrero con ubicación : {loc.lat.notna().sum():,} "
          f"de {len(loc):,}")
    print(f"Localidades sede de plantel de EMS    : {len(sede):,}"
          + (f"  ({sin_coord} sin cruce al ITER, excluida)" if sin_coord else ""))
    imp = loc.pob_15a17_imputada.sum()
    print(f"Población 15-17 imputada por reserva  : "
          f"{loc.loc[loc.pob_15a17_imputada, 'pob_15a17_est'].sum():,.0f} "
          f"en {imp:,} localidades "
          f"({100*loc.loc[loc.pob_15a17_imputada,'pob_15a17_est'].sum()/loc.pob_15a17_est.sum():.1f}% del total)")

    calc = loc.dropna(subset=["lat", "lon"]).copy()
    d = haversine_km(calc.lat.values, calc.lon.values, sede.lat.values, sede.lon.values)
    calc["dist_km"] = d.min(axis=1)
    idx = d.argmin(axis=1)
    calc["plantel_mun"] = sede.cve_inegi.values[idx]
    calc["plantel_loc"] = sede.nom_loc.values[idx]
    # Un adolescente que cruza el límite municipal para estudiar: dato en sí mismo.
    calc["cruza_municipio"] = calc.plantel_mun != calc.cve_inegi

    calc.to_csv(LIMPIO / "distancia_localidad.csv", index=False, encoding="utf-8")

    print(f"\n=== Distancia al plantel más cercano (localidades, n={len(calc):,}) ===")
    s = calc.dist_km
    print(f"  mediana={s.median():>6.2f} km   media={s.mean():>6.2f} km   "
          f"p90={s.quantile(.9):>6.2f} km   max={s.max():>6.1f} km")
    print(f"  localidades con plantel propio (0 km): {int((s == 0).sum()):,}")

    w = calc.pob_15a17_est
    print(f"\n=== Ponderado por población de 15 a 17 años ===")
    orden = np.argsort(s.values)
    acum = np.cumsum(w.values[orden]) / w.sum()
    mediana_pond = s.values[orden][np.searchsorted(acum, 0.5)]
    print(f"  distancia media    : {np.average(s, weights=w):>6.2f} km")
    print(f"  distancia mediana  : {mediana_pond:>6.2f} km")
    for u in UMBRALES_KM:
        pct = 100 * w[s > u].sum() / w.sum()
        print(f"  a más de {u:>2} km      : {pct:>6.2f}% de la población 15-17 "
              f"({w[s > u].sum():>8,.0f} personas)")
    print(f"  vive en localidad que cruza límite municipal para la prepa más cercana:"
          f" {100*w[calc.cruza_municipio].sum()/w.sum():.1f}%")

    # --- Agregado municipal ---
    g = calc.groupby("cve_inegi")
    mun = pd.DataFrame({
        "dist_media_pond": g.apply(
            lambda x: np.average(x.dist_km, weights=x.pob_15a17_est)
            if x.pob_15a17_est.sum() > 0 else np.nan, include_groups=False),
        "dist_mediana_simple": g.dist_km.median(),
        "dist_max": g.dist_km.max(),
        "localidades": g.size(),
        "pob_15a17_loc": g.pob_15a17_est.sum(),
    })
    for u in UMBRALES_KM:
        mun[f"pct_15a17_mas_{u}km"] = g.apply(
            lambda x: 100 * x.pob_15a17_est[x.dist_km > u].sum() / x.pob_15a17_est.sum()
            if x.pob_15a17_est.sum() > 0 else np.nan, include_groups=False)
    mun["pct_15a17_cruza_mun"] = g.apply(
        lambda x: 100 * x.pob_15a17_est[x.cruza_municipio].sum() / x.pob_15a17_est.sum()
        if x.pob_15a17_est.sum() > 0 else np.nan, include_groups=False)
    mun = mun.reset_index()
    mun["cve_inegi"] = a_panel(mun.cve_inegi)
    mun.to_csv(LIMPIO / "distancia_municipal.csv", index=False, encoding="utf-8")

    corte = pd.read_csv(LIMPIO / "corte_municipal.csv", dtype={"cve_inegi": str})
    j = corte.merge(mun, on="cve_inegi", how="left")

    print(f"\n=== Municipios con mayor distancia media ponderada ===")
    top = j.nlargest(8, "dist_media_pond")[
        ["nom_mun", "dist_media_pond", "pct_15a17_mas_10km", "abandono", "pct_hli"]]
    print(top.to_string(index=False, float_format=lambda x: f"{x:>8.2f}"))

    print(f"\n=== Correlación de la distancia con el abandono (n={len(j)}) ===")
    vs = ["dist_media_pond", "dist_max", "pct_15a17_mas_5km",
          "pct_15a17_mas_10km", "pct_15a17_mas_20km", "pct_15a17_cruza_mun"]
    print(f"  {'variable':24s} {'Spearman':>10s} {'pond. matrícula':>17s}")
    for v in vs:
        sp = j[v].corr(j.abandono, method="spearman")
        ok = j[[v, "abandono", "alumnos"]].dropna()
        x, y, wt = ok[v].values, ok.abandono.values, ok.alumnos.values
        mx, my = np.average(x, weights=wt), np.average(y, weights=wt)
        wc = (np.average((x - mx) * (y - my), weights=wt)
              / np.sqrt(np.average((x - mx) ** 2, weights=wt)
                        * np.average((y - my) ** 2, weights=wt)))
        print(f"  {v:24s} {sp:>+10.3f} {wc:>+17.3f}")

    print(f"\nEscritos:")
    print(f"  {(LIMPIO/'distancia_localidad.csv').relative_to(RAIZ)}  ({len(calc):,} filas)")
    print(f"  {(LIMPIO/'distancia_municipal.csv').relative_to(RAIZ)}  ({len(mun)} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
