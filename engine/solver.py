"""
engine/solver.py — Problem solver backed by problems.json.

Melhorias:
- Score mínimo obrigatório no partial match (evita falsos positivos)
- Retorna {} em vez de dict vazio quando não encontra (detectável pelo router)
- Confiança calculada e incluída na resposta
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional

DATA_FILE = Path(__file__).parent.parent / "data" / "problems.json"

# Score mínimo para aceitar um match parcial
MIN_SCORE = 2


class Solver:
    def __init__(self):
        self._data: Optional[list] = None

    @property
    def data(self) -> list:
        if self._data is None:
            self._data = _load()
        return self._data

    def solve(self, query: str) -> dict:
        match, confidence = self._best_match(query)
        if match and confidence >= MIN_SCORE:
            return self._fmt(match, confidence=confidence)
        return {}   # Sem match — router tenta próximo tier

    def _best_match(self, q: str) -> tuple[Optional[dict], int]:
        ql = q.lower().strip()

        # Tentativa 1: match direto por trigger
        for p in self.data:
            for trig in p.get("triggers", []):
                if trig.lower() in ql or ql in trig.lower():
                    return p, 10  # confiança máxima

        # Tentativa 2: score por palavras (MIN_SCORE mínimo)
        words = [w for w in ql.split() if len(w) > 3]
        if not words:
            return None, 0

        best, score = None, 0
        for p in self.data:
            hay = " ".join([
                p.get("id", ""),
                p.get("title", ""),
                *p.get("triggers", []),
                *p.get("tags", []),
            ]).lower()
            s = sum(1 for w in words if w in hay)
            if s > score:
                best, score = p, s

        return (best, score) if score >= MIN_SCORE else (None, 0)

    def _fmt(self, p: dict, note: str = "", confidence: int = 0) -> dict:
        steps = [
            {
                "label":       s.get("title", ""),
                "description": s.get("description", ""),
                "command":     s.get("command", ""),
            }
            for s in p.get("steps", [])
        ]
        cmds = [
            c if isinstance(c, dict) else {"cmd": c, "explain": ""}
            for c in p.get("commands", [])
        ]
        body = p.get("explanation", "")
        if note:
            body = f"({note})\n\n{body}"

        return {
            "type":       "fix",
            "title":      p.get("title", "Solução"),
            "body":       body,
            "steps":      steps,
            "commands":   cmds,
            "warning":    p.get("warning", ""),
            "tip":        p.get("tip", ""),
            "_confidence": confidence,
            "_source":    "solver_local",
        }


@lru_cache(maxsize=1)
def _load() -> list:
    try:
        return json.loads(DATA_FILE.read_text())
    except Exception:
        return []
