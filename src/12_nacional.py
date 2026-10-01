"""Construye la base municipal nacional: los 2,469 municipios de México.

Salidas:
  datos/limpio/nacional_localidades.csv   distancias por localidad
  datos/limpio/nacional_municipios.csv    base del modelo, un renglón por municipio

POR QUÉ ESTA BASE Y NO LA DE GUERRERO

El objetivo del proyecto es identificar municipios propensos al rezago en el
acceso a la educación media superior, con un método replicable en cualquier
parte del país. Eso exige dos cosas que el análisis estatal no da: cobertura
nacional, y suficientes unidades para validar el modelo en territorio que no vio
durante el entrenamiento.

LA VARIABLE DEPENDIENTE, Y POR QUÉ NO ES LA DESERCIÓN DEL FORMATO 911

El planteamiento original del proyecto pedía predecir la tasa de deserción
municipal construida con el Formato 911. Se intentó y no funciona: esa tasa tiene
R² ajustado de 0.002 en corte transversal y 0.017 dentro de municipios en panel.
Dos causas documentadas la vuelven inservible a nivel municipal:

  - Ruido de agregación. Los municipios con menos de 300 alumnos presentan una
    desviación estándar de 6.78 puntos entre ciclos, contra 1.43 en los de más
    de 5,000. En la mitad de los municipios del país la tasa es casi solo ruido.
  - Sesgo de atribución territorial. El Formato 911 registra planteles, no
    alumnos, de modo que quien estudia fuera de su municipio se contabiliza en el
    municipio de la escuela.

Se usa en su lugar la **tasa de inasistencia escolar de 15 a 17 años** del Censo
2020: se mide por lugar de residencia, existe para todos los municipios, y no
depende de registros administrativos. Mide el resultado acumulado de no
inscribirse y de abandonar, que es justamente lo que interesa focalizar.

Uso:
    .venv/bin/python src/12_nacional.py
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from carga import LIMPIO, RAIZ, coneval, f911_nacional, iter_nacional
from municipios import cve_inegi

CICLO = "2023-2024"
RADIO_TIERRA_KM = 6371.0
UMBRALES_KM = (5, 10, 20)
_DMS = r"(\d+)°(\d+)'([\d.]+)\"\s*([NSEWO])"


def num(s):
    return pd.to_numeric(pd.Series(s).replace({"*": None, "N/D": None}), errors="coerce")


def dms_a_decimal(s: pd.Series) -> pd.Series:
    ext = s.astype(str).str.strip().str.extract(_DMS)
    dec = (pd.to_numeric(ext[0], errors="coerce")
           + pd.to_numeric(ext[1], errors="coerce") / 60
           + pd.to_numeric(ext[2], errors="coerce") / 3600)
    return dec.where(~ext[3].isin(["S", "W", "O"]), -dec)


def distancia_minima(origen: pd.DataFrame, sedes: pd.DataFrame) -> np.ndarray:
    """Distancia de cada localidad al plantel más cercano, en km.

    Con ~190,000 localidades y ~10,000 sedes, la fuerza bruta son 1,900 millones
    de pares. Un BallTree con métrica haversine resuelve lo mismo de forma exacta
    en segundos, porque descarta regiones enteras del espacio sin medirlas.
    """
    s = sedes.dropna(subset=["lat", "lon"])
    arbol = BallTree(np.radians(s[["lat", "lon"]].values), metric="haversine")
    d, _ = arbol.query(np.radians(origen[["lat", "lon"]].values), k=1)
    return d[:, 0] * RADIO_TIERRA_KM


def localidades() -> pd.DataFrame:
    d = iter_nacional(solo_municipales=False)
    o = pd.DataFrame({
        "cve_inegi": cve_inegi(d.ENTIDAD, d.MUN).values,
        "cve_ent": d.ENTIDAD.str.zfill(2).values,
        "nom_ent": d.NOM_ENT.values,
        "cve_loc": d.LOC.str.zfill(4).values,
        "lat": dms_a_decimal(d.LATITUD).values,
        "lon": dms_a_decimal(d.LONGITUD).values,
        "altitud": num(d.ALTITUD).values,
        "pob_total": num(d.POBTOT).values,
        "pob_15a17": num(d.P_15A17).values,
        "pob_12a14": num(d.P_12A14).values,
    })
    # El INEGI reserva por confidencialidad la población de localidades muy
    # pequeñas. Se imputa con la razón del propio municipio para no perderlas del
    # ponderador, y se marca cuántas son.
    razon = (o.groupby("cve_inegi")
             .apply(lambda g: g.pob_15a17.sum() / max(g.pob_total.sum(), 1),
                    include_groups=False).rename("r"))
    o = o.merge(razon, on="cve_inegi", how="left")
    o["imputada"] = o.pob_15a17.isna()
    o["peso_15a17"] = o.pob_15a17.fillna(o.pob_total * o.r)
    return o.drop(columns="r").dropna(subset=["lat", "lon"]).reset_index(drop=True)


def municipios() -> pd.DataFrame:
    """Totales municipales del ITER, ya convertidos a tasas."""
    d = iter_nacional(solo_municipales=True)

    def pct(a, b):
        x, y = num(d[a]).values, num(d[b]).values
        return 100 * x / np.where(y > 0, y, np.nan)

    o = pd.DataFrame({
        "cve_inegi": cve_inegi(d.ENTIDAD, d.MUN).values,
        "cve_ent": d.ENTIDAD.str.zfill(2).values,
        "nom_ent": d.NOM_ENT.values,
        "nom_mun": d.NOM_MUN.values,
        "pob_total": num(d.POBTOT).values,
        "pob_15a17": num(d.P_15A17).values,
        "pob_12a14": num(d.P_12A14).values,
    })
    # Variable dependiente. El censo reporta quién ASISTE en las edades
    # posobligatorias y quién NO ASISTE en las obligatorias; se homologa todo a
    # tasa de inasistencia, que es la que se quiere focalizar.
    o["inasistencia_15a17"] = 100 - pct("P15A17A", "P_15A17")
    o["inasistencia_12a14"] = pct("P12A14NOA", "P_12A14")
    o["inasistencia_6a11"] = pct("P6A11_NOA", "P_6A11")

    o["pct_hli"] = pct("P3YM_HLI", "P_3YMAS")
    o["pct_sin_escolaridad"] = pct("P15YM_SE", "P_15YMAS")
    o["grado_prom_escolaridad"] = num(d.GRAPROES).values
    o["pct_desocupacion"] = pct("PDESOCUP", "PEA")
    o["pct_pea"] = pct("PEA", "P_15YMAS")
    o["pct_internet"] = pct("VPH_INTER", "TVIVPARHAB")
    o["pct_piso_tierra"] = pct("VPH_PISODT", "TVIVPARHAB")
    o["pct_auto"] = pct("VPH_AUTOM", "TVIVPARHAB")
    o["pct_sin_salud"] = pct("PSINDER", "POBTOT")
    o["pct_jefa_mujer"] = pct("HOGJEF_F", "TOTHOG")
    o["pct_discapacidad"] = pct("PCON_DISC", "POBTOT")
    o["personas_por_hogar"] = num(d.POBTOT).values / np.where(
        num(d.TOTHOG).values > 0, num(d.TOTHOG).values, np.nan)
    return o


def contexto_coneval() -> pd.DataFrame:
    irs = coneval("coneval_irs_municipal_2020.csv")[
        ["cve_inegi", "irs", "i_sdsalud", "i_ptierra", "i_noagua", "i_nodren"]]
    irs = irs.rename(columns={"irs": "indice_rezago_social"})

    pob = coneval("coneval_pobreza_municipal.csv")
    pob = pob[pob.periodo == "2020-01-01"][
        ["cve_inegi", "pobreza_porcentaje", "pobreza_extrema_porcentaje",
         "carencia_alimentacion_nutritiva_calidad_porcentaje"]]
    pob.columns = ["cve_inegi", "pct_pobreza", "pct_pobreza_extrema",
                   "pct_carencia_alimentacion"]

    nna = coneval("coneval_pobreza_edad.csv")
    nna = nna[(nna.periodo == "2020-01-01") &
              (nna.grupo.str.startswith("Niñas"))][
        ["cve_inegi", "pobreza_porcentaje"]]
    nna.columns = ["cve_inegi", "pct_pobreza_nna"]

    return irs.merge(pob, on="cve_inegi", how="outer").merge(
        nna, on="cve_inegi", how="outer")


def main() -> int:
    print("Leyendo el ITER nacional (149 MB, solo las columnas necesarias)...")
    loc = localidades()
    mun = municipios()
    print(f"  localidades con ubicación : {len(loc):>8,}")
    print(f"  municipios                : {len(mun):>8,}")
    print(f"  población 15-17 imputada  : {loc.imputada.sum():>8,} localidades "
          f"({100*loc.loc[loc.imputada,'peso_15a17'].sum()/loc.peso_15a17.sum():.2f}% del peso)")

    xy = loc[["cve_inegi", "cve_loc", "lat", "lon"]]
    print("\nCalculando distancias con BallTree...")
    for etq, nivel in (("prim", "PRIMARIA"), ("sec", "SECUNDARIA"), ("ems", "EMS")):
        sedes = f911_nacional(CICLO, nivel).merge(
            xy, on=["cve_inegi", "cve_loc"], how="inner")
        loc[f"dist_{etq}"] = distancia_minima(loc, sedes)
        print(f"  {nivel:11s} sedes={len(sedes):>6,}  "
              f"mediana={loc[f'dist_{etq}'].median():>6.2f} km  "
              f"p90={loc[f'dist_{etq}'].quantile(.9):>6.2f} km")

    loc.to_csv(LIMPIO / "nacional_localidades.csv", index=False, encoding="utf-8")

    # --- Agregación a municipio, ponderada por población de 15 a 17 años ---
    print("\nAgregando a municipio...")
    g = loc.groupby("cve_inegi")
    w = lambda x, c: (np.average(x[c], weights=x.peso_15a17)
                      if x.peso_15a17.sum() > 0 else np.nan)
    agg = pd.DataFrame({
        "dist_ems": g.apply(lambda x: w(x, "dist_ems"), include_groups=False),
        "dist_sec": g.apply(lambda x: w(x, "dist_sec"), include_groups=False),
        "dist_prim": g.apply(lambda x: w(x, "dist_prim"), include_groups=False),
        "altitud_media": g.apply(lambda x: w(x, "altitud"), include_groups=False),
        "localidades": g.size(),
    })
    for u in UMBRALES_KM:
        agg[f"pct_15a17_mas_{u}km"] = g.apply(
            lambda x: 100 * x.peso_15a17[x.dist_ems > u].sum() / x.peso_15a17.sum()
            if x.peso_15a17.sum() > 0 else np.nan, include_groups=False)
    # Dispersión del poblamiento: un municipio con la gente en muchas localidades
    # pequeñas enfrenta un problema de cobertura distinto al de uno concentrado.
    agg["pct_pob_en_loc_menores"] = g.apply(
        lambda x: 100 * x.pob_total[x.pob_total < 500].sum() / max(x.pob_total.sum(), 1),
        include_groups=False)
    agg = agg.reset_index()
    agg["d_ems_sec"] = agg.dist_ems - agg.dist_sec

    base = (mun.merge(agg, on="cve_inegi", how="left")
                .merge(contexto_coneval(), on="cve_inegi", how="left"))
    base.to_csv(LIMPIO / "nacional_municipios.csv", index=False, encoding="utf-8")

    print(f"\n=== Base nacional: {len(base):,} municipios, {len(base.columns)} columnas ===")
    print(f"  inasistencia 15-17: media={base.inasistencia_15a17.mean():.2f}%  "
          f"mediana={base.inasistencia_15a17.median():.2f}%  "
          f"min={base.inasistencia_15a17.min():.1f}%  max={base.inasistencia_15a17.max():.1f}%")
    print(f"  distancia al bachillerato: mediana={base.dist_ems.median():.2f} km  "
          f"p90={base.dist_ems.quantile(.9):.2f} km")

    faltan = base[["inasistencia_15a17", "dist_ems", "indice_rezago_social",
                   "pct_pobreza_nna"]].isna().sum()
    print(f"\n  faltantes: " + ", ".join(f"{k}={v}" for k, v in faltan.items()))

    print(f"\n  Guerrero dentro de la base nacional:")
    gro = base[base.cve_ent == "12"]
    print(f"    municipios={len(gro)}  inasistencia media={gro.inasistencia_15a17.mean():.2f}%  "
          f"(nacional {base.inasistencia_15a17.mean():.2f}%)")
    print(f"    lugar de Guerrero entre las 32 entidades por inasistencia: ", end="")
    ranking = base.groupby("nom_ent").apply(
        lambda x: np.average(x.inasistencia_15a17.dropna(),
                             weights=x.pob_15a17[x.inasistencia_15a17.notna()]),
        include_groups=False).sort_values(ascending=False)
    print(f"{list(ranking.index).index('Guerrero')+1} de 32")

    print(f"\nEscritos:")
    print(f"  {(LIMPIO/'nacional_localidades.csv').relative_to(RAIZ)}  ({len(loc):,} filas)")
    print(f"  {(LIMPIO/'nacional_municipios.csv').relative_to(RAIZ)}  ({len(base):,} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
