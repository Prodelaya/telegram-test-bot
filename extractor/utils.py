"""
Utilidades para el extractor de preguntas.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Union

# --------------------------------------------------------------------------- #
#  Configuración de logging con rotación (5 MB, 3 copias)
# --------------------------------------------------------------------------- #
LOG_DIR = Path("/opt/telegram-test-bot/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("extractor_utils")
_logger.setLevel(logging.INFO)

if not any(isinstance(h, RotatingFileHandler) for h in _logger.handlers):
    file_handler = RotatingFileHandler(
        LOG_DIR / "extractor_utils.log",
        maxBytes=5_242_880,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    stream_handler = logging.StreamHandler()
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(fmt)
    stream_handler.setFormatter(fmt)
    _logger.addHandler(file_handler)
    _logger.addHandler(stream_handler)
# --------------------------------------------------------------------------- #


def get_docx_files(directory: Union[str, Path]) -> List[str]:
    """
    Devuelve lista de rutas a archivos .docx dentro de *directory* (recursivo).
    Ignora archivos temporales que empiezan por "~$".
    """
    try:
        dir_path = Path(directory)
        docx_files = [
            str(p) for p in dir_path.rglob("*.docx")
            if not p.name.startswith("~$")
        ]
        _logger.info("Se encontraron %s archivos DOCX en %s", len(docx_files), directory)
        return docx_files
    except Exception as exc:
        _logger.error("Error al listar DOCX en %s: %s", directory, exc)
        return []


def ensure_directory_exists(directory: Union[str, Path]) -> bool:
    """
    Crea recursivamente *directory* si no existe.
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as exc:
        _logger.error("No se pudo crear el directorio %s: %s", directory, exc)
        return False


def clean_text(text: str) -> str:
    """
    Normaliza espacios y elimina saltos de línea/tabulaciones extra en *text*.
    """
    if not text:
        return ""

    # Reemplazar saltos/tabulaciones por un único espacio
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Compactar espacios múltiples
    return " ".join(text.split())
