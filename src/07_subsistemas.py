"""¿Cuánto acceso a bachillerato aporta cada subsistema? Contrafactual de cierre.

Salida: datos/limpio/aporte_subsistemas.csv

LA PREGUNTA

El coeficiente de 06_localidades.py dice cuánto cae la asistencia por cada km de
distancia al bachillerato. Eso permite voltear la pregunta hacia la política
pública: si un subsistema no existiera, ¿a qué distancia quedaría cada localidad
de su bachillerato más cercano, y cuánta asistencia se perdería?

Para cada subsistema se recalcula la distancia de las 6,769 localidades al
plantel más cercano EXCLUYENDO ese subsistema. La diferencia contra la distancia
observada es su aporte marginal a la proximidad. Convertido con β, da los puntos
de asistencia que ese subsistema sostiene.

POR QUÉ IMPORTA PARA GUERRERO

El Telebachillerato Comunitario se creó en 2014 para localidades de menos de
2,500 habitantes sin bachillerato en un radio de 5 km, y el EMSAD opera con un
criterio análogo de 30 km. Son programas cuya regla de asignación es
explícitamente la distancia. En Guerrero el TBC es 316 de 851 planteles (37%)
pero solo 8.5% de la matrícula: escuelas pequeñas cuya razón de ser es la
cercanía, no el volumen. Medirlas por matrícula las hace ver irrelevantes;
medirlas por acceso es la forma correcta de evaluarlas.

ESTO TAMBIÉN RESUELVE UNA OBJECIÓN DE ENDOGENEIDAD

La crítica natural a 06_localidades.py es que las escuelas se construyen donde
hay demanda, así que la cercanía estaría correlacionada con demanda latente y β
inflado. Pero si la regla de asignación del TBC y del EMSAD es precisamente
"donde la distancia es grande", entonces la política REDUJO la distancia
justamente en las localidades desatendidas. La variación de distancia que queda
es la que la política NO alcanzó a cerrar, y el sesgo va hacia cero: β = -1.70
pp/km es un piso.

ADVERTENCIA SOBRE EL CONTRAFACTUAL

β se estimó con la configuración actual de planteles. Extrapolarlo a distancias
mucho mayores que las observadas es fuera de muestra y supone linealidad donde
probablemente haya umbrales (a cierta distancia ya no se va nadie, y el efecto
marginal se aplana). Las cifras de abajo son órdenes de magnitud, no
predicciones puntuales; se reporta qué proporción del contrafactual cae fuera
del rango de distancias observado.

Uso:
    .venv/bin/python src/07_subsistemas.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from carga import LIMPIO, RAIZ, f911_ems
from municipios import cve_inegi

CICLO = "2023-2024"
BETA_PP_POR_KM = -1.6957  # de 06_localidades.py, carrera de caballos con log_pob
RADIO_TIERRA_KM = 6371.0

# Tipo de servicio codificado en las posiciones 3-5 de la CCT.
SUBSISTEMAS = {
    "ETK": "Telebachillerato Comunitario",
    "EMS": "Media Superior a Distancia (EMSAD)",
    "UBH": "Preparatorias UAGro",
    "ECB": "Colegio de Bachilleres",
    "DCT": "CBTIS (bach. tecnológico industrial)",
    "DTA": "CBTA (bach. tecnológico agropecuario)",
    "PBH": "Bachillerato privado",
    "DPT": "CONALEP",
}


def haversine_min(lat, lon, lat_b, lon_b) -> np.ndarray:
    la1, lo1 = np.radians(lat)[:, None], np.radians(lon)[:, None]
    la2, lo2 = np.radians(lat_b)[None, :], np.radians(lon_b)[None, :]
    a = (np.sin((la2 - la1) / 2) ** 2
         + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2)
    return (2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))).min(axis=1)


def main() -> int:
    loc = pd.read_csv(LIMPIO / "localidades_cohortes.csv", dtype={"cve_inegi": str,
                                                                  "cve_loc": str})
    loc = loc.dropna(subset=["lat", "lon", "pob_15a17"])
    loc = loc[loc.pob_15a17 > 0].reset_index(drop=True)

    e = f911_ems(CICLO)
    e = e[e.alumnos > 0].copy()
    e["cve_inegi"] = cve_inegi(e.entidad, e.cv_mun)
    e["cve_loc"] = e.cv_loc.str.zfill(4)
    e["tipo"] = e.escuela.astype(str).str[2:5]

    sedes = (e.groupby(["cve_inegi", "cve_loc", "tipo"], as_index=False)
             .agg(alumnos=("alumnos", "sum"), planteles=("escuela", "nunique")))
    xy = loc[["cve_inegi", "cve_loc", "lat", "lon"]]
    sedes = sedes.merge(xy, on=["cve_inegi", "cve_loc"], how="inner")

    w = loc.pob_15a17.values
    obs = haversine_min(loc.lat.values, loc.lon.values, sedes.lat.values, sedes.lon.values)
    d_obs_media = np.average(obs, weights=w)
    max_obs = obs.max()

    print(f"Localidades con población 15-17 : {len(loc):,}")
    print(f"Población 15-17 considerada     : {w.sum():,.0f}")
    print(f"Distancia media ponderada (obs) : {d_obs_media:.2f} km")
    print(f"Distancia máxima observada      : {max_obs:.2f} km\n")

    filas = []
    for tipo, nombre in SUBSISTEMAS.items():
        resto = sedes[sedes.tipo != tipo]
        if resto.empty:
            continue
        sin = haversine_min(loc.lat.values, loc.lon.values,
                            resto.lat.values, resto.lon.values)
        delta = sin - obs                       # km que ese subsistema ahorra
        d_media_sin = np.average(sin, weights=w)
        aporte_km = d_media_sin - d_obs_media
        pp = -BETA_PP_POR_KM * aporte_km        # puntos de asistencia sostenidos
        propio = sedes[sedes.tipo == tipo]
        # Cuánta población quedaría a una distancia nunca observada: ahí la
        # extrapolación lineal de β deja de ser creíble.
        fuera = 100 * w[sin > max_obs].sum() / w.sum()
        filas.append({
            "tipo_cct": tipo, "subsistema": nombre,
            "planteles": int(propio.planteles.sum()),
            "alumnos": int(propio.alumnos.sum()),
            "dist_media_sin_km": d_media_sin,
            "aporte_km": aporte_km,
            "pp_asistencia": pp,
            "personas_15a17": pp / 100 * w.sum(),
            "pob_afectada_pct": 100 * w[delta > 0.1].sum() / w.sum(),
            "pct_fuera_de_rango": fuera,
        })

    r = pd.DataFrame(filas).sort_values("aporte_km", ascending=False)
    r.to_csv(LIMPIO / "aporte_subsistemas.csv", index=False, encoding="utf-8")

    print("=== Aporte de cada subsistema al ACCESO (no a la matrícula) ===")
    print("aporte_km = cuánto subiría la distancia media ponderada si ese")
    print("subsistema no existiera. pp = puntos de asistencia que sostiene.\n")
    print(f"  {'subsistema':38s} {'plant.':>7s} {'alumnos':>8s} "
          f"{'aporte':>8s} {'pp':>6s} {'personas':>9s} {'%pob':>6s}")
    for _, x in r.iterrows():
        print(f"  {x.subsistema[:38]:38s} {x.planteles:>7,} {x.alumnos:>8,} "
              f"{x.aporte_km:>7.2f}km {x.pp_asistencia:>5.2f} "
              f"{x.personas_15a17:>9,.0f} {x.pob_afectada_pct:>5.1f}%")

    print("\n=== Aporte al acceso por alumno inscrito (eficiencia en acceso) ===")
    print("Un subsistema con pocos alumnos pero mucho aporte está cumpliendo una")
    print("función de cobertura territorial que la matrícula no refleja.\n")
    r["km_por_mil_alumnos"] = 1000 * r.aporte_km / r.alumnos
    for _, x in r.sort_values("km_por_mil_alumnos", ascending=False).iterrows():
        print(f"  {x.subsistema[:38]:38s} {x.km_por_mil_alumnos:>7.3f} km por mil alumnos")

    tbc = r[r.tipo_cct == "ETK"]
    if len(tbc):
        x = tbc.iloc[0]
        print("\n" + "=" * 68)
        print("EL CASO DEL TELEBACHILLERATO COMUNITARIO")
        print("=" * 68)
        print(f"  {x.planteles:,} planteles ({100*x.planteles/sedes.planteles.sum():.0f}% del total) "
              f"con {x.alumnos:,} alumnos ({100*x.alumnos/sedes.alumnos.sum():.1f}% de la matrícula)")
        print(f"  Sin TBC, la distancia media ponderada al bachillerato pasaría de")
        print(f"    {d_obs_media:.2f} km a {x.dist_media_sin_km:.2f} km  (+{x.aporte_km:.2f} km)")
        print(f"  Aplicando β = {BETA_PP_POR_KM:.3f} pp/km, sostiene ~{x.pp_asistencia:.2f} puntos")
        print(f"    de asistencia de 15-17, equivalente a ~{x.personas_15a17:,.0f} adolescentes")
        print(f"  Afecta la distancia de {x.pob_afectada_pct:.1f}% de la población de 15-17")
        if x.pct_fuera_de_rango > 1:
            print(f"  CAUTELA: {x.pct_fuera_de_rango:.1f}% de la población quedaría a una")
            print(f"    distancia mayor que cualquiera observada hoy; ahí la")
            print(f"    extrapolación lineal de β no es creíble y la cifra es un techo.")

    print(f"\nEscrito: {(LIMPIO/'aporte_subsistemas.csv').relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
