"""
core/context.py — Session state com histórico de conversa completo.

Guarda pares input/resposta para passar à IA como contexto multi-turn.
Permite que a IA lembre o que foi dito, o que foi tentado e o nível
da pessoa — como um professor que conhece o aluno.
"""

from datetime import datetime


class SessionContext:
    def __init__(self):
        self._exchanges: list[dict] = []   # {input, response_body, time, module}
        self._last_intent: dict    = {}
        self._cache: dict          = {}
        self.started_at            = datetime.now().isoformat()

    # ── Input / response tracking ─────────────────────────────────
    def add_input(self, text: str):
        self._exchanges.append({
            "time":          datetime.now().strftime("%H:%M:%S"),
            "input":         text,
            "response_body": "",
            "module":        "",
        })

    def add_response(self, response: dict):
        if not self._exchanges:
            return
        last = self._exchanges[-1]
        last["module"]        = response.get("_module", "")
        last["response_body"] = response.get("body", "")

    # ── Histórico para display (histórico tabela) ─────────────────
    def get_history(self) -> list[dict]:
        return [
            {"time": e["time"], "input": e["input"], "module": e["module"]}
            for e in self._exchanges
        ]

    # ── Histórico para IA (multi-turn conversation) ───────────────
    def get_ai_messages(self, max_turns: int = 6) -> list[dict]:
        """
        Retorna os últimos N pares como mensagens para a IA.
        Formato: [{"role": "user", "content": ...}, {"role": "model", "content": ...}, ...]
        Permite que a IA saiba o contexto da conversa actual.
        """
        messages = []
        recent = self._exchanges[-max_turns:]
        for ex in recent:
            messages.append({"role": "user",  "content": ex["input"]})
            if ex["response_body"]:
                messages.append({"role": "model", "content": ex["response_body"]})
        # Remover o último par incompleto (input sem resposta ainda)
        if messages and messages[-1]["role"] == "user":
            messages = messages[:-1]
        return messages

    def recent_inputs(self, n: int = 3) -> list[str]:
        return [e["input"] for e in self._exchanges[-n:]]

    # ── Intent ───────────────────────────────────────────────────
    def set_last_intent(self, intent: dict):
        self._last_intent = intent

    def get_last_intent(self) -> dict:
        return self._last_intent.copy()

    # ── Cache ────────────────────────────────────────────────────
    def cache_get(self, key: str):
        return self._cache.get(key)

    def cache_set(self, key: str, value):
        self._cache[key] = value
