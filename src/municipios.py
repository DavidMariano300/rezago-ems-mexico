"""Claves municipales de Guerrero: normalización y continuidad temporal.

Dos problemas que rompen los cruces en silencio y que este módulo resuelve.

1. Formato de clave. Cada fuente escribe la clave distinto:
     Formato 911  entidad='12',  cv_mun='81'    (sin ceros a la izquierda)
     ITER INEGI   ENTIDAD='12',  MUN='081'      (con ceros)
     CONEVAL      clave_municipio='12081'       (concatenada, 5 dígitos)
   Se unifica todo a `cve_inegi`: cadena de 5 caracteres, entidad 2 + municipio 3.
   Se usa cadena y no entero a propósito: como entero, 01001 (Aguascalientes)
   se vuelve 1001 y se confunde con Guerrero al reconstruirlo mal.

2. Continuidad del panel. Guerrero pasó de 81 a 85 municipios: el Congreso
   estatal creó cuatro en 2023 y aparecen en el Formato 911 a partir del ciclo
   2024-2025. Un panel que los trate como municipios nuevos genera series
   truncadas para ellos y saltos artificiales en sus municipios de origen (el
   origen "pierde" matrícula de golpe sin que nadie haya abandonado la escuela).

   El mapeo de abajo no viene de la literatura ni de memoria: se derivó de los
   datos siguiendo la clave de centro de trabajo (CCT) de cada plantel entre los
   ciclos 2023-2024 y 2024-2025. Una CCT identifica al plantel y no cambia con
   el redistritado, así que una escuela que aparece en otro municipio delata que
   el municipio se partió. Las 10 escuelas que cambiaron apuntan cada una a un
   solo origen, sin ambigüedad. Reproducible con:
       .venv/bin/python src/01_puente_municipios.py --derivar-mapeo
"""

from __future__ import annotations

import unicodedata

import pandas as pd

CVE_GUERRERO = "12"

# municipio creado en 2023 -> municipio del que se desprendió
MUNICIPIOS_ESCINDIDOS = {
    "12082": "12053",  # Las Vigas             <- San Marcos
    "12083": "12012",  # Ñuu Savi              <- Ayutla de los Libres
    "12084": "12041",  # Santa Cruz del Rincón <- Malinaltepec
    "12085": "12023",  # San Nicolás           <- Cuajinicuilapa
}

# Guerrero antes y después de la reforma de 2023. Son las dos cifras contra las
# que se valida todo: un conteo que no dé 81 u 85 significa que el filtro o el
# cruce está mal.
N_MUNICIPIOS_HISTORICO = 81
N_MUNICIPIOS_ACTUAL = 85


def cve_inegi(entidad, municipio) -> pd.Series:
    """Construye la clave de 5 caracteres a partir de columnas entidad/municipio."""
    ent = pd.Series(entidad).astype(str).str.strip().str.zfill(2)
    mun = pd.Series(municipio).astype(str).str.strip().str.zfill(3)
    return ent + mun


def cve_inegi_desde_concatenada(clave) -> pd.Series:
    """Normaliza la clave concatenada de CONEVAL, que llega sin cero inicial."""
    return pd.Series(clave).astype(str).str.strip().str.zfill(5)


def a_panel(cve: pd.Series) -> pd.Series:
    """Colapsa los municipios de 2023 en su origen para dar un panel balanceado.

    Aplicarlo a TODOS los ciclos, no solo a los posteriores a 2023: el objetivo
    es que la unidad de análisis sea la misma geografía en los seis ciclos.
    """
    return pd.Series(cve).replace(MUNICIPIOS_ESCINDIDOS)


def normaliza_nombre(s) -> pd.Series:
    """Minúsculas sin acentos ni puntuación, solo para diagnóstico.

    Nunca para cruzar: el briefing es explícito en que el join va por clave. Esto
    sirve para reportar en qué municipio hay una discrepancia de forma legible.
    """
    out = (
        pd.Series(s)
        .astype(str)
        .str.normalize("NFKD")
        .map(lambda x: "".join(c for c in unicodedata.normalize("NFKD", x)
                               if not unicodedata.combining(c)))
        .str.lower()
        .str.replace(r"[^a-z0-9ñ ]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return out
