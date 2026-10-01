"""Variable dependiente alterna: asistencia escolar censal, y cuánto sesga la movilidad.

Salida: datos/limpio/corte_validacion.csv — 81 municipios con las dos medidas y
el índice de importación de matrícula.

DOS MEDIDAS DEL MISMO FENÓMENO, CON SESGOS OPUESTOS

    cobertura_15a17   = matrícula del F911 / población 15-17 del Censo
                        el numerador se cuenta donde está LA ESCUELA
    asistencia_15a17  = 15-17 que asisten / población 15-17, ambos del Censo
                        el numerador se cuenta donde está LA CASA

Ninguna es perfecta, pero fallan en direcciones contrarias, y ahí está su valor:
la discrepancia entre las dos MIDE el flujo de estudiantes entre municipios, que
hasta ahora solo podíamos declarar como limitación sin cuantificar.

    indice_importacion = cobertura_15a17 / asistencia_15a17

    > 1  el municipio atiende a más adolescentes de los que residen en él
         estudiando: recibe alumnos de fuera (Acapulco, Chilpancingo)
    < 1  sus residentes estudian en otra parte: municipio emisor

Para un municipio emisor, el abandono calculado con el F911 está inflado: los
alumnos que se van a estudiar a la cabecera vecina desaparecen de su matrícula y
el cálculo los cuenta como desertores. El índice permite, por primera vez en
este proyecto, acotar ese sesgo municipio por municipio en vez de invocarlo.

LIMITACIÓN: la asistencia censal es de corte (Censo 2020, único punto en la
ventana), así que sirve para el análisis transversal y para validar, no para el
panel. El panel sigue dependiendo del F911.

ADVERTENCIA DE INTERPRETACIÓN: asistencia y abandono no son complementarios.
Asistir es un estado en un momento (el día del censo); abandonar es un flujo a lo
largo de un ciclo. Un municipio puede tener alta asistencia y alto abandono si
muchos entran y muchos se van. Se espera correlación negativa, no que sumen 100.

Uso:
    .venv/bin/python src/05_asistencia_censal.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from carga import LIMPIO, RAIZ

# Umbrales para clasificar; 15% de holgura evita leer como flujo real lo que es
# ruido de dos fuentes con fechas de referencia distintas.
UMBRAL_IMPORTADOR = 1.15
UMBRAL_EMISOR = 0.85


def wcorr(x, y, w) -> float:
    x, y, w = np.asarray(x, float), np.asarray(y, float), np.asarray(w, float)
    ok = ~(np.isnan(x) | np.isnan(y) | np.isnan(w))
    x, y, w = x[ok], y[ok], w[ok]
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return cov / np.sqrt(np.average((x - mx) ** 2, weights=w)
                         * np.average((y - my) ** 2, weights=w))


def main() -> int:
    c = pd.read_csv(LIMPIO / "corte_municipal.csv", dtype={"cve_inegi": str})
    dist = pd.read_csv(LIMPIO / "distancia_municipal.csv", dtype={"cve_inegi": str})
    c = c.merge(dist, on="cve_inegi", how="left")

    c["indice_importacion"] = c.cobertura_15a17 / c.asistencia_15a17
    c["flujo"] = np.select(
        [c.indice_importacion > UMBRAL_IMPORTADOR, c.indice_importacion < UMBRAL_EMISOR],
        ["importador", "emisor"], default="equilibrado")

    print("=== Las dos medidas (n=81 municipios) ===")
    for v, etq in (("cobertura_15a17", "cobertura F911 (por escuela)"),
                   ("asistencia_15a17", "asistencia censal (por casa)")):
        s = c[v]
        print(f"  {etq:32s} media={s.mean():>6.2f}%  mediana={s.median():>6.2f}%  "
              f"min={s.min():>6.1f}%  max={s.max():>6.1f}%")
    r = c.cobertura_15a17.corr(c.asistencia_15a17, method="spearman")
    print(f"\n  correlación entre ambas (Spearman): {r:+.3f}")
    if r < 0.5:
        print("  Correlación baja: confirma que NO miden lo mismo y que el flujo")
        print("  intermunicipal es sustancial, no un detalle.")

    print(f"\n=== Flujo intermunicipal de estudiantes ===")
    print(c.flujo.value_counts().to_string())

    print(f"\n  Mayores IMPORTADORES (reciben alumnos de fuera):")
    top = c.nlargest(6, "indice_importacion")[
        ["nom_mun", "indice_importacion", "cobertura_15a17", "asistencia_15a17",
         "abandono", "alumnos"]]
    print(top.to_string(index=False, float_format=lambda x: f"{x:>8.2f}"))

    print(f"\n  Mayores EMISORES (sus residentes estudian fuera):")
    bot = c.nsmallest(6, "indice_importacion")[
        ["nom_mun", "indice_importacion", "cobertura_15a17", "asistencia_15a17",
         "abandono", "alumnos"]]
    print(bot.to_string(index=False, float_format=lambda x: f"{x:>8.2f}"))

    print(f"\n=== ¿El sesgo de movilidad infla el abandono de los emisores? ===")
    print("Si la hipótesis es correcta, los emisores deben mostrar MÁS abandono")
    print("medido con el F911, sin que ello signifique más deserción real.\n")
    print(f"  {'grupo':14s} {'n':>3s} {'abandono medio':>15s} {'abandono pond.':>15s}")
    for gr in ("emisor", "equilibrado", "importador"):
        s = c[c.flujo == gr]
        if not len(s):
            continue
        pond = np.average(s.abandono, weights=s.alumnos)
        print(f"  {gr:14s} {len(s):>3} {s.abandono.mean():>14.2f}% {pond:>14.2f}%")
    rho = c.indice_importacion.corr(c.abandono, method="spearman")
    print(f"\n  correlación índice de importación vs abandono: {rho:+.3f}")
    print(f"  (negativa = los emisores tienen más abandono medido, como predice el sesgo)")

    print(f"\n=== Correlaciones con la ASISTENCIA CENSAL (VD alterna) ===")
    print("Signo esperado inverso al del abandono: más contexto adverso, menos asistencia.\n")
    vs = ["indice_rezago_social", "pct_pobreza_nna", "pct_hli", "grado_prom_escolaridad",
          "pct_viv_con_internet", "tasa_desocupacion", "alumnos_por_docente",
          "dist_media_pond", "pct_15a17_mas_10km", "tiene_superior"]
    print(f"  {'variable':26s} {'vs asistencia':>14s} {'vs abandono':>13s} {'|razón|':>9s}")
    for v in vs:
        ra = c[v].corr(c.asistencia_15a17, method="spearman")
        rb = c[v].corr(c.abandono, method="spearman")
        razon = abs(ra) / abs(rb) if abs(rb) > 1e-9 else float("inf")
        print(f"  {v:26s} {ra:>+14.3f} {rb:>+13.3f} {razon:>9.1f}")
    print("\n  La columna |razón| es cuántas veces más fuerte es la correlación con")
    print("  la asistencia censal que con el abandono del F911. Valores muy altos")
    print("  indican que el abandono del F911 está dominado por ruido de medición,")
    print("  no que la variable sea irrelevante.")

    print(f"\n=== Ponderado por población de 15-17 (asistencia censal) ===")
    for v in ["indice_rezago_social", "pct_pobreza_nna", "pct_hli",
              "grado_prom_escolaridad", "dist_media_pond", "pct_15a17_mas_10km"]:
        print(f"  {v:26s} {wcorr(c[v], c.asistencia_15a17, c.pob_15a17_loc):>+8.3f}")

    c.to_csv(LIMPIO / "corte_validacion.csv", index=False, encoding="utf-8")
    print(f"\nEscrito: {(LIMPIO/'corte_validacion.csv').relative_to(RAIZ)}  "
          f"({len(c)} filas, {len(c.columns)} columnas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
