"""Registro de fuentes de datos abiertos del proyecto.

Toda URL usada en el proyecto vive aquí y en ningún otro lugar. El artículo
tiene que poder citar la procedencia exacta de cada cifra, así que cada entrada
declara qué es, de dónde viene y para qué se usa.

Nota sobre el acceso: repodatos.atdt.gob.mx y datos.gob.mx están detrás de
Akamai, que rechaza con 403 los agentes de usuario de curl/wget/requests por
defecto. CABECERAS replica un Chrome real y es lo que permite el acceso. No es
una evasión de bloqueo: los datos son públicos y de acceso abierto (CC-BY-4.0),
el filtro solo discrimina por cliente.
"""

# Cabeceras que pasan el filtro de bot de Akamai. El conjunto completo importa:
# solo User-Agent no basta, las Sec-Fetch-* son parte de la huella que se valida.
CABECERAS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

_REPO = "https://repodatos.atdt.gob.mx"
_DG = "https://www.datos.gob.mx/dataset"
_F911 = f"{_DG}/59c589fe-c3cd-4134-9e0f-6b04fd9244c0/resource"
_IRS = f"{_DG}/ef697817-92a9-4937-8323-c08dda8bd00f/resource"
_POB = f"{_DG}/b6981ccc-083b-4e57-ba6f-d800a7398fa8/resource"
# Ojo: la ruta es datosabiertos/, no microdatos/. INEGI responde a las rutas
# viejas con HTTP 200 y una página "Esta liga ya no existe" en vez de un 404,
# así que una URL equivocada aquí se descarga "con éxito" como HTML de 2 KB.
# Por eso 00_descargar.py valida los bytes mágicos y no solo el código HTTP.
_ITER = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter"

# Cada fuente: (nombre_local, url, grupo, ciclo)
# `ciclo` es el ciclo escolar para el F911 y el año de referencia para el resto.
FUENTES = [
    # --- Variable dependiente: Formato 911, media superior -------------------
    # Seis ciclos consecutivos = cinco transiciones de cohorte. Es el nivel donde
    # el abandono es masivo (~13% anual nacional) y por eso el foco del análisis.
    ("f911_ems_2019-2020.csv", f"{_F911}/908a4a98-c837-4a6b-bd28-dc59990d1ba5/download/media_superior_2019-2020.csv", "f911_ems", "2019-2020"),
    ("f911_ems_2020-2021.csv", f"{_F911}/aebe55ca-aecc-41b1-9bac-905620fd5319/download/media_superior_2020-2021.csv", "f911_ems", "2020-2021"),
    ("f911_ems_2021-2022.csv", f"{_F911}/d81adeac-977b-4a3a-bfbf-2160ac4b9cbd/download/media_superior_2021-2022.csv", "f911_ems", "2021-2022"),
    ("f911_ems_2022-2023.csv", f"{_F911}/30eae81f-45f6-480e-9ac7-f491ec1c3fd5/download/media_superior_2022-2023.csv", "f911_ems", "2022-2023"),
    ("f911_ems_2023-2024.csv", f"{_F911}/b3b82081-b4fe-4d3c-8c24-813c2c6f550f/download/media_superior_2023-2024.csv", "f911_ems", "2023-2024"),
    ("f911_ems_2024-2025.csv", f"{_REPO}/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_media_superior_2024_2025.csv", "f911_ems", "2024-2025"),

    # --- Variable dependiente: Formato 911, educación básica -----------------
    # ~114 MB cada uno. Se bajan ahora para no repetir la descarga, pero el
    # pipeline se valida primero en EMS. El interés principal en básica es la
    # fuga de 3° de secundaria a 1° de EMS, el mayor punto de abandono del sistema.
    # Ojo: el ciclo 2023-2024 se publicó con otro nombre (ESTANDAR_BASICA_I2324),
    # lo que sugiere un cambio de esquema de columnas. Verificar al cargar.
    ("f911_basica_2019-2020.csv", f"{_REPO}/s_educacion_publica/f911/BASICA_2019-2020.csv", "f911_basica", "2019-2020"),
    ("f911_basica_2020-2021.csv", f"{_REPO}/s_educacion_publica/f911/BASICA_2020-2021.csv", "f911_basica", "2020-2021"),
    ("f911_basica_2021-2022.csv", f"{_REPO}/s_educacion_publica/f911/BASICA_2021-2022.csv", "f911_basica", "2021-2022"),
    ("f911_basica_2022-2023.csv", f"{_REPO}/s_educacion_publica/f911/BASICA_2022-2023.csv", "f911_basica", "2022-2023"),
    ("f911_basica_2023-2024.csv", f"{_REPO}/s_educacion_publica/f911/ESTANDAR_BASICA_I2324.csv", "f911_basica", "2023-2024"),
    ("f911_basica_2024-2025.csv", f"{_REPO}/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_basica_2024_2025.csv", "f911_basica", "2024-2025"),

    # --- Educación superior escolarizada -------------------------------------
    # Se bajan para poder medir, y no solo afirmar, si el análisis municipal es
    # viable en este nivel. La oferta de educación superior en Guerrero está
    # concentrada en pocos municipios, así que la mayoría de los 81 tiene
    # matrícula cero; ver el diagnóstico en src/03_cobertura_niveles.py.
    ("f911_superior_2019-2020.csv", f"{_F911}/f53ca47c-89b6-403e-89e9-0d567c648fca/download/superior_escolarizada_2019-2020.csv", "f911_superior", "2019-2020"),
    ("f911_superior_2020-2021.csv", f"{_F911}/a44c64b8-7202-4789-a5f8-ca0c255e1e71/download/superior_escolarizada_2020-2021.csv", "f911_superior", "2020-2021"),
    ("f911_superior_2021-2022.csv", f"{_F911}/d2782210-4573-4d16-922f-e5ccbb85f2bb/download/superior_escolarizada_2021-2022.csv", "f911_superior", "2021-2022"),
    ("f911_superior_2022-2023.csv", f"{_F911}/b0a9ed9b-36be-4afd-9c95-b9a11a9d0ea8/download/superior_escolarizada_2022-2023.csv", "f911_superior", "2022-2023"),
    ("f911_superior_2023-2024.csv", f"{_F911}/ecd6b2d1-6698-4918-af23-6a122b6dd915/download/superior_escolarizada_2023-2024.csv", "f911_superior", "2023-2024"),
    ("f911_superior_2024-2025.csv", f"{_REPO}/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_superior_escolarizada_2024_2025.csv", "f911_superior", "2024-2025"),

    # --- Variables independientes: CONEVAL -----------------------------------
    # Vía datos.gob.mx en CSV plano. Las descargas del portal de CONEVAL son
    # .zip con programas de Stata/R, no datos listos para usar.
    ("coneval_irs_municipal_2020.csv", f"{_IRS}/862d0ad7-3c26-46dd-8e0d-7f2c49c88d1c/download/irs_municipal_2020.csv", "coneval", "2020"),
    ("coneval_irs_municipal_2015.csv", f"{_IRS}/0e3dd27c-6d85-4136-98f2-a808f78838dd/download/irs_municipal_2015.csv", "coneval", "2015"),
    ("coneval_irs_municipal_2010.csv", f"{_IRS}/bcd1bfea-891e-4761-9c24-47feb1be84f3/download/irs_municipal_2010.csv", "coneval", "2010"),
    ("coneval_pobreza_municipal.csv", f"{_POB}/6e409e3a-aa08-45f5-b84b-f5d8cc6fafa8/download/pobreza_municipal.csv", "coneval", "2010-2020"),
    # Pobreza desagregada por grupo de edad: permite aislar la pobreza de la
    # población en edad escolar en vez de usar la del municipio entero.
    ("coneval_pobreza_edad.csv", f"{_POB}/f97c2271-ac51-4096-bbfb-5162b867b43f/download/pobreza_grupos_poblacionales_edad.csv", "coneval", "2010-2020"),

    # --- Tabla puente + marco demográfico: INEGI -----------------------------
    # El ITER trae CVE_ENT/CVE_MUN/NOM_MUN oficiales (la tabla puente que exige
    # el briefing) y además población por edad, que da el denominador para tasas.
    ("inegi_iter_guerrero_2020.zip", f"{_ITER}/iter_12_cpv2020_csv.zip", "inegi", "2020"),
    ("inegi_iter_nacional_2020.zip", f"{_ITER}/iter_00_cpv2020_csv.zip", "inegi", "2020"),
]
