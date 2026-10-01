"""¿De qué está hecha la brecha de asistencia de 15 a 17 años?

Salida: datos/limpio/localidades_modelo.csv

EL PROBLEMA QUE ATACA

El diseño de 06_localidades.py identifica un efecto limpio de la distancia
(-1.70 pp/km) pero de exposición baja: cerrar todos los diferenciales de
distancia recuperaría 1.66 puntos de los 29 que le faltan a Guerrero. Quedan
~27 puntos sin explicar, y ese hueco es la frontera del trabajo.

Aquí se parte en dos preguntas separables.

1. DESCOMPOSICIÓN DEL EMBUDO. Un joven de 16 años no asiste al bachillerato por
   una de dos razones muy distintas: o ya había salido del sistema antes (no
   terminó secundaria) o terminó secundaria y no continuó. La política que
   corresponde a cada caso no es la misma. Con la asistencia de 12-14 de la
   misma localidad se puede separar:

       brecha_total    = 100 - asist_15a17
       brecha_arriba   = 100 - asist_12a14      (ya estaban fuera antes)
       brecha_margen   = asist_12a14 - asist_15a17   (salieron en la transición)

   Es contabilidad, no causalidad: supone que la cohorte de 12-14 de hoy se
   parece a la que fue la de 15-17 hace tres años. En una localidad con
   demografía estable es razonable; conviene declararlo.

2. DESCOMPOSICIÓN DE LA VARIANZA. Se estima la asistencia de 15-17 a nivel
   localidad agregando bloques de variables en orden, con efectos fijos de
   municipio desde el inicio, para ver cuánta variación interna al municipio
   explica cada bloque. El orden importa y no es neutral: se pone primero el
   embudo aguas arriba porque es lo más cercano a una condición previa, y la
   distancia después, para NO regalarle a la distancia la varianza que comparte
   con el resto. Es la prueba más exigente para el efecto de la distancia.

NOTA SOBRE CIRCULARIDAD: se excluye GRAPROES (grado promedio de escolaridad de
la población de 15 y más) porque se construye con la misma población cuya
asistencia es la variable dependiente. Incluirlo daría un R² alto y vacío.

Uso:
    .venv/bin/python src/09_brecha_restante.py
"""

from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd
import statsmodels.api as sm

from carga import CRUDO, LIMPIO, RAIZ
from municipios import cve_inegi


def num(s):
    return pd.to_numeric(pd.Series(s).replace({"*": None, "N/D": None}), errors="coerce")


def contexto_localidad() -> pd.DataFrame:
    """Covariables del ITER a nivel localidad, todas como tasas."""
    with zipfile.ZipFile(CRUDO / "inegi_iter_guerrero_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig", low_memory=False)
    d = d[(d.MUN != "000") & (d.LOC != "0000") & (~d.LOC.isin(["9998", "9999"]))].copy()

    def pct(a, b):
        x, y = num(d[a]).values, num(d[b]).values
        return 100 * x / np.where(y > 0, y, np.nan)

    # `altitud` ya viene en localidades_cohortes.csv; no se repite aquí para que
    # el merge no genere altitud_x/altitud_y y rompa las fórmulas por nombre.
    o = pd.DataFrame({
        "cve_inegi": cve_inegi(d.ENTIDAD, d.MUN).values,
        "cve_loc": d.LOC.str.zfill(4).values,
        "pct_desocupacion": pct("PDESOCUP", "PEA"),
        "pct_pea": pct("PEA", "P_15YMAS"),
        "pct_internet": pct("VPH_INTER", "TVIVPARHAB"),
        "pct_piso_tierra": pct("VPH_PISODT", "TVIVPARHAB"),
        "pct_auto": pct("VPH_AUTOM", "TVIVPARHAB"),
        "pct_sin_salud": pct("PSINDER", "POBTOT"),
        "pct_jefa_mujer": pct("HOGJEF_F", "TOTHOG"),
        "pct_sin_escolaridad": pct("P15YM_SE", "P_15YMAS"),
        "pct_discapacidad": pct("PCON_DISC", "POBTOT"),
        "personas_por_hogar": num(d.POBTOT).values / np.where(
            num(d.TOTHOG).values > 0, num(d.TOTHOG).values, np.nan),
    })
    return o


def r2_ponderado(y, X, w) -> float:
    m = sm.WLS(y, X, weights=w).fit()
    return m.rsquared


def main() -> int:
    loc = pd.read_csv(LIMPIO / "localidades_cohortes.csv",
                      dtype={"cve_inegi": str, "cve_loc": str})
    ctx = contexto_localidad()
    d = loc.merge(ctx, on=["cve_inegi", "cve_loc"], how="left")
    d = d.dropna(subset=["asist_15a17", "asist_12a14", "dist_ems", "pob_15a17"])
    d = d[d.pob_15a17 > 0].reset_index(drop=True)
    w = d.pob_15a17.values

    # ---------- 1. Descomposición del embudo ----------
    a15 = np.average(d.asist_15a17, weights=w)
    a12 = np.average(d.asist_12a14, weights=d.pob_12a14.where(d.pob_12a14 > 0).fillna(0))
    print("=" * 66)
    print("1. DE QUÉ ESTÁ HECHA LA BRECHA")
    print("=" * 66)
    print(f"  Asistencia 12-14 (edad de secundaria)     : {a12:>6.2f}%")
    print(f"  Asistencia 15-17 (edad de bachillerato)   : {a15:>6.2f}%")
    print()
    print(f"  Brecha total de 15-17 frente a la cobertura plena : {100-a15:>6.2f} pp")
    print(f"    ├─ ya estaban fuera a los 12-14 (embudo previo) : {100-a12:>6.2f} pp "
          f"({100*(100-a12)/(100-a15):>4.1f}% de la brecha)")
    print(f"    └─ salieron en la transición a bachillerato     : {a12-a15:>6.2f} pp "
          f"({100*(a12-a15)/(100-a15):>4.1f}% de la brecha)")
    print()
    print("  Supuesto contable: la cohorte de 12-14 de hoy se parece a la que fue")
    print("  la de 15-17 hace tres años. No es causal.")

    # ---------- 2. Descomposición de la varianza ----------
    print("\n" + "=" * 66)
    print("2. QUÉ EXPLICA LA VARIACIÓN ENTRE LOCALIDADES DEL MISMO MUNICIPIO")
    print("=" * 66)
    fe = pd.get_dummies(d.cve_inegi, prefix="m", drop_first=True, dtype=float)
    bloques = [
        ("Solo efectos fijos de municipio", []),
        ("+ embudo previo (asistencia 12-14)", ["asist_12a14"]),
        ("+ tamaño y altitud de la localidad", ["log_pob", "altitud"]),
        ("+ contexto socioeconómico", ["pct_desocupacion", "pct_pea", "pct_internet",
                                       "pct_piso_tierra", "pct_auto", "pct_sin_salud",
                                       "pct_jefa_mujer", "pct_sin_escolaridad",
                                       "pct_discapacidad", "personas_por_hogar"]),
        ("+ composición étnica", ["pct_hli"]),
        ("+ DISTANCIA al bachillerato", ["dist_ems"]),
    ]
    acum, previo = [], 0.0
    print(f"  {'bloque':40s} {'R²':>7s} {'ΔR²':>7s}")
    for etq, cols in bloques:
        acum += cols
        X = sm.add_constant(pd.concat([d[acum], fe], axis=1).fillna(0)) if acum \
            else sm.add_constant(fe)
        r2 = r2_ponderado(d.asist_15a17.values, X, w)
        print(f"  {etq:40s} {r2:>7.3f} {r2-previo:>+7.3f}")
        previo = r2

    # ---------- 3. Modelo final ----------
    print("\n" + "=" * 66)
    print("3. MODELO COMPLETO (coeficientes, errores agrupados por municipio)")
    print("=" * 66)
    X = sm.add_constant(pd.concat([d[acum], fe], axis=1).fillna(0))
    m = sm.WLS(d.asist_15a17.values, X, weights=w).fit(
        cov_type="cluster", cov_kwds={"groups": d.cve_inegi})
    orden = sorted(acum, key=lambda c: -abs(m.tvalues[c]))
    print(f"  {'variable':24s} {'β':>9s} {'EE':>7s} {'t':>7s} {'p':>8s}")
    for c in orden:
        marca = "  *" if m.pvalues[c] < 0.05 else ""
        print(f"  {c:24s} {m.params[c]:>+9.3f} {m.bse[c]:>7.3f} "
              f"{m.tvalues[c]:>+7.2f} {m.pvalues[c]:>8.4f}{marca}")
    print(f"\n  n={int(m.nobs):,} localidades  ·  81 municipios  ·  R²={m.rsquared:.3f}")

    # ---------- 4. ¿Y si el embudo previo es el verdadero cuello de botella? ----------
    print("\n" + "=" * 66)
    print("4. EL MISMO EJERCICIO SOBRE LA ASISTENCIA DE 12-14")
    print("=" * 66)
    print("  Si el problema está aguas arriba, conviene saber qué lo explica ahí.\n")
    cols12 = [c for c in acum if c not in ("asist_12a14", "dist_ems")] + ["dist_sec"]
    d12 = d.dropna(subset=["asist_12a14", "dist_sec", "pob_12a14"])
    d12 = d12[d12.pob_12a14 > 0]
    fe12 = pd.get_dummies(d12.cve_inegi, prefix="m", drop_first=True, dtype=float)
    X12 = sm.add_constant(pd.concat([d12[cols12].reset_index(drop=True),
                                     fe12.reset_index(drop=True)], axis=1).fillna(0))
    m12 = sm.WLS(d12.asist_12a14.values, X12, weights=d12.pob_12a14.values).fit(
        cov_type="cluster", cov_kwds={"groups": d12.cve_inegi})
    sig = [c for c in cols12 if m12.pvalues[c] < 0.05]
    print(f"  {'variable':24s} {'β':>9s} {'t':>7s} {'p':>8s}")
    for c in sorted(sig, key=lambda x: -abs(m12.tvalues[x])):
        print(f"  {c:24s} {m12.params[c]:>+9.3f} {m12.tvalues[c]:>+7.2f} "
              f"{m12.pvalues[c]:>8.4f}")
    print(f"\n  n={int(m12.nobs):,}  R²={m12.rsquared:.3f}   "
          f"(solo se listan las significativas al 5%)")

    d.to_csv(LIMPIO / "localidades_modelo.csv", index=False, encoding="utf-8")
    print(f"\nEscrito: {(LIMPIO/'localidades_modelo.csv').relative_to(RAIZ)}  "
          f"({len(d):,} filas, {len(d.columns)} columnas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
