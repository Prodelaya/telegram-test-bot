"""
Parser de archivos DOCX con preguntas tipo test.

✔ Reconoce dos formatos de los documentos recibidos:
  1. **Clásico** ─ líneas "OPCIÓN 1 (A): …"
  2. **Lista con viñeta** ─ "• A) …" (sin la palabra OPCIÓN)

✔ Tolera que las cabeceras y los separadores usen «:» o «.».
✔ Divide los párrafos que contienen saltos blandos (Shift+Enter) para no perder información.
✔ Devuelve:
    {
        "asignatura": str,
        "origen": str,
        "preguntas": [
            {
                "enunciado": str,
                "opciones": [{"letra", "texto"}],
                "respuesta_correcta": "A"|"B"|"C"|"D",
                "explicacion": str,
                "referencia": str,
            }, …
        ]
    }

No genera ID: eso lo hace `JsonBuilder`.
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Dict, List, Any

from docx import Document  # python-docx

from .utils import clean_text

LOGGER = logging.getLogger("docx_parser")
if not LOGGER.handlers:
    LOGGER.addHandler(logging.NullHandler())

# --------------------------------------------------------------------------- #
#  Expresiones regulares                                                      #
# --------------------------------------------------------------------------- #
RE_ASIGNATURA = re.compile(r"^ASIGNATURA\s*[:.]\s*(.+)$", re.I)
RE_ORIGEN     = re.compile(r"^ORIGEN\s*[:.]\s*(.+)$", re.I)
RE_PREGUNTA   = re.compile(r"^PREGUNTA\s+\d+\s*[.:]\s*(.+)$", re.I)

# Formato 1:  OPCIÓN 1 (A): texto
PAT_CLASICO = r"OPCI[ÓO]N\s+\d+\s*\(\s*(?P<let1>[A-D])\s*\)\s*[.:–-]\s*(?P<txt1>.+)"
# Formato 2:  • A) texto  OR  - A) texto
PAT_LISTA   = r"^[\u2022•\-]?\s*(?P<let2>[A-D])\)\s+(?P<txt2>.+)"
RE_OPCION   = re.compile(f"(?:{PAT_CLASICO})|(?:{PAT_LISTA})", re.I)

# MODIFICADO: Expresión regular mejorada para capturar diferentes formatos de respuesta correcta
RE_RESPUESTA   = re.compile(r"^RESPUESTA\s+CORRECTA\s*[:.]\s*(?:(?:Opción\s+\d+\s*\()([A-D])\)|([A-D]))", re.I)
RE_REFERENCIA  = re.compile(r"^REFERENCIA\s*[:.]\s*(.+)$", re.I)
RE_EXPLICACION = re.compile(r"^EXPLICACI[ÓO]N\s*[:.]\s*(.+)$", re.I)

# --------------------------------------------------------------------------- #
#  API pública                                                                 
# --------------------------------------------------------------------------- #

def parse_docx(file_path: str | Path) -> Dict[str, Any]:
    """Devuelve la información estructurada del DOCX."""

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    doc = Document(str(file_path))

    # Expandir cada párrafo en posibles sub-líneas por saltos blandos
    lines: List[str] = []
    for p in doc.paragraphs:
        if not p.text.strip():
            continue
        for chunk in p.text.splitlines():
            text = clean_text(chunk)
            if text:
                lines.append(text)

    asignatura = origen = ""
    preguntas: List[Dict[str, Any]] = []

    idx = 0
    total = len(lines)

    # ------------------- Cabeceras ------------------- #
    while idx < total:
        ln = lines[idx]
        if not asignatura and (m := RE_ASIGNATURA.match(ln)):
            asignatura = m.group(1).strip()
            idx += 1
            continue
        if not origen and (m := RE_ORIGEN.match(ln)):
            origen = m.group(1).strip()
            idx += 1
            continue
        if asignatura and origen:
            break
        idx += 1

    if not (asignatura and origen):
        raise ValueError(f"Faltan ASIGNATURA/ORIGEN en {file_path.name}")

    # ------------------- Preguntas ------------------- #
    current: Dict[str, Any] | None = None
    while idx < total:
        ln = lines[idx]

        # Inicio de pregunta
        if m := RE_PREGUNTA.match(ln):
            if current:
                _commit(current, preguntas)
            current = {
                "enunciado": m.group(1).strip(),
                "opciones": [],
                "respuesta_correcta": "",
                "explicacion": "",
                "referencia": "",
            }
            idx += 1
            continue

        # Opciones (ambos formatos)
        if current and (m := RE_OPCION.match(ln)):
            letra = (m.group("let1") or m.group("let2")).upper()
            texto  = (m.group("txt1") or m.group("txt2")).strip()
            current["opciones"].append({"letra": letra, "texto": texto})
            idx += 1
            continue

        # Respuesta correcta - MODIFICADO para capturar ambos formatos
        if current and (m := RE_RESPUESTA.match(ln)):
            # Extraer la letra de respuesta del primer o segundo grupo capturado
            current["respuesta_correcta"] = (m.group(1) or m.group(2)).upper()
            idx += 1
            continue
        
        # Si no se pudo extraer con la expresión regular pero la línea contiene "RESPUESTA CORRECTA"
        if current and ln.startswith("RESPUESTA CORRECTA"):
            # Método alternativo: buscar directamente la letra entre paréntesis
            if match := re.search(r"\(([A-D])\)", ln, re.I):
                current["respuesta_correcta"] = match.group(1).upper()
            else:
                # Alternativa para formato "A) texto"
                if match := re.search(r":\s*([A-D])\)", ln, re.I):
                    current["respuesta_correcta"] = match.group(1).upper()
            idx += 1
            continue

        # Referencia
        if current and (m := RE_REFERENCIA.match(ln)):
            current["referencia"] = m.group(1).strip()
            idx += 1
            continue

        # Explicación
        if current and (m := RE_EXPLICACION.match(ln)):
            current["explicacion"] = m.group(1).strip()
            idx += 1
            continue

        idx += 1  # nada reconocido → línea ignorada

    if current:
        _commit(current, preguntas)

    LOGGER.info("%d preguntas extraídas de %s", len(preguntas), file_path.name)
    return {"asignatura": asignatura, "origen": origen, "preguntas": preguntas}

# --------------------------------------------------------------------------- #
#  Helpers                                                                    #
# --------------------------------------------------------------------------- #

def _commit(q: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
    """Añade *q* a *out* si es coherente (3-5 opciones + respuesta válida)."""
    # MODIFICADO: Ahora acepta preguntas con 3-5 opciones
    if not (3 <= len(q["opciones"]) <= 5):
        LOGGER.warning("Pregunta omitida: %d opciones (se esperan 3-5)", len(q["opciones"]))
        return
    
    letras = {o["letra"] for o in q["opciones"]}
    if q["respuesta_correcta"] not in letras:
        LOGGER.warning("Pregunta omitida: respuesta '%s' fuera de %s", q["respuesta_correcta"], sorted(letras))
        return
    
    q["opciones"].sort(key=lambda o: o["letra"])
    out.append(q)