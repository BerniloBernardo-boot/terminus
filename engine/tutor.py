"""
engine/tutor.py — Practical Linux tutor backed by tutorials.json.
"""

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional

DATA_FILE = Path(__file__).parent.parent / "data" / "tutorials.json"


class Tutor:
    def __init__(self):
        self._data: Optional[list] = None

    @property
    def data(self) -> list:
        if self._data is None:
            self._data = _load()
        return self._data

    def teach(self, topic: str) -> dict:
        tut = self._find(topic) or self._fuzzy(topic)
        if tut:
            return self._fmt(tut)

        return {
            "type":  "info",
            "title": f"Sem tutorial para: {topic}",
            "body":  (
                f"Ainda não tenho um tutorial local sobre '{topic}'.\n\n"
                "Tópicos disponíveis:\n"
                "permissões · processos · disco · rede · pacotes\n"
                "usuários · ssh · cron · logs · variáveis-ambiente"
            ),
            "tip": "Configure ANTHROPIC_API_KEY para tutoriais gerados por IA.",
        }

    def _find(self, topic: str) -> Optional[dict]:
        t = topic.lower().strip()
        for item in self.data:
            if t in item.get("id", "").lower():
                return item
            if t in item.get("title", "").lower():
                return item
            if any(t in kw or kw in t for kw in item.get("keywords", [])):
                return item
        return None

    def _fuzzy(self, topic: str) -> Optional[dict]:
        words = {w for w in topic.lower().split() if len(w) > 3}
        best, score = None, 0
        for item in self.data:
            hay = " ".join([item.get("id",""), item.get("title",""),
                            *item.get("keywords",[])]).lower()
            s = sum(1 for w in words if w in hay)
            if s > score:
                best, score = item, s
        return best if score >= 1 else None

    def _fmt(self, tut: dict, note: str = "") -> dict:
        steps = [{"label": s.get("title",""),
                  "description": s.get("description",""),
                  "command": s.get("command","")}
                 for s in tut.get("steps", [])]
        body = tut.get("overview", "")
        if note:
            body = f"({note})\n\n{body}"
        return {
            "type":    "learn",
            "title":   tut.get("title", "Tutorial"),
            "body":    body,
            "steps":   steps,
            "tip":     tut.get("tip", ""),
            "warning": tut.get("warning", ""),
        }


@lru_cache(maxsize=1)
def _load() -> list:
    try:
        return json.loads(DATA_FILE.read_text())
    except Exception:
        return []
