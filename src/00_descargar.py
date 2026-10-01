"""Descarga las fuentes declaradas en fuentes.py a datos/crudo/.

Escribe datos/crudo/MANIFIESTO.csv con SHA256, tamaño, URL y fecha de cada
archivo. El manifiesto es el respaldo de reproducibilidad del artículo: los
portales de datos abiertos reemplazan archivos sin avisar ni versionar, así que
el hash es la única prueba de contra qué versión se corrieron los resultados.

Uso:
    .venv/bin/python src/00_descargar.py                 # todo lo que falte
    .venv/bin/python src/00_descargar.py f911_ems coneval # solo esos grupos
    .venv/bin/python src/00_descargar.py --verificar      # revisa hashes, no baja
    .venv/bin/python src/00_descargar.py --reindexar      # rehace el manifiesto

NO correr dos instancias a la vez. El manifiesto se reescribe completo tras cada
descarga, así que dos procesos en paralelo se pisan las filas entre sí y el
archivo queda incompleto (sin que falte ningún dato en disco). Si pasa, se
arregla con --reindexar, que reconstruye el manifiesto a partir de lo que hay
en datos/crudo/.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from fuentes import CABECERAS, FUENTES

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "datos" / "crudo"
MANIFIESTO = CRUDO / "MANIFIESTO.csv"
TROZO = 1 << 20  # 1 MiB


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        while trozo := f.read(TROZO):
            h.update(trozo)
    return h.hexdigest()


def humano(n: int) -> str:
    for unidad in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidad == "GB":
            return f"{n:,.1f} {unidad}"
        n /= 1024
    return ""


class ContenidoInvalido(Exception):
    pass


def validar(ruta: Path, esperado: str) -> None:
    """Confirma que el archivo sea del tipo que pedimos.

    INEGI responde a rutas obsoletas con HTTP 200 y una página de error, así que
    raise_for_status() no protege de nada: lo que llega es HTML válido con el
    nombre de un .zip. Se revisan los primeros bytes y, si no cuadran, el
    archivo se descarta en vez de entrar al manifiesto como bueno.
    """
    with ruta.open("rb") as f:
        cabeza = f.read(512)

    if cabeza.lstrip()[:1] in (b"<",) or b"<!DOCTYPE html" in cabeza:
        raise ContenidoInvalido(
            "el servidor devolvió HTML (URL obsoleta o página de error)"
        )
    if esperado == ".zip" and not cabeza.startswith(b"PK"):
        raise ContenidoInvalido(f"no es un ZIP (empieza con {cabeza[:4]!r})")
    if esperado == ".csv":
        try:
            cabeza.decode("utf-8")
        except UnicodeDecodeError:
            cabeza.decode("latin-1")  # el F911 viene en latin-1 en varios ciclos
        if b"," not in cabeza and b";" not in cabeza and b"|" not in cabeza:
            raise ContenidoInvalido("no se detectó ningún separador en la cabecera")


def descargar(url: str, destino: Path) -> None:
    """Baja a un archivo .parcial, valida y renombra al terminar.

    El renombrado al final es lo que hace que el script sea seguro de reanudar:
    un archivo con el nombre definitivo está completo y validado por
    construcción, así que una descarga interrumpida o corrupta nunca se
    confunde con una exitosa.
    """
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with requests.get(url, headers=CABECERAS, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        bajado = 0
        with parcial.open("wb") as f:
            for trozo in r.iter_content(TROZO):
                f.write(trozo)
                bajado += len(trozo)
                if total:
                    pct = 100 * bajado / total
                    print(f"\r    {pct:5.1f}%  {humano(bajado)} / {humano(total)}",
                          end="", flush=True)
        print("\r" + " " * 50 + "\r", end="")
    try:
        validar(parcial, destino.suffix.lower())
    except ContenidoInvalido:
        parcial.unlink()
        raise
    parcial.rename(destino)


def leer_manifiesto() -> dict[str, dict[str, str]]:
    if not MANIFIESTO.exists():
        return {}
    with MANIFIESTO.open(newline="", encoding="utf-8") as f:
        return {fila["archivo"]: fila for fila in csv.DictReader(f)}


def escribir_manifiesto(filas: dict[str, dict[str, str]]) -> None:
    campos = ["archivo", "grupo", "ciclo", "bytes", "sha256", "descargado_utc", "url"]
    with MANIFIESTO.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for nombre in sorted(filas):
            w.writerow(filas[nombre])


def verificar(registro: dict[str, dict[str, str]]) -> int:
    problemas = 0
    for nombre, fila in sorted(registro.items()):
        ruta = CRUDO / nombre
        if not ruta.exists():
            print(f"  FALTA      {nombre}")
            problemas += 1
        elif sha256(ruta) != fila["sha256"]:
            print(f"  HASH DISTINTO  {nombre}")
            problemas += 1
        else:
            print(f"  ok         {nombre}  ({humano(int(fila['bytes']))})")
    return problemas


def reindexar() -> dict[str, dict[str, str]]:
    """Reconstruye el manifiesto a partir de los archivos que hay en disco.

    Recupera la fecha de la mtime del archivo, no de la descarga real, así que
    es una aproximación: se marca con sufijo ~ para no dar por exacta una fecha
    que no lo es. Solo indexa archivos declarados en FUENTES; cualquier otra
    cosa en datos/crudo/ se reporta aparte para que no pase inadvertida.
    """
    por_nombre = {n: (u, g, c) for n, u, g, c in FUENTES}
    registro: dict[str, dict[str, str]] = {}
    huerfanos = []

    for ruta in sorted(CRUDO.iterdir()):
        if not ruta.is_file() or ruta.name == MANIFIESTO.name:
            continue
        if ruta.suffix == ".parcial":
            print(f"  descarga incompleta, se borra: {ruta.name}")
            ruta.unlink()
            continue
        if ruta.name not in por_nombre:
            huerfanos.append(ruta.name)
            continue
        url, grupo, ciclo = por_nombre[ruta.name]
        mtime = datetime.fromtimestamp(ruta.stat().st_mtime, timezone.utc)
        print(f"  indexando {ruta.name}")
        registro[ruta.name] = {
            "archivo": ruta.name,
            "grupo": grupo,
            "ciclo": ciclo,
            "bytes": str(ruta.stat().st_size),
            "sha256": sha256(ruta),
            "descargado_utc": mtime.isoformat(timespec="seconds") + "~",
            "url": url,
        }

    faltantes = [n for n in por_nombre if n not in registro]
    if huerfanos:
        print(f"\n  No declarados en fuentes.py: {', '.join(huerfanos)}")
    if faltantes:
        print(f"\n  Declarados pero ausentes: {', '.join(faltantes)}")
    return registro


def main() -> int:
    args = sys.argv[1:]
    CRUDO.mkdir(parents=True, exist_ok=True)
    registro = leer_manifiesto()

    if "--reindexar" in args:
        print("Reconstruyendo el manifiesto desde datos/crudo/:\n")
        registro = reindexar()
        escribir_manifiesto(registro)
        print(f"\n{len(registro)} archivo(s) indexados en {MANIFIESTO.name}")
        return 0

    if "--verificar" in args:
        if not registro:
            print("No hay manifiesto: nada que verificar.")
            return 1
        print(f"Verificando {len(registro)} archivos contra el manifiesto:\n")
        problemas = verificar(registro)
        print(f"\n{'Todo íntegro.' if not problemas else f'{problemas} problema(s).'}")
        return 1 if problemas else 0

    grupos = set(args)
    pendientes = [
        f for f in FUENTES
        if (not grupos or f[2] in grupos) and not (CRUDO / f[0]).exists()
    ]
    ya = len([f for f in FUENTES if (not grupos or f[2] in grupos)]) - len(pendientes)

    if ya:
        print(f"{ya} archivo(s) ya estaban en disco; se omiten.")
    if not pendientes:
        print("Nada por descargar.")
        return 0

    print(f"Por descargar: {len(pendientes)} archivo(s)\n")
    fallos = []
    for i, (nombre, url, grupo, ciclo) in enumerate(pendientes, 1):
        destino = CRUDO / nombre
        print(f"[{i}/{len(pendientes)}] {nombre}")
        try:
            descargar(url, destino)
        except Exception as e:
            print(f"    ERROR: {type(e).__name__}: {e}")
            fallos.append(nombre)
            continue
        tam = destino.stat().st_size
        registro[nombre] = {
            "archivo": nombre,
            "grupo": grupo,
            "ciclo": ciclo,
            "bytes": str(tam),
            "sha256": sha256(destino),
            "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "url": url,
        }
        escribir_manifiesto(registro)  # se guarda tras cada éxito, no al final
        print(f"    listo  {humano(tam)}")

    print(f"\nManifiesto: {MANIFIESTO.relative_to(RAIZ)}")
    if fallos:
        print(f"Fallaron {len(fallos)}: {', '.join(fallos)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
