"""Figuras del modelo nacional, en PDF vectorial y PNG a 300 dpi.

Salidas en salidas/figuras/. Cada una sostiene una afirmación del artículo:

  fig5_validacion_estados   El modelo predice entidades que no vio. Es la
                            evidencia de que el método es replicable.
  fig6_focalizacion         Focalizar por tasa y por número dan listas
                            distintas; la figura muestra cuánto.
  fig7_que_pesa             Qué condiciones estructurales mandan.
  fig8_brecha               Restricción estructural contra margen de política.

Se conservan las decisiones de diseño de 08_figuras.py: un eje por panel,
etiquetas directas en lugar de leyenda, rejilla recesiva y la misma paleta, para
que las ocho figuras del artículo se lean como un solo sistema.

Uso:
    .venv/bin/python src/14_figuras_nacional.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from carga import LIMPIO, RAIZ

FIGS = RAIZ / "salidas" / "figuras"

AZUL_CLARO, AZUL, AZUL_OSCURO = "#86b6ef", "#2a78d6", "#104281"
SERIE_1, SERIE_2 = "#2a78d6", "#eb6834"
TINTA, TINTA_2, TINTA_3 = "#0b0b0b", "#52514e", "#8a8984"
REJILLA = "#e6e5e1"

mpl.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": TINTA_3, "axes.labelcolor": TINTA_2,
    "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlecolor": TINTA,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": REJILLA, "grid.linewidth": 0.7,
})


def guarda(fig, nombre: str) -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(FIGS / f"{nombre}.{ext}")
    plt.close(fig)
    print(f"  {nombre}")


def r2_pond(y, p, w) -> float:
    my = np.average(y, weights=w)
    return 1 - np.sum(w * (y - p) ** 2) / np.sum(w * (y - my) ** 2)


def fig_validacion(d: pd.DataFrame) -> None:
    """Desempeño por entidad apartada, que es la prueba de replicabilidad."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.6),
                                   gridspec_kw={"width_ratios": [1, 1.25]})

    # Panel izquierdo: observado contra predicho, cada punto un municipio.
    s = ax1.scatter(d.pred, d.inasistencia_15a17, s=np.sqrt(d.pob_15a17) / 7,
                    c=AZUL, alpha=0.22, linewidths=0)
    lim = [0, 90]
    ax1.plot(lim, lim, color=TINTA_3, lw=1, ls="--", zorder=1)
    ax1.set_xlim(lim); ax1.set_ylim(lim)
    ax1.set_xlabel("Inasistencia predicha (%)")
    ax1.set_ylabel("Inasistencia observada (%)")
    ax1.set_title("Cada municipio, predicho sin\nhaber visto su estado", loc="left")
    r2 = r2_pond(d.inasistencia_15a17.values, d.pred.values, d.pob_15a17.values)
    ax1.text(0.04, 0.95, f"$R^2$ = {r2:.3f}\nn = {len(d):,}", transform=ax1.transAxes,
             va="top", fontsize=9, color=TINTA)
    ax1.text(0.97, 0.06, "el área del punto es\nla población de 15-17",
             transform=ax1.transAxes, ha="right", fontsize=7.5, color=TINTA_3)
    ax1.grid(True, lw=0.7, alpha=0.6)

    # Panel derecho: por qué el R² se vuelve negativo en algunas entidades. No es
    # que el modelo falle ahí —el error absoluto es casi el mismo en todo el
    # país— sino que el R² compara contra la varianza interna, y en un estado
    # homogéneo esa varianza es casi nula y el cociente se dispara.
    por_ent = (d.groupby("nom_ent")
               .apply(lambda g: pd.Series({
                   "r2": r2_pond(g.inasistencia_15a17.values, g.pred.values,
                                 g.pob_15a17.values),
                   "de": np.sqrt(np.average(
                       (g.inasistencia_15a17 - np.average(g.inasistencia_15a17,
                                                          weights=g.pob_15a17)) ** 2,
                       weights=g.pob_15a17)),
                   "mae": np.average(np.abs(g.inasistencia_15a17 - g.pred),
                                     weights=g.pob_15a17),
                   "n": len(g)}), include_groups=False))

    col = [SERIE_2 if v < 0 else AZUL for v in por_ent.r2]
    ax2.scatter(por_ent.de, por_ent.r2, s=28 + np.sqrt(por_ent.n) * 9,
                c=col, alpha=0.75, linewidths=0)
    ax2.axhline(0, color=TINTA_3, lw=0.9, ls="--")
    ax2.set_xlabel("Dispersión de la inasistencia dentro de la entidad (p.p.)")
    ax2.set_ylabel("$R^2$ dentro de la entidad")
    ax2.set_title("El $R^2$ se hunde donde no hay nada\nque discriminar, no donde falla",
                  loc="left")
    ax2.grid(True, lw=0.7, alpha=0.6)
    for nom in ("Baja California Sur", "Sinaloa", "Oaxaca", "Chiapas", "México",
                "Ciudad de México"):
        if nom not in por_ent.index:
            continue
        r = por_ent.loc[nom]
        ax2.annotate(nom, xy=(r.de, r.r2), xytext=(r.de + 0.5, r.r2 + 0.06),
                     fontsize=7.5, color=TINTA_2)
    rho = por_ent.de.corr(por_ent.r2)
    mneg, mpos = por_ent[por_ent.r2 < 0].mae.mean(), por_ent[por_ent.r2 >= 0].mae.mean()
    ax2.text(0.97, 0.06,
             f"correlación dispersión–$R^2$: {rho:+.2f}\n"
             f"error absoluto medio: {mneg:.1f} p.p. en naranja,\n"
             f"{mpos:.1f} p.p. en azul — prácticamente igual",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=7.5,
             color=TINTA_2)
    ax2.text(0.03, 0.03, "el área del punto es\nel número de municipios",
             transform=ax2.transAxes, fontsize=7, color=TINTA_3)
    guarda(fig, "fig5_validacion_estados")


def fig_focalizacion(d: pd.DataFrame) -> None:
    """La tensión entre focalizar por tasa y por número de adolescentes."""
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    total = d.fuera.sum()
    n = len(d)
    eje = np.arange(1, n + 1) / n * 100

    for col, etq, color, ls in (
        ("fuera", "ordenando por número de adolescentes fuera", AZUL_OSCURO, "-"),
        ("pred", "ordenando por tasa predicha (el modelo)", AZUL, "-"),
        ("inasistencia_15a17", "ordenando por tasa observada", AZUL_CLARO, "-"),
    ):
        orden = d.sort_values(col, ascending=False)
        ax.plot(eje, np.cumsum(orden.fuera.values) / total * 100,
                color=color, lw=2, ls=ls, label=etq)
    ax.plot([0, 100], [0, 100], color=TINTA_3, lw=1, ls="--")

    ax.set_xlabel("Municipios seleccionados (% del total, ordenados de mayor a menor)")
    ax.set_ylabel("Adolescentes fuera de la escuela capturados (%)")
    ax.set_title("Focalizar por tasa o por número no es lo mismo", loc="left")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.grid(True, lw=0.7, alpha=0.6)

    for col, color, dy in (("fuera", AZUL_OSCURO, 0), ("pred", AZUL, -6),
                           ("inasistencia_15a17", AZUL_CLARO, -12)):
        orden = d.sort_values(col, ascending=False)
        y10 = np.cumsum(orden.fuera.values)[int(n * 0.1)] / total * 100
        ax.annotate(f"{y10:.0f}%", xy=(10, y10), xytext=(13, y10 + dy + 4),
                    color=color, fontsize=8.5, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.8))
    ax.axvline(10, color=TINTA_3, lw=0.8, ls=":")
    ax.text(10.6, 3, "decil", fontsize=7.5, color=TINTA_3)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.text(0.015, 0.97, "La diagonal es lo que capturaría una selección al azar.",
            transform=ax.transAxes, va="top", fontsize=7.5, color=TINTA_3)
    guarda(fig, "fig6_focalizacion")


def fig_que_pesa(coef: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    c = coef.head(12).iloc[::-1]
    col = [SERIE_2 if v < 0 else AZUL for v in c]
    ax.barh(range(len(c)), c.values, color=col, height=0.72)
    ax.set_yticks(range(len(c)))
    ax.set_yticklabels([k.replace("_", " ") for k in c.index], fontsize=8)
    ax.axvline(0, color=TINTA_3, lw=0.9)
    ax.set_xlabel("Puntos de inasistencia por desviación estándar de la variable")
    ax.set_title("Qué condiciones del territorio pesan más", loc="left")
    ax.grid(True, axis="x", lw=0.7, alpha=0.6)
    ax.text(0.98, 0.04,
            "Coeficientes de un modelo predictivo:\nindican asociación, no efecto causal.",
            transform=ax.transAxes, ha="right", fontsize=7.5, color=TINTA_2)
    guarda(fig, "fig7_que_pesa")


def fig_brecha(d: pd.DataFrame) -> None:
    """Restricción estructural contra margen de política."""
    fi = d[d.pob_15a17 >= 200]
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    ax.scatter(fi.pred, fi.inasistencia_15a17, s=np.sqrt(fi.pob_15a17) / 6,
               c=AZUL, alpha=0.2, linewidths=0)
    lim = [0, 90]
    ax.plot(lim, lim, color=TINTA_3, lw=1.1, ls="--")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Inasistencia predicha por las condiciones estructurales (%)")
    ax.set_ylabel("Inasistencia observada (%)")
    ax.set_title("Dónde hay margen de política y dónde restricción estructural",
                 loc="left")
    ax.grid(True, lw=0.7, alpha=0.6)

    for nom, dx, dy, color in (
        ("Chamula", 6, -9, SERIE_2), ("Zinacantán", 8, -4, SERIE_2),
        ("Riva Palacio", -14, 9, SERIE_2),
        ("Malinaltepec", 7, -11, AZUL_OSCURO), ("Iliatenco", 5, -9, AZUL_OSCURO),
    ):
        r = fi[fi.nom_mun == nom]
        if not len(r):
            continue
        r = r.iloc[0]
        ax.scatter([r.pred], [r.inasistencia_15a17], s=46, facecolor="none",
                   edgecolor=color, lw=1.5, zorder=5)
        ax.annotate(nom, xy=(r.pred, r.inasistencia_15a17),
                    xytext=(r.pred + dx, r.inasistencia_15a17 + dy),
                    fontsize=8, color=color, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.8))
    ax.text(0.035, 0.95, "peor de lo esperado:\nmargen de política",
            transform=ax.transAxes, va="top", fontsize=8, color=SERIE_2)
    ax.text(0.62, 0.17, "mejor de lo esperado:\ncasos de los que aprender",
            transform=ax.transAxes, va="top", fontsize=8, color=AZUL_OSCURO)
    ax.text(0.98, 0.02, "solo municipios con 200 o más adolescentes de 15-17",
            transform=ax.transAxes, ha="right", fontsize=7.5, color=TINTA_3)
    guarda(fig, "fig8_brecha")


def main() -> int:
    d = pd.read_csv(LIMPIO / "riesgo_municipal.csv",
                    dtype={"cve_inegi": str, "cve_ent": str})
    d = d.dropna(subset=["pred", "inasistencia_15a17", "pob_15a17"])

    print("Figuras del modelo nacional:")
    fig_validacion(d)
    fig_focalizacion(d)

    # Los coeficientes se recalculan aquí para que la figura no dependa de que
    # 13_modelo_riesgo.py los haya dejado escritos en algún lado.
    import importlib, sys
    sys.path.insert(0, str(RAIZ / "src"))
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    mod = importlib.import_module("13_modelo_riesgo")
    base = pd.read_csv(LIMPIO / "nacional_municipios.csv",
                       dtype={"cve_inegi": str, "cve_ent": str})
    base["log_pob"] = np.log(base.pob_total.clip(lower=1))
    base = base.dropna(subset=[mod.OBJETIVO, "pob_15a17"])
    base = base[base.pob_15a17 > 0]
    base[mod.ESTRUCTURAL] = base[mod.ESTRUCTURAL].fillna(base[mod.ESTRUCTURAL].median())
    m = make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-2, 3, 20)))
    m.fit(base[mod.ESTRUCTURAL], base[mod.OBJETIVO])
    coef = pd.Series(m[-1].coef_, index=mod.ESTRUCTURAL).sort_values(key=abs,
                                                                    ascending=False)
    fig_que_pesa(coef)
    fig_brecha(d)
    print(f"\nEscritas en {FIGS.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
