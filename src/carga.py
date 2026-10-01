"""Lectores de las fuentes crudas, con el esquema ya homologado.

Todo lo que sabemos sobre las rarezas de cada archivo vive aquí, para que los
scripts de análisis reciban datos ya comparables entre ciclos.

Lo que se descubrió inspeccionando los datos y que estos lectores resuelven:

- El ciclo 2024-2025 renombró los sufijos de grado de _2.._5 a _02.._05 y
  nomescuela a nom_escuela. Se homologa al esquema de los cinco ciclos previos.
- `cv_mun` viene sin ceros a la izquierda; el ITER y CONEVAL sí los traen.
- La modalidad NO ESCOLARIZADA no desglosa matrícula por grado: sus 20 filas de
  Guerrero 2023-2024 reportan 4,935 alumnos con la suma de grados en cero. Por
  eso `solo_escolarizada` está en True por defecto; dejarla entrar mete ruido en
  cualquier cálculo por cohorte y además su dinámica de abandono no es
  comparable (no tiene aulas ni grupos en el mismo sentido).
- `nvo_ing_g` NO es nuevo ingreso al nivel: se verificó que
  `nvo_ing_g + repetidores_g == alumnos_g` exactamente en cada grado, así que es
  "alumnos del grado g que no son repetidores". Para la fórmula oficial de
  abandono el nuevo ingreso al nivel es `nvo_ing_01`.
- `existentes` NO es matrícula de fin de ciclo: en 280 de 878 filas supera a
  `alumnos` (hasta 29% más). No se usa; su semántica no está documentada en el
  conjunto abierto.
- `egresados` en el archivo del ciclo t son los egresados al CIERRE DEL CICLO
  t-1, no del ciclo t. El Formato 911 se levanta al inicio de cursos y pregunta
  por el egreso del ciclo previo. Se comprobó a nivel plantel: leído como mismo
  ciclo, entre 32% y 46% de los planteles reportarían más egresados que alumnos
  de 3º, lo que es imposible; leído como ciclo anterior, las violaciones bajan a
  8-10% y se explican por traslados entre planteles. Verificable con:
      .venv/bin/python src/02_abandono.py --verificar-egresados
  Consecuencia: para medir el abandono del ciclo t hay que tomar `egresados` del
  archivo del ciclo t+1. Ignorarlo corre la variable dependiente un ciclo
  completo y produce tasas de abandono negativas en el último grado.
- CONEVAL codifica los faltantes como -999, no como celda vacía.

Media superior en Guerrero solo ocupa los grados 1 a 3; las columnas _4 y _5
están en cero en los seis ciclos.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from municipios import CVE_GUERRERO, cve_inegi, cve_inegi_desde_concatenada, normaliza_nombre

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "datos" / "crudo"
LIMPIO = RAIZ / "datos" / "limpio"

CICLOS_EMS = ["2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
GRADOS_EMS = ["01", "2", "3"]

# Columnas del F911 que se tratan como numéricas. El resto queda como texto.
_BASES_POR_GRADO = ("alumnos", "mujeres", "hombres", "nvo_ing", "repetidores", "grupos")
_NUMERICAS = (
    ["escuelas", "alumnos", "mujeres", "hombres", "docentes", "docentes_m", "docentes_h",
     "nvo_ing", "repetidores", "grupos", "egresados", "egresados_m", "egresados_h",
     "titulados", "existentes"]
    + [f"{b}_{g}" for b in _BASES_POR_GRADO for g in GRADOS_EMS]
)

DEMOGRAFICAS_ITER = {
    "POBTOT": "pob_total",
    "P_6A11": "pob_6a11",
    "P_12A14": "pob_12a14",
    "P_15A17": "pob_15a17",   # tramo de edad de media superior
    "P_18A24": "pob_18a24",
    "GRAPROES": "grado_prom_escolaridad",
}


def _a_numero(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def f911_ems(ciclo: str, solo_guerrero: bool = True,
             solo_escolarizada: bool = True) -> pd.DataFrame:
    """Lee un ciclo del Formato 911 de media superior con el esquema homologado."""
    d = pd.read_csv(CRUDO / f"f911_ems_{ciclo}.csv", dtype=str, low_memory=False)
    d.columns = [c.strip().lower() for c in d.columns]

    d = d.rename(columns={"nom_escuela": "nomescuela"})
    d = d.rename(columns={
        f"{base}_0{g}": f"{base}_{g}"
        for base in _BASES_POR_GRADO for g in (2, 3, 4, 5)
    })

    if solo_guerrero:
        d = d[d["entidad"].astype(str).str.strip().str.lstrip("0") == CVE_GUERRERO]
    if solo_escolarizada:
        d = d[d["modalidad"].str.strip().str.upper() == "ESCOLARIZADA"]

    d = d.copy()
    d["cve_inegi"] = cve_inegi(d["entidad"], d["cv_mun"])
    d["ciclo"] = ciclo
    for c in _NUMERICAS:
        if c in d.columns:
            d[c] = _a_numero(d[c])
    return d.reset_index(drop=True)


def iter_guerrero() -> pd.DataFrame:
    """Totales municipales del ITER del Censo 2020, leídos directo del zip."""
    with zipfile.ZipFile(CRUDO / "inegi_iter_guerrero_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig", low_memory=False)

    # LOC=='0000' es el total municipal; MUN=='000' es el total estatal y se
    # excluye o Guerrero entero entraría como un municipio más.
    mun = d[(d["LOC"] == "0000") & (d["MUN"] != "000")].copy()
    salida = pd.DataFrame({
        "cve_inegi": cve_inegi(mun["ENTIDAD"], mun["MUN"]),
        "nom_mun": mun["NOM_MUN"].values,
    })
    for origen, destino in DEMOGRAFICAS_ITER.items():
        # '*' = reservado por confidencialidad, 'N/D' = no disponible. NaN, no 0.
        salida[destino] = _a_numero(mun[origen].replace({"*": None, "N/D": None})).values
    salida["nom_mun_norm"] = normaliza_nombre(salida["nom_mun"])
    return salida.sort_values("cve_inegi").reset_index(drop=True)


# Contexto socioeconómico derivado del ITER. La clave del diseño es que todas
# son tasas o porcentajes, no conteos: un conteo absoluto en un panel municipal
# solo mide el tamaño del municipio y correlaciona con todo.
def iter_contexto() -> pd.DataFrame:
    """Contexto municipal del Censo 2020, en tasas listas para modelar.

    `asistencia_15a17` merece atención especial: es la proporción de residentes
    de 15 a 17 años que asisten a la escuela, medida por LUGAR DE RESIDENCIA.
    El F911 mide por lugar del plantel, así que las dos series discrepan
    justamente donde hay movilidad intermunicipal. Contrastarlas es la única
    forma de acotar ese sesgo con los datos disponibles.
    """
    with zipfile.ZipFile(CRUDO / "inegi_iter_guerrero_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig", low_memory=False)

    m = d[(d["LOC"] == "0000") & (d["MUN"] != "000")].copy()
    for c in m.columns:
        if c not in ("ENTIDAD", "NOM_ENT", "MUN", "NOM_MUN", "LOC", "NOM_LOC"):
            m[c] = _a_numero(m[c].replace({"*": None, "N/D": None}))

    out = pd.DataFrame({"cve_inegi": cve_inegi(m["ENTIDAD"], m["MUN"]).values})
    pct = lambda num, den: (100 * m[num].values / m[den].where(m[den] > 0).values)

    # Marginación y composición étnica. En Guerrero la región de La Montaña
    # concentra población hablante de lengua indígena y el mayor rezago, así que
    # esta variable es central y no un control decorativo.
    out["pct_hli"] = pct("P3YM_HLI", "P_3YMAS")
    out["grado_prom_escolaridad"] = m["GRAPROES"].values
    out["pct_15ymas_sin_escolaridad"] = pct("P15YM_SE", "P_15YMAS")

    # Conectividad del hogar: el mecanismo por el que el cierre de escuelas pudo
    # golpear distinto a cada municipio, porque la clase a distancia la requería.
    out["pct_viv_con_internet"] = pct("VPH_INTER", "TVIVPARHAB")
    out["pct_viv_piso_tierra"] = pct("VPH_PISODT", "TVIVPARHAB")

    # Costo de oportunidad de seguir estudiando.
    out["tasa_desocupacion"] = pct("PDESOCUP", "PEA")
    out["pct_pea"] = pct("PEA", "P_15YMAS")

    # Asistencia escolar censal, por residencia (contraste con el F911).
    out["asistencia_15a17"] = pct("P15A17A", "P_15A17")
    out["asistencia_18a24"] = pct("P18A24A", "P_18A24")
    out["pct_12a14_no_asiste"] = pct("P12A14NOA", "P_12A14")

    out["pct_hogares_jefa_mujer"] = pct("HOGJEF_F", "TOTHOG")
    out["pct_sin_derechohabiencia"] = pct("PSINDER", "POBTOT")
    out["pct_con_discapacidad"] = pct("PCON_DISC", "POBTOT")
    return out.sort_values("cve_inegi").reset_index(drop=True)


# Columnas del ITER que usa el modelo nacional. Se declaran para no cargar las
# 286 del archivo: el ITER nacional son 149 MB y leerlo entero multiplica por
# ocho la memoria sin aportar nada.
ITER_COLUMNAS = [
    "ENTIDAD", "NOM_ENT", "MUN", "NOM_MUN", "LOC", "NOM_LOC",
    "LONGITUD", "LATITUD", "ALTITUD", "POBTOT",
    "P_6A11", "P6A11_NOA", "P_12A14", "P12A14NOA", "P_15A17", "P15A17A",
    "P_18A24", "P18A24A", "P_3YMAS", "P3YM_HLI", "P_15YMAS", "P15YM_SE",
    "GRAPROES", "PEA", "PDESOCUP", "POCUPADA", "TVIVPARHAB", "VPH_INTER",
    "VPH_PISODT", "VPH_AUTOM", "TOTHOG", "HOGJEF_F", "PSINDER", "PCON_DISC",
]


def iter_nacional(solo_municipales: bool = False) -> pd.DataFrame:
    """Lee el ITER nacional del Censo 2020 desde el zip, sin descomprimirlo.

    `solo_municipales=True` devuelve el renglón de total por municipio (LOC
    '0000'); en falso devuelve las localidades, que es lo que necesita el
    cálculo de distancias.
    """
    with zipfile.ZipFile(CRUDO / "inegi_iter_nacional_2020.zip") as zf:
        interno = next(n for n in zf.namelist()
                       if "conjunto_de_datos/" in n and n.endswith(".csv"))
        with zf.open(interno) as f:
            d = pd.read_csv(f, dtype=str, encoding="utf-8-sig",
                            usecols=ITER_COLUMNAS, low_memory=False)

    # MUN '000' es el total estatal y LOC '9998'/'9999' son agregados de
    # localidades de una y dos viviendas, que no tienen ubicación.
    d = d[d["MUN"] != "000"]
    if solo_municipales:
        d = d[d["LOC"] == "0000"]
    else:
        d = d[(d["LOC"] != "0000") & (~d["LOC"].isin(["9998", "9999"]))]
    return d.reset_index(drop=True)


def f911_nacional(ciclo: str, nivel: str) -> pd.DataFrame:
    """Localidades del país con al menos un plantel del nivel indicado.

    `nivel` es "EMS" para media superior o PRIMARIA/SECUNDARIA para básica, que
    viven en archivos con esquemas distintos.
    """
    if nivel == "EMS":
        d = pd.read_csv(CRUDO / f"f911_ems_{ciclo}.csv", dtype=str, low_memory=False)
        d.columns = [c.strip().lower() for c in d.columns]
        d = d[d["modalidad"].str.strip().str.upper() == "ESCOLARIZADA"]
        d = d[_a_numero(d["alumnos"]).fillna(0) > 0]
        ent, mun, loc = d["entidad"], d["cv_mun"], d["cv_loc"]
    else:
        d = pd.read_csv(CRUDO / f"f911_basica_{ciclo}.csv", dtype=str, low_memory=False,
                        usecols=["entidad", "municipio", "localidad", "nivel", "insc_t"])
        d = d[d["nivel"].str.strip().str.upper() == nivel]
        d = d[_a_numero(d["insc_t"]).fillna(0) > 0]
        ent, mun, loc = d["entidad"], d["municipio"], d["localidad"]

    return pd.DataFrame({
        "cve_inegi": cve_inegi(ent, mun).values,
        "cve_loc": loc.astype(str).str.strip().str.zfill(4).values,
    }).drop_duplicates().reset_index(drop=True)


def coneval(archivo: str) -> pd.DataFrame:
    """Lee un CSV de CONEVAL con -999 convertido a NaN y clave normalizada.

    El centinela -999 es el detalle que más daño hace si pasa inadvertido: entra
    a una regresión como un número plausible y sesga los coeficientes sin
    producir ningún error.
    """
    d = pd.read_csv(CRUDO / archivo, dtype=str, encoding="utf-8-sig", low_memory=False)
    d.columns = [c.strip().lower() for c in d.columns]
    d["cve_inegi"] = cve_inegi_desde_concatenada(d["clave_municipio"])

    for c in d.columns:
        if c.endswith(("_porcentaje", "_poblacion")) or c in ("poblacion", "irs", "lugar") \
                or c.startswith("i_"):
            d[c] = _a_numero(d[c]).replace(-999.0, pd.NA)
    return d


def guerrero(d: pd.DataFrame) -> pd.DataFrame:
    return d[d["cve_inegi"].str.startswith(CVE_GUERRERO)].copy()
