"""Figuras del artículo, en PDF vectorial y PNG a 300 dpi.

Salidas en salidas/figuras/. Cada figura tiene un trabajo distinto:

  fig1_distancia_por_nivel   La asimetría que hace posible el diseño: la
                             primaria está en todas partes, el bachillerato no.
  fig2_efecto_distancia      El resultado: gráfico de residuales parciales tras
                             absorber efectos fijos de municipio.
  fig3_carrera_caballos      La identificación: solo pesa la distancia al nivel
                             que le toca a la edad.
  fig4_aporte_subsistemas    La implicación de política: matrícula y aporte al
                             acceso son cosas distintas.

Decisiones de diseño, para que se puedan repetir:
- Paleta validada con scripts/validate_palette.js del skill dataviz. Rampa
  ordinal de un solo tono para los niveles educativos (son ordinales, no
  categorías), y dos tonos categóricos para la carrera de caballos.
- Un solo eje por panel; nunca dos escalas verticales. Cuando hay dos medidas de
  escala distinta se usan paneles gemelos con el mismo orden de categorías.
- Etiquetas directas en vez de leyenda cuando hay pocas series, para que la
  figura se lea en escala de grises si la revista imprime sin color.
- Rejilla y ejes recesivos; el dato es lo único con peso visual.

Uso:
    .venv/bin/python src/08_figuras.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import statsmodels.api as sm

from carga import LIMPIO, RAIZ

FIGS = RAIZ / "salidas" / "figuras"

# Rampa ordinal de un tono (niveles educativos ascendentes).
AZUL_CLARO, AZUL, AZUL_OSCURO = "#86b6ef", "#2a78d6", "#104281"
# Categóricos para la carrera de caballos.
SERIE_1, SERIE_2 = "#2a78d6", "#eb6834"
TINTA, TINTA_2, TINTA_3 = "#0b0b0b", "#52514e", "#8a8984"
REJILLA = "#e6e5e1"


def estilo() -> None:
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 9,
        "axes.edgecolor": TINTA_3, "axes.linewidth": 0.6,
        "axes.labelcolor": TINTA_2, "axes.titlesize": 10,
        "axes.titleweight": "bold", "axes.titlecolor": TINTA,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "grid.color": REJILLA, "grid.linewidth": 0.6,
        "legend.frameon": False, "legend.fontsize": 8,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def guarda(fig, nombre: str) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{nombre}.{ext}")
    plt.close(fig)
    print(f"  {nombre}.pdf / .png")


def ecdf_ponderada(x, w):
    o = np.argsort(x)
    return np.asarray(x)[o], np.cumsum(np.asarray(w)[o]) / np.sum(w)


def fig1(loc: pd.DataFrame) -> None:
    """ECDF ponderada de la distancia a cada nivel."""
    fig, ax = plt.subplots(figsize=(5.4, 3.5))
    d = loc.dropna(subset=["pob_15a17"])
    d = d[d.pob_15a17 > 0]
    # El percentil de anclaje es distinto para cada serie a propósito: así las
    # tres etiquetas caen en coordenadas separadas y no se enciman.
    series = [("Primaria", "dist_prim", AZUL_CLARO, 99.0),
              ("Secundaria", "dist_sec", AZUL, 96.5),
              ("Bachillerato", "dist_ems", AZUL_OSCURO, 90.0)]
    for etq, col, color, ancla in series:
        x, y = ecdf_ponderada(d[col].values, d.pob_15a17.values)
        pct = 100 * y
        ax.step(x, pct, where="post", color=color, lw=2, solid_capstyle="round")
        # Etiqueta directa en tinta, no en el color de la serie: el azul claro
        # queda a 2:1 de contraste sobre blanco y se pierde al imprimir. La
        # identidad la carga la cercanía a la curva, no el color del texto.
        i = min(int(np.searchsorted(pct, ancla)), len(x) - 1)
        ax.annotate(etq, (x[i], pct[i]), xytext=(8, -9), textcoords="offset points",
                    color=TINTA, fontsize=8.5, fontweight="bold", va="center")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Distancia al plantel más cercano (km)")
    ax.set_ylabel("% acumulado de población de 15 a 17 años")
    ax.set_title("La oferta de bachillerato es la escasa")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.text(0.0, -0.06,
             "Distribución acumulada ponderada por población de 15 a 17 años residente en cada localidad.\n"
             "Guerrero, 6,769 localidades. Fuente: ITER Censo 2020 (INEGI) y Formato 911 2023-2024 (SEP).",
             fontsize=7, color=TINTA_2, ha="left")
    guarda(fig, "fig1_distancia_por_nivel")


def residualiza(y, X, w) -> np.ndarray:
    """Residuales de y sobre X por mínimos cuadrados ponderados.

    Devuelve un arreglo y no un Series: statsmodels hereda el índice del exog
    cuando es DataFrame, y un índice etiquetado rompe el indexado posicional
    que usa el resto de la figura.
    """
    m = sm.WLS(y, X, weights=w).fit()
    return np.asarray(m.resid)


def fig2(loc: pd.DataFrame) -> None:
    """Residuales parciales: brecha de asistencia vs distancia diferencial."""
    d = loc.dropna(subset=["brecha_15_12", "d_ems_sec", "pob_15a17", "pob_12a14"])
    d = d[(d.pob_15a17 > 0) & (d.pob_12a14 > 0)].reset_index(drop=True)
    w = (d.pob_15a17 + d.pob_12a14).values
    # Se residualiza contra el MISMO conjunto de controles que reporta el texto
    # (efectos fijos, tamaño de localidad y la otra distancia diferencial), para
    # que la pendiente del gráfico sea el β del artículo y no otro.
    ctrl = sm.add_constant(pd.concat(
        [d[["d_sec_prim", "log_pob"]],
         pd.get_dummies(d.cve_inegi, prefix="m", drop_first=True, dtype=float)],
        axis=1).fillna(0))
    ry = residualiza(d.brecha_15_12.values, ctrl, w)
    rx = residualiza(d.d_ems_sec.values, ctrl, w)

    # Binned scatter: 4,519 puntos individuales serían una nube ilegible; los
    # deciles ponderados muestran la forma de la relación sin ocultar dispersión.
    q = np.quantile(rx, np.linspace(0, 1, 21))
    q[-1] += 1e-9
    idx = np.clip(np.digitize(rx, q[1:-1]), 0, 19)
    bx = np.array([np.average(rx[idx == k], weights=w[idx == k]) for k in range(20)])
    by = np.array([np.average(ry[idx == k], weights=w[idx == k]) for k in range(20)])
    bw = np.array([w[idx == k].sum() for k in range(20)])

    fit = sm.WLS(ry, sm.add_constant(rx), weights=w).fit()
    # La recta se dibuja SOLO donde hay datos. Extenderla hasta los extremos de
    # la muestra la convierte en una extrapolación que exagera visualmente el
    # efecto: casi toda la masa está entre el percentil 1 y el 99.
    lo, hi = np.quantile(rx, [0.01, 0.99])
    xs = np.linspace(lo, hi, 100)
    pred = fit.get_prediction(sm.add_constant(xs)).summary_frame(alpha=0.05)

    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    ax.axhline(0, color=TINTA_3, lw=0.6, zorder=1)
    ax.fill_between(xs, pred["mean_ci_lower"], pred["mean_ci_upper"],
                    color=AZUL, alpha=0.14, lw=0, zorder=2)
    ax.plot(xs, pred["mean"], color=AZUL_OSCURO, lw=2, zorder=4)
    ax.scatter(bx, by, s=18 + 150 * bw / bw.max(), color=AZUL,
               edgecolor="white", linewidth=0.8, zorder=5)
    b, se = np.asarray(fit.params)[1], np.asarray(fit.bse)[1]
    ax.annotate(f"β = {b:.2f} pp por km\n(EE {se:.2f})",
                xy=(0.96, 0.92), xycoords="axes fraction", ha="right", va="top",
                fontsize=8.5, color=TINTA, fontweight="bold")
    margen_x = 0.06 * (hi - lo)
    ax.set_xlim(lo - margen_x, hi + margen_x)
    ry_vis = np.concatenate([by, pred["mean_ci_lower"], pred["mean_ci_upper"]])
    margen_y = 0.12 * (ry_vis.max() - ry_vis.min())
    ax.set_ylim(ry_vis.min() - margen_y, ry_vis.max() + margen_y)
    ax.set_xlabel("Distancia diferencial bachillerato − secundaria (km, residual)")
    ax.set_ylabel("Brecha de asistencia 15-17 − 12-14\n(puntos porcentuales, residual)")
    ax.set_title("A mayor distancia relativa al bachillerato, mayor caída de asistencia")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.text(0.0, -0.11,
             "Residuales tras absorber efectos fijos de municipio, tamaño de localidad y la distancia diferencial\n"
             "secundaria − primaria; ponderados por población de las dos cohortes. Puntos: veintiles de la distancia\n"
             "residual, con área proporcional a la población que representan. La recta se traza solo entre los\n"
             f"percentiles 1 y 99. n = {len(d):,} localidades en 81 municipios. Banda: intervalo de confianza al 95%.",
             fontsize=7, color=TINTA_2, ha="left")
    guarda(fig, "fig2_efecto_distancia")


def carrera_coefs(loc: pd.DataFrame) -> pd.DataFrame:
    filas = []
    especificaciones = (
        ("Brecha 15-17 vs 12-14\n(margen bachillerato)", "brecha_15_12",
         ("pob_15a17", "pob_12a14"), "d_ems_sec"),
        ("Brecha 12-14 vs 6-11\n(margen secundaria)", "brecha_12_6",
         ("pob_12a14", "pob_6a11"), "d_sec_prim"),
    )
    for etq, brecha, pobs, propia in especificaciones:
        d = loc.dropna(subset=[brecha, "d_ems_sec", "d_sec_prim", *pobs])
        d = d[(d[pobs[0]] > 0) & (d[pobs[1]] > 0)].reset_index(drop=True)
        fe = pd.get_dummies(d.cve_inegi, prefix="m", drop_first=True, dtype=float)
        X = sm.add_constant(pd.concat(
            [d[["d_ems_sec", "d_sec_prim", "log_pob"]], fe], axis=1).fillna(0))
        m = sm.WLS(d[brecha], X, weights=d[pobs[0]] + d[pobs[1]]).fit(
            cov_type="cluster", cov_kwds={"groups": d.cve_inegi})
        for var in ("d_ems_sec", "d_sec_prim"):
            ic = m.conf_int().loc[var]
            filas.append({"panel": etq, "var": var,
                          "rol": "Nivel que le toca a la edad" if var == propia
                                 else "El otro nivel",
                          "beta": m.params[var], "lo": ic[0], "hi": ic[1],
                          "p": m.pvalues[var]})
    return pd.DataFrame(filas)


def fig3(loc: pd.DataFrame) -> None:
    """Carrera de caballos: qué distancia manda en cada margen."""
    c = carrera_coefs(loc)
    paneles = c.panel.unique()
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.1), sharex=True)
    for ax, pan in zip(axes, paneles):
        s = c[c.panel == pan]
        # Orden fijo: el nivel propio arriba, el otro abajo, en los dos paneles.
        s = s.set_index("rol").loc[["Nivel que le toca a la edad", "El otro nivel"]]
        ys = [1, 0]
        for (rol, x), y, color in zip(s.iterrows(), ys, (SERIE_1, SERIE_2)):
            ax.plot([x.lo, x.hi], [y, y], color=color, lw=2.4,
                    solid_capstyle="round", zorder=3)
            ax.scatter([x.beta], [y], s=70, color=color, edgecolor="white",
                       linewidth=1.2, zorder=4)
            ax.annotate(f"{x.beta:+.2f}", (x.beta, y), xytext=(0, 11),
                        textcoords="offset points", ha="center",
                        fontsize=8.5, fontweight="bold", color=color)
        ax.axvline(0, color=TINTA_3, lw=0.8, ls=(0, (3, 3)), zorder=1)
        ax.set_yticks(ys)
        ax.set_yticklabels(s.index if ax is axes[0] else ["", ""], fontsize=8.5)
        ax.set_ylim(-0.6, 1.6)
        ax.set_title(pan, fontsize=9, fontweight="bold")
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    fig.supxlabel("Efecto sobre la brecha de asistencia (puntos porcentuales por km)",
                  fontsize=9, color=TINTA_2, y=-0.04)
    fig.suptitle("Solo importa la distancia a la escuela que corresponde a la edad",
                 fontsize=10, fontweight="bold", color=TINTA, y=1.16)
    fig.text(0.0, -0.20,
             "Las dos distancias diferenciales entran en la misma ecuación, con efectos fijos de municipio,\n"
             "control de tamaño de localidad y errores agrupados por municipio. Barras: intervalo al 95%.\n"
             "Si el efecto fuera del aislamiento general, las dos cargarían parecido en los dos paneles.",
             fontsize=7, color=TINTA_2, ha="left")
    guarda(fig, "fig3_carrera_caballos")


def fig4(sub: pd.DataFrame) -> None:
    """Matrícula y aporte al acceso: dos medidas, dos paneles, un solo eje cada uno."""
    s = sub.sort_values("aporte_km", ascending=True).copy()
    s["pct_matricula"] = 100 * s.alumnos / s.alumnos.sum()
    corto = {"Telebachillerato Comunitario": "Telebachillerato\nComunitario",
             "Media Superior a Distancia (EMSAD)": "Media Superior\na Distancia",
             "Preparatorias UAGro": "Preparatorias\nUAGro",
             "Colegio de Bachilleres": "Colegio de\nBachilleres",
             "CBTIS (bach. tecnológico industrial)": "CBTIS",
             "CBTA (bach. tecnológico agropecuario)": "CBTA",
             "Bachillerato privado": "Privado", "CONALEP": "CONALEP"}
    etiquetas = [corto.get(x, x) for x in s.subsistema]
    y = np.arange(len(s))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.9))
    for ax, col, titulo, unidad in (
        (axes[0], "pct_matricula", "Participación en la matrícula", "%"),
        (axes[1], "aporte_km", "Aporte al acceso", " km"),
    ):
        ax.barh(y, s[col], height=0.62, color=AZUL, zorder=3)
        for yy, v in zip(y, s[col]):
            ax.annotate(f"{v:.1f}{unidad}" if unidad == "%" else f"{v:.2f}{unidad}",
                        (v, yy), xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=7.5, color=TINTA_2)
        ax.set_yticks(y)
        ax.set_yticklabels(etiquetas if ax is axes[0] else [], fontsize=8)
        ax.set_title(titulo, fontsize=9, fontweight="bold")
        ax.set_xlim(0, s[col].max() * 1.26)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    axes[1].set_xlabel("km que subiría la distancia media\nsi el subsistema no existiera",
                       fontsize=8)
    axes[0].set_xlabel("% de la matrícula estatal de media superior", fontsize=8)
    fig.suptitle("El subsistema más pequeño es el que sostiene el acceso",
                 fontsize=10, fontweight="bold", color=TINTA, y=1.03)
    fig.text(0.0, -0.13,
             "Mismo orden de subsistemas en los dos paneles, ordenados por aporte al acceso. Escalas distintas,\n"
             "paneles separados: no es un gráfico de doble eje. El aporte se calcula recomputando la distancia de\n"
             "cada localidad al plantel más cercano excluyendo ese subsistema. Guerrero, ciclo 2023-2024.",
             fontsize=7, color=TINTA_2, ha="left")
    guarda(fig, "fig4_aporte_subsistemas")


def main() -> int:
    estilo()
    loc = pd.read_csv(LIMPIO / "localidades_cohortes.csv",
                      dtype={"cve_inegi": str, "cve_loc": str})
    sub = pd.read_csv(LIMPIO / "aporte_subsistemas.csv")
    print("Escribiendo figuras en salidas/figuras/ (PDF vectorial + PNG 300 dpi):")
    fig1(loc)
    fig2(loc)
    fig3(loc)
    fig4(sub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
