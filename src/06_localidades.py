"""Diseño a nivel localidad: ¿la distancia a la escuela reduce la asistencia?

Salida: datos/limpio/localidades_cohortes.csv

EL PROBLEMA QUE ESTE DISEÑO RESUELVE

A nivel municipal (81 unidades) la distancia y la pobreza son casi
indistinguibles: los bachilleratos están donde hay gente, así que "lejos" y
"despoblado y pobre" describen a los mismos municipios. Cualquier coeficiente de
distancia carga con todo eso.

LA ESTRATEGIA: CONTRASTE ENTRE COHORTES DENTRO DE LA MISMA LOCALIDAD

En Guerrero hay 1,721 localidades con secundaria y solo 589 con bachillerato. Es
decir que la MISMA localidad puede tener la secundaria a la vuelta y el
bachillerato a 15 km. Eso permite estimar

    (asist_15a17 - asist_12a14)_loc = β·(dist_bach - dist_sec)_loc
                                      + EF_municipio + controles + ε

Al diferenciar entre cohortes de la misma localidad se cancela TODO lo que
afecta igual a las dos edades: pobreza del hogar, lengua materna, aislamiento
per se, valor que la comunidad da a la escuela, calidad del camino. Lo que queda
identificando β es que a un adolescente de 15 le queda más lejos su escuela que
a su hermano de 13, y que ese diferencial varía entre localidades.

Es equivalente a apilar las dos cohortes y poner efectos fijos de LOCALIDAD: con
exactamente dos cohortes, el estimador diferenciado y el de efectos fijos dan el
mismo β. Se reporta la versión diferenciada por ser más transparente.

LA PRUEBA DE FALSACIÓN

Si β capturara "las localidades remotas son distintas" en vez del efecto de la
distancia, el mismo ejercicio sobre un margen donde la distancia NO varía
debería dar el mismo resultado. Las primarias están en casi todas las
localidades, así que la brecha 12-14 vs 6-11 tiene muy poca variación de
distancia que explotar:

    (asist_12a14 - asist_6a11)_loc = β_placebo·(dist_sec - dist_prim)_loc + ...

Si β es grande y β_placebo es cercano a cero, el efecto es de la distancia al
bachillerato y no de un rasgo general de las localidades aisladas. Si los dos
salen grandes, la interpretación causal se cae y hay que decirlo.

CONVENCIÓN DEL CENSO: para las edades de educación obligatoria el INEGI reporta
quién NO asiste (P6A11_NOA, P12A14NOA) y para las posobligatorias quién SÍ
asiste (P15A17A). Se homologa todo a tasa de asistencia.

LIMITACIONES QUE NO SE PUEDEN ARREGLAR CON ESTOS DATOS
- Censo 2020: un solo corte. No hay panel de localidades.
- La distancia es en línea recta y las escuelas se ubican en el centroide de su
  localidad. En la sierra eso subestima el traslado real, así que β subestima.
- El INEGI suprime datos de localidades muy pequeñas por confidencialidad. Se
  reporta cuántas y qué proporción de población se pierde.
- La asistencia de 15-17 mezcla bachillerato con quienes siguen en secundaria
  por rezago. No se puede separar con datos censales.

Uso:
    .venv/bin/python src/06_localidades.py
"""

from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm

from carga import CRUDO, LIMPIO, RAIZ, f911_ems
from municipios import CVE_GUERRERO, cve_inegi

CICLO = "2023-2024"
RADIO_TIERRA_KM = 6371.0

_DMS = r"(\d+)°(\d+)'([\d.]+)\"\s*([NSEWO])"


def dms_a_decimal(s: pd.Series) -> pd.Series:
    ext = s.astype(str).str.strip().str.extract(_DMS)
    dec = (pd.to_numeric(ext[0], errors="coerce")
           + pd.to_numeric(ext[1], errors="coerce") / 60
           + pd.to_numeric(ext[2], errors="coerce") / 3600)
    return dec.where(~ext[3].isin(["S", "W", "O"]), -dec)


def haversine_min(lat, lon, lat_b, lon_b) -> np.ndarray:
    """Distancia al punto más cercano del conjunto b, en km."""
    la1, lo1 = np.radians(lat)[:, None], np.radians(lon)[:, None]
    la2, lo2 = np.radians(lat_b)[None, :], np.radians(lon_b)[None, :]
    a = (np.sin((la2 - la1) / 2) ** 2
         + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2)
    return (2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).min(axis=1)


def num(s):
    return pd.to_numeric(pd.Series(s).replace({"*": None, "N/D": None}), errors="coerce")


def localidades() -> pd.DataFrame:
    with zipfile.ZipFile(CRUDO / "inegi_iter_guerrero_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig", low_memory=False)
    d = d[(d.MUN != "000") & (d.LOC != "0000") & (~d.LOC.isin(["9998", "9999"]))].copy()

    o = pd.DataFrame({
        "cve_inegi": cve_inegi(d.ENTIDAD, d.MUN).values,
        "cve_loc": d.LOC.str.zfill(4).values,
        "nom_loc": d.NOM_LOC.values,
        "lat": dms_a_decimal(d.LATITUD).values,
        "lon": dms_a_decimal(d.LONGITUD).values,
        "altitud": num(d.ALTITUD).values,
        "pob_total": num(d.POBTOT).values,
    })
    for pob, col, tipo in (("6a11", "P6A11_NOA", "no_asiste"),
                           ("12a14", "P12A14NOA", "no_asiste"),
                           ("15a17", "P15A17A", "asiste")):
        den = num(d[f"P_{pob.upper()}"]).values
        val = num(d[col]).values
        o[f"pob_{pob}"] = den
        with np.errstate(invalid="ignore", divide="ignore"):
            tasa = 100 * val / np.where(den > 0, den, np.nan)
        # Homologar a tasa de ASISTENCIA en las tres cohortes.
        o[f"asist_{pob}"] = 100 - tasa if tipo == "no_asiste" else tasa
    o["pct_hli"] = 100 * num(d.P3YM_HLI).values / np.where(
        num(d.P_3YMAS).values > 0, num(d.P_3YMAS).values, np.nan)
    return o


def sedes_basica(nivel: str) -> pd.DataFrame:
    """Localidades de Guerrero con al menos un plantel del nivel dado."""
    d = pd.read_csv(CRUDO / f"f911_basica_{CICLO}.csv", dtype=str, low_memory=False,
                    usecols=["entidad", "municipio", "localidad", "nivel", "insc_t"])
    d = d[d.entidad.astype(str).str.strip().str.lstrip("0") == CVE_GUERRERO]
    d = d[d.nivel.str.strip().str.upper() == nivel]
    d = d[pd.to_numeric(d.insc_t, errors="coerce").fillna(0) > 0]
    return pd.DataFrame({
        "cve_inegi": (CVE_GUERRERO + d.municipio.str.zfill(3)).values,
        "cve_loc": d.localidad.str.zfill(4).values,
    }).drop_duplicates()


def sedes_ems() -> pd.DataFrame:
    e = f911_ems(CICLO)
    e = e[e.alumnos > 0]
    return pd.DataFrame({
        "cve_inegi": cve_inegi(e.entidad, e.cv_mun).values,
        "cve_loc": e.cv_loc.str.zfill(4).values,
    }).drop_duplicates()


def ajusta(y, X, grupos, pesos, etiqueta: str, clave, extra=None) -> dict:
    """WLS con efectos fijos de municipio y errores agrupados por municipio.

    `clave` puede ser una columna o una lista, para correr las dos distancias en
    la misma ecuación y ver cuál sobrevive.
    """
    claves = [clave] if isinstance(clave, str) else list(clave)
    m = sm.WLS(y, X, weights=pesos).fit(cov_type="cluster",
                                        cov_kwds={"groups": grupos})
    print(f"\n  {etiqueta}")
    print(f"    n={int(m.nobs):,}  R2={m.rsquared:.3f}  "
          f"municipios(clusters)={grupos.nunique()}")
    for k in claves + list(extra or []):
        ic = m.conf_int().loc[k]
        print(f"    {k:26s} β={m.params[k]:>+8.4f}  EE={m.bse[k]:.4f}  "
              f"t={m.tvalues[k]:>+6.2f}  p={m.pvalues[k]:.4f}  "
              f"IC[{ic[0]:+.3f},{ic[1]:+.3f}]")
    return {"beta": m.params[claves[0]], "p": m.pvalues[claves[0]],
            "n": int(m.nobs),
            "todos": {k: (m.params[k], m.pvalues[k]) for k in claves}}


def carrera(loc: pd.DataFrame) -> None:
    """Pone las dos distancias diferenciales a competir en la misma ecuación.

    Es la prueba que separa las dos explicaciones rivales:

      MECANISMO  — lo que importa es la distancia a la escuela QUE TOCA a esa
                   edad. Entonces en la brecha 15-17 vs 12-14 debe pesar
                   `d_ems_sec` y NO `d_sec_prim`, y al revés en la otra brecha.
      CONFUSIÓN  — el aislamiento en general deprime la asistencia de los más
                   grandes (trabajo agrícola, migración, costo de oportunidad),
                   sin que la distancia a la escuela sea la vía. Entonces
                   CUALQUIER medida de aislamiento predice CUALQUIER brecha, y
                   los dos coeficientes salen parecidos en las dos ecuaciones.
    """
    print("\n" + "=" * 68)
    print("CARRERA DE CABALLOS: ¿importa la distancia del nivel que toca,")
    print("o solo el aislamiento en general?")
    print("=" * 68)

    for etq, brecha, pobs, orden in (
        ("Brecha 15-17 vs 12-14 (margen bachillerato)",
         "brecha_15_12", ("pob_15a17", "pob_12a14"), ["d_ems_sec", "d_sec_prim"]),
        ("Brecha 12-14 vs 6-11 (margen secundaria)",
         "brecha_12_6", ("pob_12a14", "pob_6a11"), ["d_sec_prim", "d_ems_sec"]),
    ):
        d = loc.dropna(subset=[brecha, "d_ems_sec", "d_sec_prim", *pobs])
        d = d[(d[pobs[0]] > 0) & (d[pobs[1]] > 0)].reset_index(drop=True)
        fe = pd.get_dummies(d.cve_inegi, prefix="mun", drop_first=True, dtype=float)
        X = sm.add_constant(pd.concat(
            [d[["d_ems_sec", "d_sec_prim", "log_pob"]], fe], axis=1).fillna(0))
        r = ajusta(d[brecha], X, d.cve_inegi, d[pobs[0]] + d[pobs[1]], etq, orden)
        propio, ajeno = r["todos"][orden[0]], r["todos"][orden[1]]
        print(f"    -> distancia del nivel propio : β={propio[0]:+.3f} (p={propio[1]:.4f})")
        print(f"    -> distancia del otro nivel   : β={ajeno[0]:+.3f} (p={ajeno[1]:.4f})")
        if propio[1] < 0.05 and (abs(ajeno[0]) < abs(propio[0]) / 2 or ajeno[1] > 0.05):
            print("       La distancia que manda es la del nivel que le toca a la edad:")
            print("       consistente con MECANISMO, no con aislamiento general.")
        else:
            print("       Las dos distancias pesan parecido: consistente con CONFUSIÓN")
            print("       por aislamiento general.")


def main() -> int:
    loc = localidades().dropna(subset=["lat", "lon"])
    prim, sec, ems = sedes_basica("PRIMARIA"), sedes_basica("SECUNDARIA"), sedes_ems()

    print("=== Oferta escolar por localidad en Guerrero ===")
    print(f"  localidades con ubicación   : {len(loc):,}")
    for etq, s in (("primaria", prim), ("secundaria", sec), ("bachillerato", ems)):
        print(f"  localidades con {etq:13s}: {len(s):>5,}")

    # Coordenadas de las sedes, tomadas de la localidad donde están.
    xy = loc[["cve_inegi", "cve_loc", "lat", "lon"]]
    for etq, s in (("prim", prim), ("sec", sec), ("ems", ems)):
        p = s.merge(xy, on=["cve_inegi", "cve_loc"], how="inner")
        loc[f"dist_{etq}"] = haversine_min(loc.lat.values, loc.lon.values,
                                          p.lat.values, p.lon.values)

    loc["d_ems_sec"] = loc.dist_ems - loc.dist_sec     # tratamiento principal
    loc["d_sec_prim"] = loc.dist_sec - loc.dist_prim   # tratamiento del placebo
    loc["brecha_15_12"] = loc.asist_15a17 - loc.asist_12a14
    loc["brecha_12_6"] = loc.asist_12a14 - loc.asist_6a11
    loc["log_pob"] = np.log(loc.pob_total.clip(lower=1))

    print("\n=== Distancias por localidad (km) ===")
    print(f"  {'nivel':14s} {'mediana':>9s} {'media':>8s} {'p90':>8s} {'max':>8s}")
    for etq, c in (("primaria", "dist_prim"), ("secundaria", "dist_sec"),
                   ("bachillerato", "dist_ems")):
        s = loc[c]
        print(f"  {etq:14s} {s.median():>9.2f} {s.mean():>8.2f} "
              f"{s.quantile(.9):>8.2f} {s.max():>8.2f}")
    print(f"\n  Diferencial bachillerato - secundaria: "
          f"mediana={loc.d_ems_sec.median():.2f} km  "
          f"media={loc.d_ems_sec.mean():.2f} km  p90={loc.d_ems_sec.quantile(.9):.2f} km")
    print(f"  Diferencial secundaria - primaria    : "
          f"mediana={loc.d_sec_prim.median():.2f} km  "
          f"media={loc.d_sec_prim.mean():.2f} km  p90={loc.d_sec_prim.quantile(.9):.2f} km")
    print("  (el segundo es mucho menor: por eso sirve de placebo, casi no hay")
    print("   variación de distancia que explotar en ese margen)")

    print("\n=== Supresión de datos por confidencialidad ===")
    tot_pob = loc.pob_total.sum()
    for etq, cols in (("brecha 15-17 vs 12-14", ["asist_15a17", "asist_12a14"]),
                      ("brecha 12-14 vs 6-11", ["asist_12a14", "asist_6a11"])):
        ok = loc[cols].notna().all(axis=1) & (loc[cols[0]].notna())
        usable = loc[ok]
        print(f"  {etq:24s} localidades usables={len(usable):>5,} de {len(loc):,}"
              f"  ({100*usable.pob_total.sum()/tot_pob:>5.1f}% de la población)")

    loc.to_csv(LIMPIO / "localidades_cohortes.csv", index=False, encoding="utf-8")

    # ---------------- Estimación ----------------
    print("\n" + "=" * 68)
    print("RESULTADO PRINCIPAL: brecha 15-17 vs 12-14 sobre distancia diferencial")
    print("=" * 68)

    d = loc.dropna(subset=["brecha_15_12", "d_ems_sec", "pob_15a17", "pob_12a14"])
    d = d[(d.pob_15a17 > 0) & (d.pob_12a14 > 0)]
    peso = d.pob_15a17 + d.pob_12a14
    fe = pd.get_dummies(d.cve_inegi, prefix="mun", drop_first=True, dtype=float)

    X1 = sm.add_constant(pd.concat([d[["d_ems_sec"]].reset_index(drop=True),
                                    fe.reset_index(drop=True)], axis=1))
    r1 = ajusta(d.brecha_15_12.reset_index(drop=True), X1, d.cve_inegi.reset_index(drop=True),
                peso.reset_index(drop=True),
                "Con efectos fijos de municipio", "d_ems_sec")

    X2 = sm.add_constant(pd.concat(
        [d[["d_ems_sec", "log_pob", "pct_hli"]].reset_index(drop=True),
         fe.reset_index(drop=True)], axis=1).fillna(0))
    r2 = ajusta(d.brecha_15_12.reset_index(drop=True), X2, d.cve_inegi.reset_index(drop=True),
                peso.reset_index(drop=True),
                "+ tamaño de localidad y % lengua indígena", "d_ems_sec")

    cerca = d[d.dist_sec <= 2]
    if len(cerca) > 50:
        fec = pd.get_dummies(cerca.cve_inegi, prefix="mun", drop_first=True, dtype=float)
        Xc = sm.add_constant(pd.concat([cerca[["d_ems_sec"]].reset_index(drop=True),
                                        fec.reset_index(drop=True)], axis=1))
        ajusta(cerca.brecha_15_12.reset_index(drop=True), Xc,
               cerca.cve_inegi.reset_index(drop=True),
               (cerca.pob_15a17 + cerca.pob_12a14).reset_index(drop=True),
               "Solo localidades con secundaria a ≤2 km (el tratamiento es puro)",
               "d_ems_sec")

    print("\n" + "=" * 68)
    print("PRUEBA DE FALSACIÓN: brecha 12-14 vs 6-11 sobre distancia diferencial")
    print("=" * 68)
    p = loc.dropna(subset=["brecha_12_6", "d_sec_prim", "pob_12a14", "pob_6a11"])
    p = p[(p.pob_12a14 > 0) & (p.pob_6a11 > 0)]
    fep = pd.get_dummies(p.cve_inegi, prefix="mun", drop_first=True, dtype=float)
    Xp = sm.add_constant(pd.concat([p[["d_sec_prim"]].reset_index(drop=True),
                                    fep.reset_index(drop=True)], axis=1))
    rp = ajusta(p.brecha_12_6.reset_index(drop=True), Xp, p.cve_inegi.reset_index(drop=True),
                (p.pob_12a14 + p.pob_6a11).reset_index(drop=True),
                "Con efectos fijos de municipio", "d_sec_prim")

    carrera(loc)

    print("\n" + "=" * 68)
    print("LECTURA")
    print("=" * 68)
    print(f"  Margen bachillerato (15-17 vs 12-14) : β={r2['beta']:+.3f} pp/km "
          f"(p={r2['p']:.4f})")
    print(f"  Margen secundaria   (12-14 vs 6-11)  : β={rp['beta']:+.3f} pp/km "
          f"(p={rp['p']:.4f})")
    print("\n  Los dos márgenes muestran efecto, así que el ejercicio de la sección")
    print("  anterior NO funcionó como placebo: hay variación real de distancia en")
    print("  el margen de la secundaria. La carrera de caballos de arriba es la que")
    print("  decide si es mecanismo o aislamiento general; ver su veredicto.")

    print(f"\nEscrito: {(LIMPIO/'localidades_cohortes.csv').relative_to(RAIZ)}  "
          f"({len(loc):,} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
