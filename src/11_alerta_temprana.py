"""¿Es construible el sistema de alerta temprana que planteaba el briefing?

Salida: datos/limpio/panel_planteles.csv

EL OBJETIVO ORIGINAL DEL PROYECTO

El briefing pedía identificar dónde es más probable que se concentre el abandono,
con vistas a un sistema de alerta temprana sobre datos abiertos. El análisis
municipal ya demostró que por esa vía no se puede: la tasa de deserción municipal
del Formato 911 tiene R² ajustado de 0.002 y R² within de 0.017.

Queda una vía sin explorar, y es donde la literatura de alerta temprana opera de
verdad: el PLANTEL. Guerrero tiene ~850 planteles de media superior con seis
ciclos observados, diez veces más unidades que municipios, y las escuelas son
además el destinatario natural de una alerta: se puede intervenir en una escuela,
no en un municipio.

CÓMO SE EVALÚA, Y POR QUÉ ASÍ

Un sistema de alerta temprana no se juzga por su ajuste dentro de muestra. Se
juzga por tres cosas, en este orden:

1. **Predicción fuera de muestra.** Se entrena con las transiciones tempranas y
   se evalúa en las tardías, que es la situación real: predecir un ciclo que
   todavía no ocurrió.

2. **Superar la línea base ingenua.** La comparación decisiva no es contra cero
   sino contra "usar el abandono que ese mismo plantel tuvo el ciclo pasado".
   Si el modelo no le gana a eso, no aporta nada: la escuela ya conoce su propio
   historial y no necesita un modelo para consultarlo. Este es el criterio que
   hace honesta la evaluación, y el que suele omitirse.

3. **Concentración del riesgo.** Para operar, lo que importa no es el R² sino si
   el decil señalado como de mayor riesgo concentra abandono real. Una alerta
   sirve si permite priorizar visitas, no si acierta el decimal.

Uso:
    .venv/bin/python src/11_alerta_temprana.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from carga import CICLOS_EMS, LIMPIO, RAIZ, f911_ems
from municipios import a_panel

GRADOS = ["01", "2", "3"]
MATRICULA_MINIMA = 40  # bajo este umbral la tasa de un plantel es casi solo ruido


def razon(num, den):
    num, den = pd.Series(num).astype(float), pd.Series(den).astype(float)
    return num / den.where(den > 0)


def construye_panel() -> pd.DataFrame:
    """Panel plantel × transición con abandono y características del ciclo inicial."""
    ciclos = {}
    for c in CICLOS_EMS:
        d = f911_ems(c)
        d["cve_panel"] = a_panel(d["cve_inegi"])
        # Un CCT puede aparecer en varias filas (subnivel); se agrega a plantel.
        g = d.groupby("escuela", as_index=False).agg(
            cve_inegi=("cve_panel", "first"),
            nom_mun=("c_nom_mun", "first"),
            control=("control", "first"),
            subnivel=("subnivel", "first"),
            alumnos=("alumnos", "sum"), mujeres=("mujeres", "sum"),
            docentes=("docentes", "sum"), grupos=("grupos", "sum"),
            egresados=("egresados", "sum"),
            **{f"{b}_{gr}": (f"{b}_{gr}", "sum")
               for b in ("alumnos", "nvo_ing", "repetidores") for gr in GRADOS},
        )
        g["tipo"] = g.escuela.astype(str).str[2:5]
        ciclos[c] = g

    filas = []
    for ini, fin in zip(CICLOS_EMS, CICLOS_EMS[1:]):
        a = ciclos[ini].drop(columns=["egresados"])
        b = ciclos[fin][["escuela", "alumnos", "nvo_ing_01", "egresados"]].rename(
            columns={"alumnos": "alumnos_fin", "nvo_ing_01": "nvo_ing_01_fin",
                     "egresados": "egresados_del_ciclo_ini"})
        t = a.merge(b, on="escuela", how="inner")  # solo planteles en ambos ciclos
        t["transicion"] = f"{ini}→{fin}"
        t["orden"] = CICLOS_EMS.index(ini)
        filas.append(t)

    p = pd.concat(filas, ignore_index=True)
    sobrevive = p.alumnos_fin - p.nvo_ing_01_fin + p.egresados_del_ciclo_ini
    p["abandono"] = 100 * (1 - razon(sobrevive, p.alumnos))

    p["alumnos_por_docente"] = razon(p.alumnos, p.docentes)
    p["alumnos_por_grupo"] = razon(p.alumnos, p.grupos)
    p["pct_mujeres"] = 100 * razon(p.mujeres, p.alumnos)
    p["pct_repetidores"] = 100 * razon(
        p[[f"repetidores_{g}" for g in GRADOS]].sum(axis=1), p.alumnos)
    p["pct_primer_grado"] = 100 * razon(p.alumnos_01, p.alumnos)
    p["log_alumnos"] = np.log(p.alumnos.clip(lower=1))
    p["es_privado"] = (p.control.str.strip().str.upper() == "PRIVADO").astype(int)
    return p


def evalua(nombre, y_real, y_pred, base) -> dict:
    """Compara el modelo contra la línea base en las tres dimensiones que importan."""
    ok = ~(np.isnan(y_real) | np.isnan(y_pred) | np.isnan(base))
    y, yp, yb = y_real[ok], y_pred[ok], base[ok]
    sse = lambda a: float(np.sum((y - a) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    r2_mod, r2_base = 1 - sse(yp) / sst, 1 - sse(yb) / sst
    rho = pd.Series(yp).corr(pd.Series(y), method="spearman")
    rho_base = pd.Series(yb).corr(pd.Series(y), method="spearman")

    # Concentración: abandono real medio en el decil de mayor riesgo predicho.
    k = max(1, len(y) // 10)
    top_mod = y[np.argsort(-yp)[:k]].mean()
    top_base = y[np.argsort(-yb)[:k]].mean()
    return {"nombre": nombre, "n": int(ok.sum()), "r2": r2_mod, "r2_base": r2_base,
            "rho": rho, "rho_base": rho_base, "top": top_mod, "top_base": top_base,
            "media": float(y.mean()), "mae": float(np.mean(np.abs(y - yp))),
            "mae_base": float(np.mean(np.abs(y - yb)))}


def main() -> int:
    p = construye_panel()
    print(f"Panel de planteles: {len(p):,} observaciones, "
          f"{p.escuela.nunique():,} planteles, {p.transicion.nunique()} transiciones")

    grande = p[p.alumnos >= MATRICULA_MINIMA].copy()
    print(f"Con matrícula >= {MATRICULA_MINIMA}: {len(grande):,} observaciones\n")

    print("=== Volatilidad del abandono por plantel (¿hay señal que predecir?) ===")
    est = grande.groupby("escuela").abandono.agg(["std", "mean", "size"])
    est = est[est["size"] >= 3]
    print(f"  planteles con >=3 transiciones : {len(est):,}")
    print(f"  desviación estándar mediana    : {est['std'].median():.2f} pp")
    print(f"  desviación entre planteles      : {est['mean'].std():.2f} pp")
    # Si la variación dentro del plantel supera a la que hay entre planteles, el
    # historial propio sirve de poco y cualquier alerta hereda ese ruido.
    icc = est["mean"].var() / (est["mean"].var() + (est["std"] ** 2).mean())
    print(f"  proporción de varianza estable  : {icc:.3f}")
    print("  (fracción de la varianza total atribuible a diferencias persistentes")
    print("   entre planteles; el resto es fluctuación año con año)")

    # --- Diseño de validación temporal ---
    grande["abandono_previo"] = grande.sort_values("orden").groupby("escuela")\
        .abandono.shift(1)
    entrena = grande[grande.orden <= 2]
    prueba = grande[grande.orden >= 3].dropna(subset=["abandono_previo"])

    X = ["alumnos_por_docente", "alumnos_por_grupo", "pct_mujeres", "pct_repetidores",
         "pct_primer_grado", "log_alumnos", "es_privado", "abandono_previo"]
    Xsin = [c for c in X if c != "abandono_previo"]

    print(f"\n=== Validación temporal ===")
    print(f"  entrenamiento: transiciones 1-3  (n={len(entrena):,})")
    print(f"  prueba       : transiciones 4-5  (n={len(prueba):,})")

    ent = entrena.dropna(subset=X + ["abandono"])
    y_ent, y_pru = ent.abandono.values, prueba.abandono.values
    base = prueba.abandono_previo.values          # línea base ingenua
    media_ent = float(ent.abandono.mean())

    resultados = []
    # Modelo 1: solo características del plantel, sin historial.
    r = Ridge(alpha=1.0).fit(ent[Xsin], y_ent)
    resultados.append(evalua("Ridge, solo características", y_pru,
                             r.predict(prueba[Xsin]), base))
    # Modelo 2: características + historial propio.
    r2 = Ridge(alpha=1.0).fit(ent[X], y_ent)
    resultados.append(evalua("Ridge, + historial del plantel", y_pru,
                             r2.predict(prueba[X]), base))
    # Modelo 3: boosting con todo.
    gb = HistGradientBoostingRegressor(max_depth=4, max_iter=300,
                                       learning_rate=0.05, random_state=0)
    gb.fit(ent[X], y_ent)
    resultados.append(evalua("Boosting, + historial", y_pru,
                             gb.predict(prueba[X]), base))
    # Modelo 4: predecir siempre la media estatal, para tener el piso absoluto.
    resultados.append(evalua("Media del estado (piso)", y_pru,
                             np.full(len(y_pru), media_ent), base))

    print(f"\n=== Desempeño FUERA DE MUESTRA ===")
    print("La columna que decide es Δ vs base: si no es positiva, el modelo no")
    print("aporta sobre consultar el abandono del ciclo anterior del propio plantel.\n")
    print(f"  {'modelo':32s} {'R²':>7s} {'ρ Spearman':>11s} {'MAE':>7s} {'Δ R² vs base':>13s}")
    for x in resultados:
        print(f"  {x['nombre']:32s} {x['r2']:>7.3f} {x['rho']:>11.3f} "
              f"{x['mae']:>7.2f} {x['r2']-x['r2_base']:>+13.3f}")
    b = resultados[0]
    print(f"\n  {'LÍNEA BASE (abandono previo)':32s} {b['r2_base']:>7.3f} "
          f"{b['rho_base']:>11.3f} {b['mae_base']:>7.2f}")

    print(f"\n=== Concentración del riesgo (lo que importa para operar) ===")
    print(f"  abandono medio en el conjunto de prueba : {b['media']:.2f}%")
    print(f"  {'modelo':32s} {'decil de mayor riesgo':>22s}")
    for x in resultados[:3]:
        print(f"  {x['nombre']:32s} {x['top']:>21.2f}%")
    print(f"  {'línea base (abandono previo)':32s} {b['top_base']:>21.2f}%")

    p.to_csv(LIMPIO / "panel_planteles.csv", index=False, encoding="utf-8")

    print(f"\n=== Veredicto ===")
    mejor = max(resultados[:3], key=lambda x: x["r2"])
    gana = mejor["r2"] > mejor["r2_base"]
    util = mejor["top"] > b["media"] * 1.5
    if gana and util:
        print("  El modelo supera a la línea base y concentra riesgo. La alerta")
        print("  temprana por plantel ES viable y vale la pena desarrollarla.")
    elif util and not gana:
        print("  El modelo NO supera a la línea base en precisión, pero el decil")
        print("  señalado sí concentra abandono muy por encima de la media. Sirve")
        print("  para priorizar, no para estimar magnitudes.")
    else:
        print("  El modelo no supera a la línea base ni concentra riesgo de forma")
        print("  útil. Con datos abiertos agregados a nivel plantel, el sistema de")
        print("  alerta temprana del briefing NO es construible.")
    print(f"\nEscrito: {(LIMPIO/'panel_planteles.csv').relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
