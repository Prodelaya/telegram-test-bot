"""
Script principal para extraer preguntas de archivos DOCX y guardarlas en JSON.
"""

from __future__ import annotations

import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ajustar imports relativos
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from extractor.docx_parser import parse_docx
from extractor.json_builder import JsonBuilder
from extractor.utils import get_docx_files, ensure_directory_exists

# Configuración de logging
LOG_DIR = Path("/opt/telegram-test-bot/data/logs")
ensure_directory_exists(LOG_DIR)

logger = logging.getLogger("extractor")
logger.setLevel(logging.INFO)
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    fh = RotatingFileHandler(LOG_DIR / "extractor.log", maxBytes=5_242_880, backupCount=3, encoding="utf-8")
    sh = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Extractor de preguntas de archivos DOCX")
    p.add_argument("-i", "--input", default="/opt/telegram-test-bot/docs/docx",
                   help="Directorio con archivos DOCX")
    p.add_argument("-o", "--output", default="/opt/telegram-test-bot/data/preguntas.json",
                   help="Archivo JSON de salida")
    p.add_argument("-m", "--mode", choices=["add", "replace"], default="replace",
                   help="Modo de operación: añadir (add) o reemplazar (replace). Por defecto 'replace'.")
    return p

def main() -> int:
    args = build_arg_parser().parse_args()
    logger.info("Iniciando extracción (modo=%s)", args.mode)

    in_dir = Path(args.input)
    if not in_dir.exists():
        logger.error("Directorio de entrada no encontrado: %s", in_dir)
        return 1

    ensure_directory_exists(Path(args.output).parent)
    docx_files = get_docx_files(str(in_dir))
    if not docx_files:
        logger.warning("No se encontraron archivos DOCX en %s", in_dir)
        return 0

    builder = JsonBuilder(args.output)
    total_preguntas = 0
    archivos_con_preguntas = 0

    for file_path in docx_files:
        try:
            logger.info("Procesando archivo: %s", file_path)
            result = parse_docx(file_path)
            asignatura, origen, preguntas = result["asignatura"], result["origen"], result["preguntas"]

            logger.info("  → %d preguntas extraídas para %s (%s)", len(preguntas), asignatura, origen)
            if not preguntas:
                continue

            if builder.build_json(asignatura, origen, preguntas, args.mode):
                archivos_con_preguntas += 1
                total_preguntas += len(preguntas)
            else:
                logger.error("  ¡Error guardando preguntas para %s (%s)!", asignatura, origen)

        except Exception as exc:
            logger.exception("Error procesando %s: %s", file_path, exc)

    logger.info("Proceso completado: %d preguntas de %d archivos", total_preguntas, archivos_con_preguntas)
    return 0

if __name__ == "__main__":
    sys.exit(main())
