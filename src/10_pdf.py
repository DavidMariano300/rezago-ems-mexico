"""Convierte el manuscrito en Markdown a un PDF con formato APA 7ª edición.

Salida: salidas/Articulo_APA7.pdf

Formato aplicado: Times New Roman 12 pt, interlineado doble en todo el documento
(texto, tablas, figuras y referencias), márgenes de 2.54 cm, encabezado en
mayúsculas a la izquierda y número de página a la derecha desde la portada,
sangría de primera línea de 1.27 cm salvo en resumen, notas y referencias, y
sangría francesa en la lista de referencias.

Se escribe LaTeX directamente porque pandoc no está disponible en el entorno y
porque el control fino del formato es justo lo que exige la norma.

DIRECTIVAS DE BLOQUE

El Markdown admite tres bloques delimitados por `:::` que el conversor traduce a
los elementos que APA formatea de manera particular:

    ::: portada
    titulo: ...
    autor: ...
    :::

    ::: tabla 1
    titulo: Título en cursiva
    nota: Texto de la nota al pie
    | encabezado | encabezado |
    |---|---|
    | celda | celda |
    :::

    ::: figura 1
    archivo: nombre.png
    titulo: Título en cursiva
    nota: Texto de la nota al pie
    :::

Existen porque la norma numera, titula y anota tablas y figuras de una forma que
no tiene equivalente en Markdown, y deducirla del contexto resultaba frágil.

Uso:
    .venv/bin/python src/10_pdf.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "docs" / "ARTICULO.md"
FIGS = RAIZ / "salidas" / "figuras"
SALIDA = RAIZ / "salidas" / "Articulo_APA7.pdf"

ENCABEZADO = "REZAGO EN EDUCACIÓN MEDIA SUPERIOR"

PREAMBULO = r"""\documentclass[12pt,letterpaper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[spanish,mexico]{babel}
\usepackage{mathptmx}                      % Times New Roman
\usepackage{amsmath}
\usepackage[margin=2.54cm]{geometry}
\usepackage{setspace}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\newcolumntype{D}{>{\raggedleft\arraybackslash}X}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage[hidelinks,breaklinks=true]{hyperref}
% Las URLs se parten solo en separadores naturales. Con xurl se partían en
% cualquier carácter y «coneval.org» quedaba como «coneval.or / g», lo que al
% copiar el PDF producía una URL aparentemente rota.
\usepackage{url}
\def\UrlBreaks{\do\/\do\-\do\.\do\_\do\?\do\&\do\=\do\+\do\:}
\Urlmuskip=0mu plus 3mu\relax
\usepackage{enumitem}

\doublespacing
\setlength{\parindent}{1.27cm}
\setlength{\parskip}{0pt}

% Encabezado: texto en mayúsculas a la izquierda, número de página a la derecha.
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\normalsize ENCABEZADO_CORTO}
\fancyhead[R]{\normalsize\thepage}
\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{portada}{%
  \fancyhf{}
  \fancyhead[L]{\normalsize Running head: ENCABEZADO_CORTO}
  \fancyhead[R]{\normalsize\thepage}
  \renewcommand{\headrulewidth}{0pt}}

% Jerarquía de encabezados de la norma: nivel 1 centrado en negrita, nivel 2 a la
% izquierda en negrita, nivel 3 a la izquierda en negrita cursiva.
\titleformat{\section}{\normalfont\bfseries\centering}{}{0pt}{}
\titleformat{\subsection}{\normalfont\bfseries\raggedright}{}{0pt}{}
\titleformat{\subsubsection}{\normalfont\bfseries\itshape\raggedright}{}{0pt}{}
\titlespacing*{\section}{0pt}{0.5\baselineskip}{0pt}
\titlespacing*{\subsection}{0pt}{0.5\baselineskip}{0pt}
\titlespacing*{\subsubsection}{0pt}{0.5\baselineskip}{0pt}

\newenvironment{referencias}
  {\setlength{\parindent}{-1.27cm}\setlength{\leftskip}{1.27cm}}
  {}

% Resumen, abstract y notas van en bloque, sin sangría de primera línea.
\newenvironment{bloque}
  {\par\setlength{\parindent}{0pt}}
  {\par}

\setlist[enumerate]{leftmargin=1.27cm,labelsep=0.4em,itemsep=0pt,parsep=0pt,
                    topsep=0pt}
\setlist[itemize]{leftmargin=1.27cm,itemsep=0pt,parsep=0pt,topsep=0pt}

\begin{document}
""".replace("ENCABEZADO_CORTO", ENCABEZADO)

ESCAPES = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_"}

# Unicode que inputenc no reconoce. El signo menos tipográfico es el más
# frecuente porque casi todos los coeficientes del artículo son negativos.
UNICODE = {
    "−": r"$-$", "±": r"$\pm$", "×": r"$\times$", "÷": r"$\div$",
    "≤": r"$\leq$", "≥": r"$\geq$", "≈": r"$\approx$", "≠": r"$\neq$",
    "→": r"$\rightarrow$", "←": r"$\leftarrow$",
    "β": r"$\beta$", "α": r"$\alpha$", "γ": r"$\gamma$", "δ": r"$\delta$",
    "ε": r"$\varepsilon$", "σ": r"$\sigma$", "μ": r"$\mu$", "ρ": r"$\rho$",
    "λ": r"$\lambda$", "Δ": r"$\Delta$", "Σ": r"$\Sigma$", "χ": r"$\chi$",
    "²": r"\textsuperscript{2}", "³": r"\textsuperscript{3}",
    "⁻": r"\textsuperscript{$-$}", "⁰": r"\textsuperscript{0}",
    "¹": r"\textsuperscript{1}", "⁴": r"\textsuperscript{4}",
    "…": r"\ldots{}", "“": "``", "”": "''", "‘": "`", "’": "'",
    # Espacios especiales escritos con escape explícito. Una versión anterior
    # tenía aquí un espacio normal (U+0020) tecleado por error, lo que convertía
    # TODOS los espacios del documento en espacios finos irrompibles y producía
    # párrafos de una sola palabra kilométrica.
    " ": "~",      # espacio duro
    " ": r"\,",    # espacio fino
    " ": r"\,",    # espacio fino duro
}

assert " " not in UNICODE, "el espacio normal nunca debe mapearse"


def escapa(t: str) -> str:
    for a, b in ESCAPES.items():
        t = t.replace(a, b)
    for a, b in UNICODE.items():
        t = t.replace(a, b)
    return t


def en_linea(t: str) -> str:
    marcadores: list[str] = []

    def guarda(s: str) -> str:
        marcadores.append(s)
        return f"\x00{len(marcadores)-1}\x00"

    t = re.sub(r"\$([^$]+)\$", lambda m: guarda("$" + m.group(1) + "$"), t)
    t = re.sub(r"`([^`]+)`", lambda m: guarda(r"\texttt{" + escapa(m.group(1)) + "}"), t)
    t = re.sub(r"\[([^\]]+)\]\((?:[^)]+)\)", r"\1", t)
    t = re.sub(r"(https?://[^\s,)]+)", lambda m: guarda(r"\url{" + m.group(1) + "}"), t)
    t = escapa(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", t)
    t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\textit{\1}", t)
    t = t.replace("—", "---").replace("–", "--")
    t = re.sub(r"\x00(\d+)\x00", lambda m: marcadores[int(m.group(1))], t)
    return t


def campos(lineas: list[str]) -> tuple[dict, list[str]]:
    """Separa las líneas `clave: valor` del resto del bloque."""
    meta, resto = {}, []
    for l in lineas:
        m = re.match(r"^(\w+):\s*(.*)$", l.strip())
        if m and not l.strip().startswith("|"):
            meta[m.group(1)] = m.group(2)
        else:
            resto.append(l)
    return meta, resto


def portada(meta: dict) -> str:
    p = [r"\thispagestyle{portada}", r"\begin{center}", r"\vspace*{3\baselineskip}",
         r"\textbf{" + en_linea(meta.get("titulo", "")) + "}",
         r"\vspace{2\baselineskip}"]
    for clave in ("autor", "afiliacion", "programa", "asesor", "fecha"):
        if meta.get(clave):
            p.append(r"\par " + en_linea(meta[clave]))
    p += [r"\end{center}", r"\vfill"]
    if meta.get("nota"):
        p += [r"\begin{center}\textit{Nota del autor}\end{center}",
              r"\begin{bloque}", en_linea(meta["nota"]), r"\end{bloque}"]
    p.append(r"\newpage")
    return "\n".join(p)


def tabla(num: str, meta: dict, filas_md: list[str]) -> str:
    filas = [[c.strip() for c in l.strip().strip("|").split("|")]
             for l in filas_md if l.strip().startswith("|")]
    filas = [f for f in filas if not all(set(c) <= set("-: ") for c in f)]
    if not filas:
        return ""
    n = len(filas[0])
    # tabularx reparte el ancho disponible entre columnas flexibles, de modo que
    # la tabla nunca excede el margen por larga que sea una cabecera; con anchos
    # fijos, la última columna de la Tabla 2 se salía de la página.
    # Los pesos deben sumar el número de columnas: la primera lleva texto
    # descriptivo y recibe `peso`; las restantes se reparten el resto por igual.
    if n > 1:
        peso = float(meta.get("peso", 2.0))
        peso = min(peso, n - 0.5)          # dejar sitio a las columnas de cifras
        resto = (n - peso) / (n - 1)
        ancho = lambda w, t: (rf">{{\hsize={w:.4f}\hsize\linewidth=\hsize}}{t}")
        col = ancho(peso, "X") + "".join(ancho(resto, "D") for _ in range(n - 1))
    else:
        col = "X"
    # Flotante para que el título, el cuerpo y la nota no se separen entre
    # páginas: sin él la tabla quedaba partida con el encabezado huérfano.
    out = [r"\begin{table}[htbp]",
           r"\begin{singlespace}", r"\noindent\textbf{Tabla " + num + "}",
           r"\par\noindent\textit{" + en_linea(meta.get("titulo", "")) + "}",
           r"\end{singlespace}", r"\vspace{0.5\baselineskip}",
           r"\begin{center}", r"\begin{tabularx}{\textwidth}{" + col + "}", r"\toprule"]
    out.append(" & ".join(en_linea(c) for c in filas[0]) + r" \\")
    out.append(r"\midrule")
    for f in filas[1:]:
        f = (f + [""] * n)[:n]
        out.append(" & ".join(en_linea(c) for c in f) + r" \\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{center}"]
    if meta.get("nota"):
        out.append(r"\begin{singlespace}\noindent{\footnotesize\textit{Nota.} "
                   + en_linea(meta["nota"]) + r"}\end{singlespace}")
    out.append(r"\end{table}")
    return "\n".join(out)


def figura(num: str, meta: dict) -> str:
    ruta = (FIGS / meta["archivo"]).as_posix()
    out = [r"\begin{figure}[htbp]",
           r"\begin{singlespace}", r"\noindent\textbf{Figura " + num + "}",
           r"\par\noindent\textit{" + en_linea(meta.get("titulo", "")) + "}",
           r"\end{singlespace}", r"\vspace{0.5\baselineskip}",
           r"\centering",
           rf"\includegraphics[width=0.95\textwidth]{{{ruta}}}"]
    if meta.get("nota"):
        out += [r"\par\vspace{0.5\baselineskip}",
                r"\begin{singlespace}\noindent{\footnotesize\textit{Nota.} "
                + en_linea(meta["nota"]) + r"}\end{singlespace}"]
    out.append(r"\end{figure}")
    return "\n".join(out)


def convierte(md: str) -> str:
    lineas = md.split("\n")
    out: list[str] = []
    i = 0
    en_refs = False
    # El resumen y el abstract van en bloque, sin sangría de primera línea.
    SIN_SANGRIA = {"resumen", "abstract"}
    en_bloque = False

    while i < len(lineas):
        st = lineas[i].strip()

        if st.startswith(":::"):
            cab = st[3:].strip().split()
            if cab:
                tipo, num = cab[0], (cab[1] if len(cab) > 1 else "")
                cuerpo = []
                i += 1
                while i < len(lineas) and lineas[i].strip() != ":::":
                    cuerpo.append(lineas[i])
                    i += 1
                i += 1
                meta, filas = campos(cuerpo)
                if tipo == "portada":
                    out.append(portada(meta))
                elif tipo == "tabla":
                    out.append(tabla(num, meta, filas))
                elif tipo == "figura":
                    out.append(figura(num, meta))
                continue
            i += 1
            continue

        if st in ("---", "***") or not st:
            out.append("")
            i += 1
            continue

        # ## = nivel 1 (centrado, negrita); ### = nivel 2 (izquierda, negrita);
        # #### = nivel 3 (izquierda, negrita cursiva).
        if st.startswith("#### "):
            out.append(r"\subsubsection*{" + en_linea(st[5:]) + "}")
            i += 1
            continue
        if st.startswith("### "):
            out.append(r"\subsection*{" + en_linea(st[4:]) + "}")
            i += 1
            continue
        if st.startswith("## "):
            if en_refs:
                out.append(r"\end{referencias}")
                en_refs = False
            titulo = st[3:]
            out.append(r"\section*{" + en_linea(titulo) + "}")
            en_bloque = titulo.strip().lower() in SIN_SANGRIA
            if titulo.strip().lower().startswith("referencias"):
                out.append(r"\begin{referencias}")
                en_refs = True
            i += 1
            continue
        if st.startswith("# "):
            i += 1  # el título vive en la portada
            continue

        # Listas. Un solo entorno para todos los elementos: cerrarlo en cada
        # línea de continuación reiniciaba la numeración y producía «1.» repetido.
        es_num = re.match(r"^\d+\. ", st) is not None
        es_vin = re.match(r"^[-*] ", st) is not None and not st.startswith("**")
        if es_num or es_vin:
            ent = "enumerate" if es_num else "itemize"
            out.append(r"\begin{" + ent + "}")
            while i < len(lineas):
                s = lineas[i].strip()
                if not s:
                    j = i + 1
                    while j < len(lineas) and not lineas[j].strip():
                        j += 1
                    if j >= len(lineas) or not re.match(r"^\d+\. |^[-*] ",
                                                        lineas[j].strip()):
                        break
                    i = j
                    continue
                marca = re.match(r"^(?:\d+\.|[-*]) ", s)
                if not marca:
                    break
                texto = s[marca.end():]
                j = i + 1
                while (j < len(lineas) and lineas[j].strip()
                       and not re.match(r"^(?:\d+\.|[-*]) ", lineas[j].strip())
                       and not lineas[j].strip().startswith((":::", "#", "|"))):
                    texto += " " + lineas[j].strip()
                    j += 1
                out.append(r"\item " + en_linea(texto))
                i = j
            out.append(r"\end{" + ent + "}")
            continue

        parr = []
        while i < len(lineas) and lineas[i].strip():
            s = lineas[i].strip()
            if s.startswith((":::", "#", "|")):
                break
            if re.match(r"^\d+\. |^[-*] ", s) and not s.startswith("**"):
                break
            parr.append(s)
            i += 1
        if parr:
            texto = " ".join(parr)
            if en_bloque:
                out.append(r"\begin{bloque}" + en_linea(texto) + r"\end{bloque}")
            else:
                out.append(en_linea(texto))
            out.append("")
        else:
            i += 1

    if en_refs:
        out.append(r"\end{referencias}")
    return "\n".join(out) + "\n\\end{document}\n"


def main() -> int:
    if not shutil.which("pdflatex"):
        print("No hay pdflatex en el sistema.")
        return 1
    if not FUENTE.exists():
        print(f"No existe {FUENTE.relative_to(RAIZ)}")
        return 1

    tex = PREAMBULO + convierte(FUENTE.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "art.tex").write_text(tex, encoding="utf-8")
        for _ in range(2):
            r = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "art.tex"],
                cwd=t, capture_output=True, text=True, errors="replace")
        if not (t / "art.pdf").exists():
            print("pdflatex falló. Últimas líneas del registro:\n")
            print("\n".join(r.stdout.strip().split("\n")[-25:]))
            (RAIZ / "salidas" / "art_fallido.tex").write_text(tex, encoding="utf-8")
            print("\nLaTeX generado en salidas/art_fallido.tex para inspección.")
            return 1
        SALIDA.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(t / "art.pdf", SALIDA)

    print(f"Escrito: {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
