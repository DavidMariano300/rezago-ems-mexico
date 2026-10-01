"""Cruza el abandono municipal con rezago social, pobreza y contexto censal.

Salidas:
  datos/limpio/panel_completo.csv    405 filas (81 municipios × 5 transiciones)
  datos/limpio/corte_municipal.csv    81 filas, promedios sin ciclos COVID

EL PROBLEMA DE IDENTIFICACIÓN QUE ESTE CRUCE HACE EXPLÍCITO

La hipótesis del briefing es que la pobreza y el rezago en infraestructura
elevan el abandono. Pero las dos mitades de esa hipótesis viven en regímenes
estadísticos distintos:

  - La infraestructura escolar (alumnos por docente, por grupo, planteles)
    cambia cada ciclo. Se identifica con efectos fijos de municipio.
  - El rezago social y la pobreza vienen de CONEVAL en cortes quinquenales
    (2010, 2015, 2020) y del Censo 2020. Dentro de la ventana 2019-2024 son
    constantes. Un efecto fijo de municipio las absorbe por completo y su
    coeficiente queda sin identificar — el modelo no da error, simplemente las
    elimina o devuelve un coeficiente sin sentido.

No es un defecto de los datos, es la naturaleza del problema: no se puede
estimar el efecto de algo que no varía usando un estimador que solo usa
variación interna. Hay tres salidas, y el cruce prepara las tres:

  (1) CORTE TRANSVERSAL — promediar el abandono por municipio y regresar contra
      contexto. Identifica el efecto del rezago, pero sin controlar lo no
      observado: es correlación descriptiva, no causal. Va en el artículo como
      caracterización, con ese nombre.

  (2) EFECTOS FIJOS sobre lo que sí varía — estima el efecto de la
      infraestructura limpio de todo lo municipal invariante (geografía,
      cultura, marginación estructural, y también el sesgo de movilidad
      intermunicipal si es estable). Es la parte con pretensión causal.

  (3) INTERACCIONES con el choque COVID — ESTA ES LA MÁS FUERTE Y LA MENOS
      OBVIA. Bajo efectos fijos no se puede estimar el efecto de `pct_hli` ni de
      `irs`, pero SÍ se puede estimar `irs × COVID`: si el cierre de escuelas
      golpeó más fuerte a los municipios con mayor rezago, eso es variación
      temporal diferenciada por una característica fija, y los efectos fijos no
      la absorben. Convierte la limitación en el resultado principal: no "los
      municipios pobres tienen más abandono" (que ya se sabe) sino "el choque
      recayó desproporcionadamente sobre los municipios pobres", que es una
      afirmación causal defendible y de interés para política pública.

Uso:
    .venv/bin/python src/03_cruce.py
"""

from __future__ import annotations

import pandas as pd

from carga import LIMPIO, RAIZ, coneval, guerrero, iter_contexto
from municipios import N_MUNICIPIOS_HISTORICO, a_panel

ANIO_CONEVAL = "2020-01-01"
GRUPO_NNA = "Niñas, niños y adolescentes (0 a 17 años)"

# Indicadores del IRS que se conservan. Se excluyen deliberadamente `i_analf`,
# `i_asistesc` y `i_edbasinc`: son indicadores EDUCATIVOS construidos con el
# mismo censo, así que meterlos como predictores del abandono escolar es
# circular. Se guardan aparte, con ese nombre, para contrastar y no para modelar.
IRS_ESTRUCTURAL = ["i_sdsalud", "i_ptierra", "i_nosan", "i_noagua", "i_nodren",
                   "i_noelec", "i_nolav", "i_noref"]
IRS_EDUCATIVO = ["i_analf", "i_asistesc", "i_edbasinc"]


def rezago_social() -> pd.DataFrame:
    d = guerrero(coneval("coneval_irs_municipal_2020.csv"))
    cols = ["cve_inegi", "irs", "grs", "lugar"] + IRS_ESTRUCTURAL + IRS_EDUCATIVO
    return d[cols].rename(columns={
        "irs": "indice_rezago_social", "grs": "grado_rezago_social",
        "lugar": "lugar_nacional_rezago",
    })


def pobreza() -> pd.DataFrame:
    d = guerrero(coneval("coneval_pobreza_municipal.csv"))
    d = d[d.periodo == ANIO_CONEVAL]
    cols = {
        "pobreza_porcentaje": "pct_pobreza",
        "pobreza_extrema_porcentaje": "pct_pobreza_extrema",
        "carencia_rezago_educativo_porcentaje": "pct_carencia_rezago_educativo",
        "carencia_servicios_basicos_vivienda_porcentaje": "pct_carencia_serv_vivienda",
        "carencia_alimentacion_nutritiva_calidad_porcentaje": "pct_carencia_alimentacion",
        "ingreso_inferior_a_lpi_porcentaje": "pct_ingreso_bajo_lpi",
    }
    return d[["cve_inegi"] + list(cols)].rename(columns=cols)


def pobreza_infantil() -> pd.DataFrame:
    """Pobreza del grupo de 0 a 17 años.

    Más pertinente que la pobreza del municipio entero: la decisión de dejar el
    bachillerato la toma un hogar con adolescentes, no el municipio promedio.
    """
    d = guerrero(coneval("coneval_pobreza_edad.csv"))
    d = d[(d.periodo == ANIO_CONEVAL) & (d.grupo == GRUPO_NNA)]
    cols = {
        "pobreza_porcentaje": "pct_pobreza_nna",
        "carencia_rezago_educativo_porcentaje": "pct_carencia_educativa_nna",
        "carencia_alimentacion_nutritiva_calidad_porcentaje": "pct_carencia_alim_nna",
    }
    return d[["cve_inegi"] + list(cols)].rename(columns=cols)


def oferta_superior() -> pd.DataFrame:
    """Matrícula de educación superior por municipio, ciclo 2023-2024.

    No es un control más: es una hipótesis. Si en tu municipio hay a dónde
    seguir estudiando, terminar el bachillerato tiene un retorno visible. Donde
    la universidad más cercana está a tres horas, el tercer año de bachillerato
    es un callejón sin salida. Solo 29 de los 81 municipios tienen oferta, así
    que entra como indicador binario más el logaritmo de la matrícula.
    """
    d = pd.read_csv(RAIZ / "datos" / "crudo" / "f911_superior_2023-2024.csv",
                    dtype=str, low_memory=False)
    d.columns = [c.strip().lower() for c in d.columns]
    d = d[d.cve_entidad.astype(str).str.strip().str.lstrip("0") == "12"].copy()
    d["cve_inegi"] = "12" + d.cve_municipio.astype(str).str.strip().str.zfill(3)
    matr = [c for c in d.columns if c.startswith("alumnos_")]
    for c in matr:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["alumnos_superior"] = d[matr].sum(axis=1)
    g = d.groupby("cve_inegi", as_index=False)["alumnos_superior"].sum()
    g["cve_inegi"] = a_panel(g["cve_inegi"])
    g = g.groupby("cve_inegi", as_index=False)["alumnos_superior"].sum()
    g["tiene_superior"] = (g.alumnos_superior > 0).astype(int)
    return g


def main() -> int:
    panel = pd.read_csv(LIMPIO / "panel_abandono_ems.csv", dtype={"cve_inegi": str})

    piezas = [rezago_social(), pobreza(), pobreza_infantil(),
              iter_contexto(), oferta_superior()]
    ctx = piezas[0]
    for p in piezas[1:]:
        ctx = ctx.merge(p, on="cve_inegi", how="outer")

    # La oferta de superior solo existe en 29 municipios; el resto es cero real,
    # no dato faltante, así que se rellena explícitamente.
    ctx["alumnos_superior"] = ctx["alumnos_superior"].fillna(0)
    ctx["tiene_superior"] = ctx["tiene_superior"].fillna(0).astype(int)

    print(f"Contexto municipal: {len(ctx)} municipios, {len(ctx.columns)-1} variables")
    if len(ctx) != N_MUNICIPIOS_HISTORICO:
        print(f"  AVISO: se esperaban {N_MUNICIPIOS_HISTORICO} municipios")

    antes = len(panel)
    completo = panel.merge(ctx, on="cve_inegi", how="left",
                           suffixes=("", "_ctx"), validate="many_to_one")
    dup = [c for c in completo.columns if c.endswith("_ctx")]
    completo = completo.drop(columns=dup)  # grado_prom_escolaridad ya venía del puente

    print(f"Panel completo: {len(completo)} filas (antes {antes}), "
          f"{len(completo.columns)} columnas")
    sin_ctx = completo.indice_rezago_social.isna().sum()
    if sin_ctx:
        print(f"  PROBLEMA: {sin_ctx} filas sin contexto tras el cruce")
        return 1

    # --- Diagnóstico de identificación: cuánto varía cada cosa en el tiempo ---
    print("\n=== Variación temporal INTERNA de cada variable ===")
    print("(share within = fracción de la varianza total que ocurre dentro del")
    print(" municipio a lo largo del tiempo. Cerca de 0 = los efectos fijos la")
    print(" absorben y su efecto NO se puede estimar con efectos fijos.)\n")
    print(f"  {'variable':34s} {'share within':>13s}")
    cands = ["abandono", "alumnos_por_docente", "alumnos_por_grupo", "pct_privado",
             "planteles", "cobertura_15a17", "indice_rezago_social", "pct_pobreza",
             "pct_pobreza_nna", "pct_hli", "pct_viv_con_internet", "tasa_desocupacion"]
    for c in cands:
        s = completo[c].astype(float)
        if s.notna().sum() < 10 or s.var() in (0, None) or pd.isna(s.var()):
            continue
        within = completo.groupby("cve_inegi")[c].transform(lambda x: x - x.mean())
        share = within.var() / s.var()
        marca = "  <- invariante" if share < 0.01 else ""
        print(f"  {c:34s} {share:>12.3f}{marca}")

    completo.to_csv(LIMPIO / "panel_completo.csv", index=False, encoding="utf-8")

    # --- Corte transversal: un renglón por municipio, sin ciclos COVID ---
    sin_covid = completo[~completo.covid]
    variables_panel = ["abandono", "abandono_g01", "abandono_g2", "abandono_g3",
                       "alumnos", "alumnos_por_docente", "alumnos_por_grupo",
                       "pct_privado", "planteles", "cobertura_15a17"]
    corte = sin_covid.groupby("cve_inegi", as_index=False)[variables_panel].mean()
    # El abandono durante COVID se guarda aparte: es el insumo del contraste (3).
    covid = (completo[completo.covid].groupby("cve_inegi", as_index=False)["abandono"]
             .mean().rename(columns={"abandono": "abandono_covid"}))
    corte = corte.merge(covid, on="cve_inegi").merge(
        completo[["cve_inegi", "nom_mun"]].drop_duplicates(), on="cve_inegi").merge(
        ctx, on="cve_inegi")
    corte["brecha_covid"] = corte.abandono_covid - corte.abandono
    corte.to_csv(LIMPIO / "corte_municipal.csv", index=False, encoding="utf-8")

    print("\n=== Correlaciones con el abandono promedio (corte, sin COVID, n=81) ===")
    print("Descriptivas, no causales: ninguna controla por lo no observado.\n")
    objetivo = ["indice_rezago_social", "pct_pobreza", "pct_pobreza_nna",
                "pct_carencia_educativa_nna", "pct_hli", "pct_viv_con_internet",
                "pct_viv_piso_tierra", "tasa_desocupacion", "grado_prom_escolaridad",
                "asistencia_15a17", "alumnos_por_docente", "alumnos_por_grupo",
                "pct_privado", "tiene_superior", "cobertura_15a17"]
    corr = (corte[objetivo + ["abandono"]].astype(float).corr(method="spearman")
            ["abandono"].drop("abandono").sort_values(key=abs, ascending=False))
    for k, v in corr.items():
        barra = "█" * int(abs(v) * 30)
        print(f"  {k:31s} {v:>+7.3f}  {barra}")

    print("\n=== La brecha COVID: ¿el choque fue peor donde hay más rezago? ===")
    print("(correlación de la brecha COVID con el contexto; esto es lo que SÍ")
    print(" queda identificado bajo efectos fijos)\n")
    cb = (corte[["brecha_covid", "indice_rezago_social", "pct_pobreza_nna",
                 "pct_hli", "pct_viv_con_internet", "alumnos_por_docente"]]
          .astype(float).corr(method="spearman")["brecha_covid"]
          .drop("brecha_covid").sort_values(key=abs, ascending=False))
    for k, v in cb.items():
        print(f"  {k:31s} {v:>+7.3f}")

    print(f"\nEscritos:")
    print(f"  {(LIMPIO/'panel_completo.csv').relative_to(RAIZ)}  "
          f"({len(completo)} filas, {len(completo.columns)} col)")
    print(f"  {(LIMPIO/'corte_municipal.csv').relative_to(RAIZ)}  "
          f"({len(corte)} filas, {len(corte.columns)} col)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
