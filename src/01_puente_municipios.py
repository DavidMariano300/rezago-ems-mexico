"""Construye la tabla puente de municipios de Guerrero y valida los cruces.

Salida: datos/limpio/puente_municipios.csv — 81 municipios con la clave INEGI
canónica, el nombre oficial y el marco demográfico del Censo 2020 (población por
grupo de edad escolar, que da el denominador de las tasas de cobertura).

El script no solo construye: valida que las claves de las tres fuentes crucen
contra el puente y falla si no. Un join silencioso que pierde municipios es el
riesgo central del proyecto, así que se convierte en error explícito.

Uso:
    .venv/bin/python src/01_puente_municipios.py
    .venv/bin/python src/01_puente_municipios.py --derivar-mapeo
"""

from __future__ import annotations

import sys

import pandas as pd

from carga import CICLOS_EMS, CRUDO, DEMOGRAFICAS_ITER, LIMPIO, RAIZ
from carga import coneval as lee_coneval
from carga import f911_ems, guerrero, iter_guerrero
from municipios import (
    CVE_GUERRERO,
    MUNICIPIOS_ESCINDIDOS,
    N_MUNICIPIOS_ACTUAL,
    N_MUNICIPIOS_HISTORICO,
)

def derivar_mapeo() -> None:
    """Reconstruye el mapeo de municipios escindidos rastreando CCT entre ciclos.

    Existe para que el mapeo en municipios.py sea auditable y no un dato que el
    lector tenga que creer.
    """
    ant = f911_ems("2023-2024")
    nvo = f911_ems("2024-2025")
    a = ant[["escuela", "cve_inegi", "c_nom_mun"]].drop_duplicates("escuela")
    n = nvo[["escuela", "cve_inegi", "c_nom_mun"]].drop_duplicates("escuela")
    j = a.merge(n, on="escuela", suffixes=("_ant", "_nvo"))
    cambio = j[j.cve_inegi_ant != j.cve_inegi_nvo]

    print(f"Escuelas rastreadas por CCT en ambos ciclos: {len(j):,}")
    print(f"Escuelas que cambiaron de municipio: {len(cambio)}\n")
    derivado = {}
    for cve in sorted(cambio.cve_inegi_nvo.unique()):
        sub = cambio[cambio.cve_inegi_nvo == cve]
        origenes = sub.cve_inegi_ant.value_counts()
        derivado[cve] = origenes.index[0]
        nom = sub.c_nom_mun_nvo.iloc[0]
        det = ", ".join(f"{o} ({c} esc.)" for o, c in origenes.items())
        marca = "" if len(origenes) == 1 else "  <-- MÚLTIPLES ORÍGENES, revisar"
        print(f"  {cve} {nom:24s} <- {det}{marca}")

    print()
    if derivado == MUNICIPIOS_ESCINDIDOS:
        print("Coincide con MUNICIPIOS_ESCINDIDOS en municipios.py.")
    else:
        print("NO coincide con municipios.py:")
        print(f"  derivado ahora : {derivado}")
        print(f"  en el módulo   : {MUNICIPIOS_ESCINDIDOS}")


def valida(puente: pd.DataFrame) -> list[str]:
    """Cruza las claves de cada fuente contra el puente. Devuelve los problemas."""
    problemas: list[str] = []
    claves = set(puente.cve_inegi)
    esperadas = {f"{CVE_GUERRERO}{i:03d}" for i in range(1, N_MUNICIPIOS_HISTORICO + 1)}

    print(f"Puente: {len(puente)} municipios")
    if len(puente) != N_MUNICIPIOS_HISTORICO:
        problemas.append(
            f"el puente tiene {len(puente)} municipios, se esperaban "
            f"{N_MUNICIPIOS_HISTORICO} (el Censo 2020 es previo a la reforma de 2023)"
        )
    if faltan := esperadas - claves:
        problemas.append(f"claves 001-081 ausentes del puente: {sorted(faltan)}")
    if sobran := claves - esperadas:
        problemas.append(f"claves inesperadas en el puente: {sorted(sobran)}")

    print("\n--- Formato 911, media superior ---")
    for ciclo in CICLOS_EMS:
        d = f911_ems(ciclo)
        suyas = set(d.cve_inegi)
        nuevas = suyas & set(MUNICIPIOS_ESCINDIDOS)
        huerfanas = suyas - claves - set(MUNICIPIOS_ESCINDIDOS)
        esperado = N_MUNICIPIOS_ACTUAL if ciclo == "2024-2025" else N_MUNICIPIOS_HISTORICO
        estado = "ok" if len(suyas) == esperado and not huerfanas else "REVISAR"
        print(f"  {ciclo}  municipios={len(suyas):>3}  escindidos={len(nuevas)}  "
              f"sin_puente={len(huerfanas)}  [{estado}]")
        if huerfanas:
            problemas.append(f"F911 {ciclo}: claves sin puente {sorted(huerfanas)}")

    print("\n--- CONEVAL ---")
    for arch in ("coneval_irs_municipal_2020.csv",
                 "coneval_pobreza_municipal.csv",
                 "coneval_pobreza_edad.csv"):
        d = lee_coneval(arch)
        gro = set(guerrero(d).cve_inegi)
        huerfanas = gro - claves - set(MUNICIPIOS_ESCINDIDOS)
        cubre = len(gro & claves)
        estado = "ok" if cubre == N_MUNICIPIOS_HISTORICO and not huerfanas else "REVISAR"
        print(f"  {arch:36s} Guerrero={len(gro):>3}  cruzan={cubre:>3}  "
              f"sin_puente={len(huerfanas)}  [{estado}]")
        if huerfanas:
            problemas.append(f"{arch}: claves sin puente {sorted(huerfanas)}")
        if cubre != N_MUNICIPIOS_HISTORICO:
            problemas.append(
                f"{arch}: solo cruzan {cubre} de {N_MUNICIPIOS_HISTORICO} municipios"
            )
    return problemas


def main() -> int:
    if "--derivar-mapeo" in sys.argv[1:]:
        derivar_mapeo()
        return 0

    LIMPIO.mkdir(parents=True, exist_ok=True)
    puente = iter_guerrero()
    problemas = valida(puente)

    destino = LIMPIO / "puente_municipios.csv"
    puente.to_csv(destino, index=False, encoding="utf-8")
    print(f"\nEscrito: {destino.relative_to(RAIZ)}")
    print(f"  {len(puente)} municipios, {len(puente.columns)} columnas")
    faltantes = puente[list(DEMOGRAFICAS_ITER.values())].isna().sum()
    if faltantes.any():
        print("  valores faltantes:",
              ", ".join(f"{k}={v}" for k, v in faltantes.items() if v))

    if problemas:
        print(f"\n{len(problemas)} problema(s) de consistencia:")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("\nTodas las claves de las tres fuentes cruzan contra el puente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
