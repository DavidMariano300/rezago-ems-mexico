"""Modelo de riesgo municipal de inasistencia escolar, validado entre estados.

Salida: datos/limpio/riesgo_municipal.csv — los 2,469 municipios clasificados.

QUÉ PREGUNTA RESPONDE

El proyecto busca identificar municipios propensos al rezago en el acceso a la
educación media superior, con un método que se pueda aplicar en cualquier parte
del país. Eso exige probar algo que casi nunca se prueba: que el modelo sirva en
territorio que NO vio durante el entrenamiento.

LA VALIDACIÓN: BLOQUEO ESPACIAL POR ENTIDAD

Una validación cruzada al azar sería engañosa aquí. Los municipios vecinos se
parecen, así que repartir municipios al azar entre entrenamiento y prueba deja
al modelo memorizar regiones: el municipio de prueba tiene a sus vecinos en el
entrenamiento y el desempeño sale inflado.

Se usa en cambio bloqueo por entidad federativa: en cada pliegue se apartan
estados COMPLETOS. El modelo se entrena sin haber visto un solo municipio de
Michoacán y se le pide predecir Michoacán. Es la simulación honesta de lo que
significa "replicable en cualquier parte de México".

LAS DOS ESPECIFICACIONES

  estructural — solo condiciones del territorio: distancia, pobreza, rezago,
                dispersión del poblamiento, mercado laboral, vivienda. No usa
                ningún resultado educativo. Es la que puede aplicarse donde no
                se confíe en las cifras escolares.
  con embudo  — agrega la inasistencia de 12 a 14 años, que es el mejor predictor
                individual pero es también un resultado educativo. Sirve para
                focalizar, no para explicar.

Se excluye el grado promedio de escolaridad: se calcula sobre la población de 15
años y más, que incluye a la cohorte cuya inasistencia es la variable
dependiente. Daría un ajuste alto y vacío.

LOS DOS TIPOS DE RIESGO QUE PRODUCE

  riesgo absoluto — nivel de inasistencia. Dónde está el problema.
  brecha no explicada — cuánto peor le va al municipio de lo que predicen sus
                condiciones estructurales. Un municipio pobre y aislado con la
                inasistencia que le corresponde tiene una restricción material;
                uno que lo hace mucho peor que sus pares tiene algo más, y ahí
                la política puede actuar sin esperar a cambiar la geografía.

Uso:
    .venv/bin/python src/13_modelo_riesgo.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from carga import LIMPIO, RAIZ

OBJETIVO = "inasistencia_15a17"

# Piso de población para considerar fiable la tasa de un municipio. Con 200
# adolescentes, una persona mueve la tasa 0.5 puntos; con 14, la mueve 7. El
# umbral no descarta municipios del modelo, solo de las listas de desempeño.
MIN_POB_15A17 = 200

# Condiciones del territorio. Ningún resultado educativo entra aquí.
ESTRUCTURAL = [
    "dist_ems", "d_ems_sec", "pct_15a17_mas_5km", "pct_15a17_mas_10km",
    "altitud_media", "pct_pob_en_loc_menores", "log_pob",
    "pct_hli", "indice_rezago_social", "pct_pobreza", "pct_pobreza_extrema",
    "pct_pobreza_nna", "pct_carencia_alimentacion",
    "pct_desocupacion", "pct_pea", "pct_internet", "pct_piso_tierra",
    "pct_auto", "pct_sin_salud", "pct_jefa_mujer", "pct_discapacidad",
    "personas_por_hogar", "pct_sin_escolaridad",
]
EMBUDO = ESTRUCTURAL + ["inasistencia_12a14"]


def metricas(y, pred, peso) -> dict:
    """R², MAE y correlación de rangos, todo ponderado por población.

    Se pondera porque un municipio de 300 habitantes y uno de 800 mil no valen
    lo mismo para focalizar: el error en el grande afecta a más adolescentes.
    """
    ok = ~(np.isnan(y) | np.isnan(pred))
    y, pred, peso = y[ok], pred[ok], peso[ok]
    my = np.average(y, weights=peso)
    sse = np.sum(peso * (y - pred) ** 2)
    sst = np.sum(peso * (y - my) ** 2)
    return {
        "r2": 1 - sse / sst,
        "mae": float(np.average(np.abs(y - pred), weights=peso)),
        "rho": float(pd.Series(pred).corr(pd.Series(y), method="spearman")),
    }


def valida(d: pd.DataFrame, cols: list[str], modelo, etiqueta: str) -> pd.Series:
    """Predicción fuera de muestra con estados completos apartados."""
    X, y = d[cols].values, d[OBJETIVO].values
    peso = d["pob_15a17"].values
    pred = np.full(len(d), np.nan)

    gkf = GroupKFold(n_splits=8)  # 8 pliegues = 4 estados apartados por vuelta
    for ent, pru in gkf.split(X, y, groups=d["cve_ent"]):
        m = modelo()
        m.fit(X[ent], y[ent], **({"regressor__sample_weight": peso[ent]}
                                 if False else {}))
        pred[pru] = m.predict(X[pru])

    r = metricas(y, pred, peso)
    print(f"  {etiqueta:34s} R²={r['r2']:>6.3f}  MAE={r['mae']:>5.2f}  ρ={r['rho']:>6.3f}")
    return pd.Series(pred, index=d.index)


def main() -> int:
    d = pd.read_csv(LIMPIO / "nacional_municipios.csv", dtype={"cve_inegi": str,
                                                               "cve_ent": str})
    d["log_pob"] = np.log(d.pob_total.clip(lower=1))
    d = d.dropna(subset=[OBJETIVO, "pob_15a17"])
    d = d[d.pob_15a17 > 0].reset_index(drop=True)

    # Las medianas rellenan los pocos faltantes de CONEVAL; se reporta cuántos.
    faltaban = int(d[ESTRUCTURAL].isna().any(axis=1).sum())
    d[ESTRUCTURAL] = d[ESTRUCTURAL].fillna(d[ESTRUCTURAL].median())
    d["inasistencia_12a14"] = d.inasistencia_12a14.fillna(d.inasistencia_12a14.median())

    print(f"Base: {len(d):,} municipios en {d.cve_ent.nunique()} entidades")
    print(f"  con algún faltante imputado por mediana: {faltaban}")
    print(f"  inasistencia 15-17 (pond. por población): "
          f"{np.average(d[OBJETIVO], weights=d.pob_15a17):.2f}%\n")

    print("=== Predicción FUERA DE MUESTRA, con estados completos apartados ===")
    print("Cada municipio se predice con un modelo que nunca vio su estado.\n")

    ridge = lambda: make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20)))
    boost = lambda: HistGradientBoostingRegressor(max_depth=5, max_iter=400,
                                                  learning_rate=0.05, random_state=0)

    pred_est = valida(d, ESTRUCTURAL, ridge, "Ridge, solo estructural")
    pred_est_gb = valida(d, ESTRUCTURAL, boost, "Boosting, solo estructural")
    pred_emb = valida(d, EMBUDO, boost, "Boosting, + embudo previo")

    # Líneas base: hay que superar lo que se sabe sin modelo.
    print()
    media = np.full(len(d), np.average(d[OBJETIVO], weights=d.pob_15a17))
    r = metricas(d[OBJETIVO].values, media, d.pob_15a17.values)
    print(f"  {'LÍNEA BASE media nacional':34s} R²={r['r2']:>6.3f}  MAE={r['mae']:>5.2f}")
    # Media del propio estado, calculada SIN el municipio evaluado.
    s = d.groupby("cve_ent")[OBJETIVO].transform("sum")
    n = d.groupby("cve_ent")[OBJETIVO].transform("size")
    media_edo = (s - d[OBJETIVO]) / (n - 1)
    r = metricas(d[OBJETIVO].values, media_edo.values, d.pob_15a17.values)
    print(f"  {'LÍNEA BASE media del estado':34s} R²={r['r2']:>6.3f}  MAE={r['mae']:>5.2f}")

    # --- Utilidad para focalizar ---
    d["pred"] = pred_est_gb
    print("\n=== Utilidad para focalizar (modelo estructural) ===")
    med = np.average(d[OBJETIVO], weights=d.pob_15a17)
    for q, etq in ((0.9, "decil superior"), (0.8, "quintil superior")):
        corte = d.pred.quantile(q)
        sel = d[d.pred >= corte]
        print(f"  {etq:16s} n={len(sel):>4}  inasistencia real media="
              f"{np.average(sel[OBJETIVO], weights=sel.pob_15a17):>5.2f}%  "
              f"(nacional {med:.2f}%)")
    # ¿Cuántos adolescentes fuera de la escuela capturan los municipios señalados?
    d["fuera"] = d[OBJETIVO] / 100 * d.pob_15a17
    top = d.nlargest(int(len(d) * 0.1), "pred")
    print(f"  el decil señalado concentra "
          f"{100*top.fuera.sum()/d.fuera.sum():.1f}% de los adolescentes fuera de la escuela")
    print(f"  (si la selección fuera al azar capturaría ~"
          f"{100*top.pob_15a17.sum()/d.pob_15a17.sum():.1f}%, su parte de la población)")

    # --- Focalizar por número de adolescentes, no solo por tasa ---
    print("\n=== Dónde están, en número, los adolescentes fuera de la escuela ===")
    print("La tasa señala municipios rurales pequeños; el conteo señala ciudades.")
    print("Son dos preguntas distintas y ambas importan.\n")
    porv = d.nlargest(8, "fuera")[["nom_mun", "nom_ent", OBJETIVO, "pob_15a17", "fuera"]]
    print(porv.to_string(index=False, float_format=lambda x: f"{x:>9.1f}"))
    k = int(len(d) * 0.1)
    print(f"\n  los {k} municipios con más adolescentes fuera concentran "
          f"{100*d.nlargest(k,'fuera').fuera.sum()/d.fuera.sum():.1f}% del total nacional")

    # --- Brecha no explicada ---
    d["brecha"] = d[OBJETIVO] - d.pred
    d["riesgo_absoluto"] = pd.qcut(d[OBJETIVO], 5,
                                   labels=["muy bajo", "bajo", "medio", "alto", "muy alto"])
    d["brecha_cat"] = pd.cut(
        d.brecha, [-np.inf, -5, 5, np.inf],
        labels=["mejor de lo esperado", "en lo esperado", "peor de lo esperado"])

    # Un municipio con 14 adolescentes tiene una tasa que se mueve 7 puntos si una
    # sola persona cambia de condición. Sin un piso de población, la lista de
    # "peores" es un ranking de varianza muestral, no de desempeño.
    chicos = int((d.pob_15a17 < MIN_POB_15A17).sum())
    d["fiable"] = d.pob_15a17 >= MIN_POB_15A17
    print(f"\n=== Precisión de la tasa según tamaño ===")
    print(f"  municipios con menos de {MIN_POB_15A17} adolescentes de 15-17: "
          f"{chicos:,} de {len(d):,} ({100*chicos/len(d):.1f}%)")
    print(f"  concentran {100*d.loc[~d.fiable,'pob_15a17'].sum()/d.pob_15a17.sum():.1f}% "
          f"de la población de esa edad")
    print(f"  desviación de la brecha: {d.loc[~d.fiable,'brecha'].std():.1f} pp en los "
          f"pequeños contra {d.loc[d.fiable,'brecha'].std():.1f} pp en el resto")
    print("  Por eso las listas de abajo se restringen a los municipios fiables.")

    fi = d[d.fiable]
    print(f"\n=== Peor de lo que predicen sus condiciones (población suficiente) ===")
    print("Ahí la restricción no es la geografía ni la pobreza; hay margen de política.\n")
    peor = fi.nlargest(12, "brecha")[
        ["nom_mun", "nom_ent", OBJETIVO, "pred", "brecha", "pob_15a17"]]
    print(peor.to_string(index=False, float_format=lambda x: f"{x:>8.1f}"))

    print("\n=== Y los que lo hacen mucho mejor de lo esperado ===")
    print("Vale la pena mirarlos: son los casos de los que se puede aprender.\n")
    mejor = fi.nsmallest(8, "brecha")[
        ["nom_mun", "nom_ent", OBJETIVO, "pred", "brecha", "pob_15a17"]]
    print(mejor.to_string(index=False, float_format=lambda x: f"{x:>8.1f}"))

    print("\n=== Importancia: qué pesa en el modelo estructural (Ridge) ===")
    m = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20)))
    m.fit(d[ESTRUCTURAL], d[OBJETIVO])
    coef = pd.Series(m[-1].coef_, index=ESTRUCTURAL).sort_values(key=abs, ascending=False)
    for k, v in coef.head(10).items():
        print(f"  {k:28s} {v:>+7.3f}")
    print("  (coeficientes estandarizados: puntos de inasistencia por desviación")
    print("   estándar de cada variable)")

    salida = d[["cve_inegi", "cve_ent", "nom_ent", "nom_mun", "pob_total", "pob_15a17",
                OBJETIVO, "inasistencia_12a14", "pred", "brecha", "riesgo_absoluto",
                "brecha_cat", "dist_ems", "pct_15a17_mas_10km", "indice_rezago_social",
                "pct_pobreza_nna", "pct_hli", "fuera"]]
    salida.to_csv(LIMPIO / "riesgo_municipal.csv", index=False, encoding="utf-8")
    print(f"\nEscrito: {(LIMPIO/'riesgo_municipal.csv').relative_to(RAIZ)}  "
          f"({len(salida):,} municipios)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
