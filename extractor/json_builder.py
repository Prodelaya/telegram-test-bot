"""
Módulo para construir y mantener un único JSON con todas las preguntas
extraídas de los .docx.

* Acepta ahora preguntas con **3‑5 opciones**.
* Si la letra de la respuesta no casa con las letras de opciones,
  intenta mapearla buscando coincidencia de texto.
* Permite explicación o referencia vacías (ya se completa luego si se desea).
"""

from __future__ import annotations

import json
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Any

from extractor.utils import ensure_directory_exists, clean_text

LOG_DIR = Path("/opt/telegram-test-bot/data/logs")
ensure_directory_exists(LOG_DIR)

logger = logging.getLogger("json_builder")
logger.setLevel(logging.INFO)
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    fh = RotatingFileHandler(LOG_DIR / "json_builder.log", maxBytes=5_242_880, backupCount=3, encoding="utf-8")
    sh = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt); sh.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(sh)


class JsonBuilder:
    """Mantiene (crear / actualizar) preguntas en un único archivo JSON."""

    def __init__(self, output_file: str):
        self.output_file = Path(output_file)

    # ------------------------------------------------------------------
    #  API pública
    # ------------------------------------------------------------------
    def build_json(
        self,
        asignatura: str,
        origen: str,
        preguntas: List[Dict[str, Any]],
        mode: str = "replace",
    ) -> bool:
        """Valida y vuelca *preguntas* de una asignatura‑origen al JSON.
        *mode* = "replace" elimina las preguntas previas del mismo par.
        """
        try:
            valid = self._validate_questions(asignatura, origen, preguntas)
            if not valid:
                return False

            data = self._load_existing()
            if mode == "replace":
                data["preguntas"] = [p for p in data["preguntas"]
                    if not (p.get("asignatura") == asignatura and p.get("origen") == origen)]

            new_entries = self._build_entries(asignatura, origen, valid, data)
            data["preguntas"].extend(new_entries)
            data["preguntas"].sort(key=lambda p: p["id"])
            self._save(data)
            logger.info("%d preguntas agregadas para %s (%s)", len(new_entries), asignatura, origen)
            return True
        except Exception as exc:
            logger.exception("Error al construir JSON: %s", exc)
            return False

    # ------------------------------------------------------------------
    #  helpers internos
    # ------------------------------------------------------------------
    def _validate_questions(self, asign: str, orig: str, qs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra preguntas mal formadas, permite 3‑5 opciones.
        Si la letra de la respuesta no encaja, busca por coincidencia de texto.
        """
        valids: List[Dict[str, Any]] = []
        for idx, q in enumerate(qs, 1):
            opts = q.get("opciones", [])
            if not (3 <= len(opts) <= 5):
                logger.warning("[%s-%s] P%d ignorada: %d opciones (se esperan 3‑5)", asign, orig, idx, len(opts))
                continue

            # letras únicas A‑E
            letras = {o["letra"].upper() for o in opts}
            ans = q.get("respuesta_correcta", "").upper()

            if ans not in letras:
                # intento 1: buscar respuesta por coincidencia textual
                ans_text = ans if len(ans) > 1 else ""
                if ans_text:
                    for o in opts:
                        if ans_text.lower() in o["texto"].lower():
                            ans = o["letra"]; break
                
                # intento 2: buscar si la respuesta está entre paréntesis (Opción 3 (C))
                if ans not in letras:
                    # Extraer de la respuesta original si contiene un formato como "Opción X (Y)"
                    respuesta_orig = q.get("respuesta_original", "")
                    if respuesta_orig:
                        match = re.search(r"\(([A-E])\)", respuesta_orig, re.I)
                        if match:
                            possible_ans = match.group(1).upper()
                            if possible_ans in letras:
                                ans = possible_ans
                
                # Si la respuesta es "todas" o "ninguna" (para futura implementación)
                
                # Si no se pudo determinar, marcar vacía
                if ans not in letras:
                    logger.warning("[%s-%s] P%d: no se reconoce la letra de respuesta; se marca vacía", asign, orig, idx)
                    ans = ""

            valids.append({
                "enunciado": clean_text(q.get("enunciado", "")),
                "opciones" : sorted([
                    {"letra": o["letra"].upper(), "texto": clean_text(o["texto"])} for o in opts
                ], key=lambda x: x["letra"]),
                "respuesta_correcta": ans,
                "explicacion": clean_text(q.get("explicacion", "")),
                "referencia" : clean_text(q.get("referencia", "")),
            })
        if not valids:
            logger.warning("No hay preguntas válidas para %s (%s)", asign, orig)
        return valids

    # --------------------------------------------------------------
    def _load_existing(self) -> Dict[str, Any]:
        if self.output_file.exists() and self.output_file.stat().st_size > 0:
            try:
                return json.loads(self.output_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("%s corrupto, se rehace.", self.output_file)
        return {"preguntas": []}

    # --------------------------------------------------------------
    def _build_entries(self, asign: str, orig: str, qs: List[Dict[str, Any]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Generar prefijos a partir de las iniciales de palabras en asignatura y origen
        pref_as = "".join(w[0].upper() for w in asign.split())
        pref_or = "".join(w[0].upper() for w in orig.split())
        id_prefix = f"{pref_as}_{pref_or}_"
        
        # Buscar el número más alto existente para este prefijo
        existing_nums = [int(p["id"].split("_")[-1]) for p in data["preguntas"]
                         if p["id"].startswith(id_prefix) and p["id"].split("_")[-1].isdigit()]
        next_idx = max(existing_nums, default=0) + 1

        new_entries = []
        for off, q in enumerate(qs, start=next_idx):
            qid = f"{id_prefix}{off:03d}"
            new_entries.append({
                "id": qid,
                "asignatura": asign,
                "origen": orig,
                **q,
            })
        return new_entries

    # --------------------------------------------------------------
    def _save(self, data: Dict[str, Any]):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")