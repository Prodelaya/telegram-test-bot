"""
Paquete extractor

Reexporta las clases y helpers principales para importar fácilmente:

    from extractor import parse_docx, JsonBuilder, get_docx_files, ...
"""

from .docx_parser import parse_docx
from .json_builder import JsonBuilder
from .utils import (
    get_docx_files,
    ensure_directory_exists,
    clean_text,
)

__all__ = [
    'parse_docx',
    'JsonBuilder',
    'get_docx_files',
    'ensure_directory_exists',
    'clean_text',
]