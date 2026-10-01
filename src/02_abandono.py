"""Calcula la tasa de abandono escolar municipal en media superior.

Salida: datos/limpio/panel_abandono_ems.csv — panel de 81 municipios × 5
transiciones de ciclo (2019-2020 → 2024-2025), con la tasa de abandono, su
descomposición por grado y las covariables de infraestructura escolar.

LA FÓRMULA

    abandono_t = [1 - (M_{t+1} - NI_{t+1} + EG_t) / M_t] * 100

    M  = matrícula total al inicio del ciclo
    NI = nuevo ingreso a primer grado
    EG = egresados al cierre del ciclo t

Es la definición de la SEP y la ex-INEE, así que las cifras son comparables con
la estadística nacional publicada. Resta a los egresados, que salieron por haber
terminado y no por abandono, y al nuevo ingreso, que no estaba en la cohorte.

DOS TRAMPAS DEL FORMATO 911 QUE ESTA IMPLEMENTACIÓN EVITA

1. NI no es la columna `nvo_ing`. Se verificó que
   `nvo_ing_g + repetidores_g == alumnos_g` exactamente en los seis ciclos, o
   sea que `nvo_ing_g` son los alumnos del grado g que no repiten, no los que
   entran al nivel. El nuevo ingreso al bachillerato es `nvo_ing_01`. Usar el
   `nvo_ing` total (132 mil en vez de 52 mil en 2023-2024) produce cifras sin
   sentido.

2. EG_t no es el `egresados` del archivo del ciclo t, sino el del ciclo t+1. El
   911 se levanta al inicio de cursos y pregunta por el egreso del ciclo previo
   (ver la comprobación en carga.py y --verificar-egresados). Leerlo mal corre
   la variable dependiente un ciclo entero.

SOBRE LA DESCOMPOSICIÓN POR GRADO

El briefing planteaba el seguimiento de cohorte como alternativa a la fórmula
oficial. Calculadas ambas, resultan ser la MISMA cantidad, no dos estimaciones
que se puedan contrastar: como alumnos_g == nvo_ing_g + repetidores_g es una
identidad contable del formato, se sigue que

    M_{t+1} - NI_{t+1} = rep_01 + nvo_2 + rep_2 + nvo_3 + rep_3   (en t+1)

que es exactamente el conjunto de sobrevivientes que suma el seguimiento por
grado. La correlación entre las dos series es 1.0000, no 0.99: son la misma
fórmula reordenada.

Así que el seguimiento por grado no aporta una segunda medida del mismo número,
sino algo distinto y más útil: DÓNDE se va la gente.

    sobrevivientes(g -> g+1) = nvo_ing_{g+1,t+1} + repetidores_{g,t+1}
    abandono_g = [1 - sobrevivientes / alumnos_{g,t}] * 100

Sumar los repetidores del propio grado evita contar como desertor a quien sigue
inscrito pero no fue promovido. Para el último grado la salida legítima es el
egreso: sobrevivientes(3) = EG_t + repetidores_{3,t+1}.

LIMITACIÓN: MOVILIDAD INTERMUNICIPAL

El F911 registra planteles, no alumnos, así que quien cambia de municipio sin
dejar la escuela cuenta como abandono en el origen y como nuevo ingreso en el
destino. Sesga al alza en municipios emisores y a la baja en receptores. En
Guerrero el sesgo es material: Acapulco y Chilpancingo concentran oferta de
bachillerato que absorbe alumnos de municipios rurales. Es el argumento central
para usar efectos fijos por municipio — si la movilidad de cada municipio es
estable en el tiempo, el efecto fijo la absorbe y el coeficiente de interés
queda limpio.

Uso:
    .venv/bin/python src/02_abandono.py
    .venv/bin/python src/02_abandono.py --verificar-egresados
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from carga import CICLOS_EMS, LIMPIO, RAIZ, f911_ems, iter_guerrero
from municipios import N_MUNICIPIOS_HISTORICO, a_panel

GRADOS = ["01", "2", "3"]

# Transiciones atravesadas por el cierre de escuelas de la pandemia. No se
# excluyen: se marcan, para poder estimar con y sin ellas y para contrastarlas.
TRANSICIONES_COVID = {"2019-2020→2020-2021", "2020-2021→2021-2022"}

SUMAR = (
    ["alumnos", "egresados", "docentes", "grupos", "escuelas"]
    + [f"{b}_{g}" for b in ("alumnos", "nvo_ing", "repetidores") for g in GRADOS]
)


def razon(num, den) -> pd.Series:
    """División que devuelve NaN donde el denominador es 0 o nulo.

    Un municipio sin matrícula no tiene abandono 0: no lo tiene definido. Como
    0 metería ceros falsos y sesgaría la media a la baja precisamente en los
    municipios más pequeños, que son los de mayor interés sustantivo.
    """
    num, den = pd.Series(num), pd.Series(den)
    return num / den.where(den > 0)


def verificar_egresados() -> None:
    """Comprueba a qué ciclo corresponde la columna `egresados`.

    Existe para que la decisión de tomar EG del archivo t+1 sea auditable y no
    un supuesto que el lector tenga que aceptar por fe.
    """
    cic = {c: f911_ems(c)[["escuela", "alumnos_3", "egresados"]] for c in CICLOS_EMS}
    print("A nivel plantel, egresados no puede exceder a los alumnos de 3º del")
    print("ciclo al que corresponde el egreso. Violaciones bajo cada lectura:\n")
    print(f"{'archivo t':>10} {'n':>5} | {'egreso DE t':>17} | {'egreso DE t-1':>17}")
    print(f"{'':>10} {'':>5} | {'viola':>8} {'%':>7} | {'viola':>8} {'%':>7}")
    for i, c in enumerate(CICLOS_EMS):
        if i == 0:
            continue
        a = cic[c].rename(columns={"alumnos_3": "a3_t", "egresados": "eg"})
        b = cic[CICLOS_EMS[i - 1]].rename(columns={"alumnos_3": "a3_prev"})
        j = a.merge(b[["escuela", "a3_prev"]], on="escuela")
        j = j[j.eg > 0]
        t = j[j.a3_t > 0]
        p = j[j.a3_prev > 0]
        vt, vp = (t.eg > t.a3_t), (p.eg > p.a3_prev)
        print(f"{c:>10} {len(j):>5} | {int(vt.sum()):>8} {100*vt.mean():>6.1f}% "
              f"| {int(vp.sum()):>8} {100*vp.mean():>6.1f}%")
    print("\nLa lectura 'egreso del ciclo t-1' es la única compatible con los datos,")
    print("así que para el abandono del ciclo t se usa `egresados` del archivo t+1.")


def agrega_municipal(ciclo: str) -> pd.DataFrame:
    """Suma el F911 de planteles a municipios, con la geografía del panel."""
    d = f911_ems(ciclo)
    d["cve_panel"] = a_panel(d["cve_inegi"])

    g = d.groupby("cve_panel", as_index=False)[SUMAR].sum(min_count=1)
    g["planteles"] = d.groupby("cve_panel")["escuela"].nunique().values
    priv = d.assign(
        priv=np.where(d["control"].str.strip().str.upper() == "PRIVADO", d["alumnos"], 0.0)
    ).groupby("cve_panel")["priv"].sum()
    g["pct_privado"] = (100 * razon(priv.values, g["alumnos"])).values
    return g.rename(columns={"cve_panel": "cve_inegi"})


def construye_panel() -> pd.DataFrame:
    ciclos = {c: agrega_municipal(c) for c in CICLOS_EMS}
    puente = iter_guerrero()[["cve_inegi", "nom_mun", "pob_15a17", "grado_prom_escolaridad"]]

    filas = []
    for ini, fin in zip(CICLOS_EMS, CICLOS_EMS[1:]):
        a = ciclos[ini].drop(columns=["egresados"])  # ese egresados es del ciclo ini-1
        b = ciclos[fin].add_suffix("_fin").rename(columns={"cve_inegi_fin": "cve_inegi"})
        t = a.merge(b, on="cve_inegi", how="outer")
        t["transicion"] = f"{ini}→{fin}"
        t["ciclo_inicio"], t["ciclo_fin"] = ini, fin
        filas.append(t)
    p = pd.concat(filas, ignore_index=True)

    # `egresados_fin` viene del archivo del ciclo de cierre, así que son los que
    # egresaron al final del ciclo de inicio: el EG_t que pide la fórmula.
    p = p.rename(columns={"egresados_fin": "egresados_del_ciclo_ini"})
    eg = p["egresados_del_ciclo_ini"]

    sobrevive = p["alumnos_fin"] - p["nvo_ing_01_fin"] + eg
    p["abandono"] = 100 * (1 - razon(sobrevive, p["alumnos"]))

    # Descomposicion por grado: la misma identidad, abierta por punto de fuga.
    for g, sig in (("01", "2"), ("2", "3")):
        s = p[f"nvo_ing_{sig}_fin"] + p[f"repetidores_{g}_fin"]
        p[f"abandono_g{g}"] = 100 * (1 - razon(s, p[f"alumnos_{g}"]))
    p["abandono_g3"] = 100 * (1 - razon(eg + p["repetidores_3_fin"], p["alumnos_3"]))

    p["alumnos_por_docente"] = razon(p["alumnos"], p["docentes"])
    # `grupos` es el mejor proxy de aulas disponible: el F911 de media superior
    # no reporta aulas, y un grupo ocupa un aula por turno.
    p["alumnos_por_grupo"] = razon(p["alumnos"], p["grupos"])
    p["covid"] = p["transicion"].isin(TRANSICIONES_COVID)

    p = p.merge(puente, on="cve_inegi", how="left")
    p["cobertura_15a17"] = 100 * razon(p["alumnos"], p["pob_15a17"])

    orden = [
        "cve_inegi", "nom_mun", "transicion", "ciclo_inicio", "ciclo_fin", "covid",
        "abandono", "abandono_g01", "abandono_g2", "abandono_g3",
        # Insumos crudos, para poder recalcular sin volver a los 6 CSV del F911.
        "alumnos", "alumnos_fin", "egresados_del_ciclo_ini",
        "alumnos_01", "alumnos_2", "alumnos_3",
        "nvo_ing_01_fin", "nvo_ing_2_fin", "nvo_ing_3_fin",
        "repetidores_01_fin", "repetidores_2_fin", "repetidores_3_fin",
        "docentes", "grupos", "escuelas", "planteles", "pct_privado",
        "alumnos_por_docente", "alumnos_por_grupo",
        "pob_15a17", "cobertura_15a17", "grado_prom_escolaridad",
    ]
    return p[orden].sort_values(["transicion", "cve_inegi"]).reset_index(drop=True)


def reporta(p: pd.DataFrame) -> list[str]:
    problemas = []
    print(f"Panel: {len(p)} filas = {p.cve_inegi.nunique()} municipios "
          f"× {p.transicion.nunique()} transiciones")
    if p.cve_inegi.nunique() != N_MUNICIPIOS_HISTORICO:
        problemas.append(
            f"el panel tiene {p.cve_inegi.nunique()} municipios y no "
            f"{N_MUNICIPIOS_HISTORICO}: el colapso de municipios escindidos falló"
        )
    if p.nom_mun.isna().any():
        problemas.append(f"{int(p.nom_mun.isna().sum())} filas sin nombre (no cruzaron)")

    print("\n=== Abandono estatal por transición (agregado, no promedio de tasas) ===")
    print(f"{'transición':>25} {'abandono':>9} {'matrícula':>10} {'COVID':>6}")
    for tr, g in p.groupby("transicion", sort=True):
        tasa = 100 * (1 - (g.alumnos_fin.sum() - g.nvo_ing_01_fin.sum()
                           + g.egresados_del_ciclo_ini.sum()) / g.alumnos.sum())
        print(f"{tr:>25} {tasa:>8.2f}% {g.alumnos.sum():>10,.0f} "
              f"{'sí' if g.covid.iloc[0] else '':>6}")

    print("\n=== Descomposición por grado (media municipal, sin ciclos COVID) ===")
    sc = p[~p.covid]
    for g, etq in (("01", "1º → 2º"), ("2", "2º → 3º"), ("3", "3º → egreso")):
        s = sc[f"abandono_g{g}"].dropna()
        print(f"  {etq:14s} media={s.mean():>6.2f}%  mediana={s.median():>6.2f}%  "
              f"p90={s.quantile(.9):>6.2f}%")

    print("\n=== Distribución municipal del abandono ===")
    s = p.abandono.dropna()
    print(f"  n={len(s)}  media={s.mean():.2f}%  mediana={s.median():.2f}%  "
          f"de={s.std():.2f}")
    print(f"  p05={s.quantile(.05):>6.2f}%  p25={s.quantile(.25):>6.2f}%  "
          f"p75={s.quantile(.75):>6.2f}%  p95={s.quantile(.95):>6.2f}%")
    neg = int((s < 0).sum())
    print(f"  negativos: {neg} de {len(s)} ({100*neg/len(s):.1f}%)  "
          f"min={s.min():.1f}%  max={s.max():.1f}%")
    if neg:
        print("  Un abandono negativo es matrícula que creció más de lo que la cohorte")
        print("  permite: llegada de alumnos de otros municipios o reingresos. Se deja")
        print("  como está; recortarlo a cero inventaría datos y sesgaría la media.")

    print("\n=== Municipios con mayor abandono promedio (sin COVID, matrícula ≥ 200) ===")
    agg = (sc[sc.alumnos >= 200].groupby(["cve_inegi", "nom_mun"])
           .agg(abandono=("abandono", "mean"), alumnos=("alumnos", "mean"),
                al_x_doc=("alumnos_por_docente", "mean"))
           .sort_values("abandono", ascending=False))
    print(agg.head(8).to_string(float_format=lambda x: f"{x:>8.2f}"))
    print("\n=== Y los de menor ===")
    print(agg.tail(5).to_string(float_format=lambda x: f"{x:>8.2f}"))

    faltan = int(p.abandono.isna().sum())
    if faltan:
        sinmat = p[p.abandono.isna()].nom_mun.nunique()
        print(f"\nSin abandono definido: {faltan} filas en {sinmat} municipio(s) "
              f"sin matrícula de EMS en el ciclo inicial.")
    return problemas


def main() -> int:
    if "--verificar-egresados" in sys.argv[1:]:
        verificar_egresados()
        return 0

    LIMPIO.mkdir(parents=True, exist_ok=True)
    p = construye_panel()
    problemas = reporta(p)

    destino = LIMPIO / "panel_abandono_ems.csv"
    p.to_csv(destino, index=False, encoding="utf-8")
    print(f"\nEscrito: {destino.relative_to(RAIZ)}  "
          f"({len(p)} filas, {len(p.columns)} columnas)")

    if problemas:
        print(f"\n{len(problemas)} problema(s):")
        for x in problemas:
            print(f"  - {x}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
