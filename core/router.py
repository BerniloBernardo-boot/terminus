"""
core/router.py — Dispatcher central com lógica de fallback correcta.

Pipeline:
  1. Validar input (Validator)
  2. Classificar intenção (Parser)
  3. Módulos especializados (scan, exec, setup) — sem IA
  4. IA primeiro (com histórico multi-turn)
  5. Fallback offline (base local) se IA falhou ou indisponível
  6. No-match final
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import SessionContext
    from cli.ui import TerminusUI

from engine.parser   import IntentParser
from engine.solver   import Solver
from engine.safety   import SafetyGuard
from core.config     import Config
from utils.validator import Validator


def _is_real_answer(r: object) -> bool:
    """
    Retorna True APENAS para respostas úteis ao utilizador.
    Exclui explicitamente dicts de erro (type="error") e dicts vazios.
    Isto garante que o fallback chain funciona correctamente.
    """
    return (
        isinstance(r, dict)
        and bool(r.get("body", "").strip())
        and r.get("type") not in (None, "error")
    )


class Router:
    def __init__(self, ctx: "SessionContext"):
        self.ctx    = ctx
        self.parser = IntentParser()
        self.solver = Solver()
        self.guard  = SafetyGuard()
        self.cfg    = Config()

    # ── Dispatcher principal ────────────────────────────────────────
    def route(self, raw: str, ui: "TerminusUI") -> dict:
        # 1. Validar e sanitizar input
        v = Validator.validate(raw)
        if not v.ok:
            return {
                "type": "block", "title": "Input inválido",
                "body": f"Motivo: {v.reason}\n\nTente formular a pergunta de forma diferente.",
                "steps": [], "warning": "", "tip": "",
            }
        raw = v.value

        # 2. Classificar intenção
        intent = self.parser.parse(raw)
        module = intent.get("module", "geral")
        topic  = intent.get("topic", raw)
        self.ctx.set_last_intent(intent)

        # 3. Módulos que não usam IA
        if module == "setup":
            from modules.setup import run_setup
            return self._tag(run_setup(topic=intent.get("topic", ""), ui=ui), "setup")

        if module == "scan":
            from modules.scan import run_scan
            return self._tag(run_scan(), module)

        if module == "exec":
            return self._tag(self._exec_flow(intent.get("command", raw), ui), module)

        # 4. IA primeiro (para fix, learn, e linguagem natural)
        ai_result = {}
        if self.cfg.has_ai():
            ai_result = self._call_ai(raw)
            if _is_real_answer(ai_result):
                return self._tag(ai_result, module)

        # 5. Fallback offline (sem IA, sem internet, ou IA falhou)
        offline = self._offline_fallback(module, topic, raw)
        if _is_real_answer(offline):
            offline["_offline"] = True
            return self._tag(offline, module)

        # 6. Se a IA retornou um erro conhecido, mostrá-lo
        # (melhor que "não entendi" quando há um motivo real)
        if isinstance(ai_result, dict) and ai_result.get("type") == "error":
            return self._tag(ai_result, module)

        # 7. No-match final
        return self._tag(self._no_match(raw), module)

    # ── Chamar a IA ───────────────────────────────────────────────
    def _call_ai(self, query: str) -> dict:
        try:
            from engine.ai import AIEngine
            history = self.ctx.get_ai_messages(max_turns=6)
            return AIEngine().interpret(query, history)
        except Exception:
            return {}

    # ── Fallback offline ──────────────────────────────────────────
    def _offline_fallback(self, module: str, topic: str, raw: str) -> dict:
        """Base local de problemas e tutoriais — funciona sem internet."""
        # Solver (problems.json)
        r = self.solver.solve(raw)
        if _is_real_answer(r):
            return r

        # Módulo learn
        if module == "learn":
            from modules.learn import LearnModule
            r = LearnModule().teach(topic)
            if _is_real_answer(r):
                return r

        # Módulo fix
        if module in ("fix", "geral"):
            from modules.fix import FixModule
            r = FixModule().fix(raw)
            if _is_real_answer(r):
                return r

        return {}

    # ── No-match ─────────────────────────────────────────────────
    def _no_match(self, query: str) -> dict:
        if not self.cfg.has_ai():
            return {
                "type":  "info",
                "title": "IA não configurada — modo offline",
                "body":  (
                    "Sem chave de IA, o Terminus usa apenas a base local.\n\n"
                    "Para activar a IA (grátis):\n"
                    "  1. Acede a: aistudio.google.com/app/apikey\n"
                    "  2. Cria uma chave\n"
                    "  3. Executa: terminus setup\n\n"
                    "Enquanto isso:\n"
                    "  fix wifi · fix disco cheio · learn docker · scan"
                ),
                "tip":     "setup",
                "warning": "",
            }
        return {
            "type":  "info",
            "title": "Não entendi",
            "body":  (
                "Não consegui processar esta solicitação.\n\n"
                "Tenta ser mais específico, por exemplo:\n"
                "  'meu wifi para depois de suspender'\n"
                "  'quero aprender a criar scripts bash'\n"
                "  'o disco está cheio mas não sei o que ocupa'\n\n"
                "Ou usa: scan · fix wifi · learn docker"
            ),
            "tip":     "",
            "warning": "",
        }

    # ── Execution flow ────────────────────────────────────────────
    def _exec_flow(self, command: str, ui: "TerminusUI") -> dict:
        if not command.strip():
            return self._no_match("")
        blocked, reason = self.guard.check(command)
        if blocked:
            return {
                "type":    "block",
                "title":   "Comando bloqueado pelo SafetyGuard",
                "body":    f"Comando: {command}\nMotivo: {reason}",
                "warning": "O Terminus nunca executa comandos destrutivos.",
                "steps":   [],
            }
        return ui.run_command_flow(command, is_dangerous=self.guard.is_dangerous(command))

    @staticmethod
    def _tag(response: dict, module: str) -> dict:
        if isinstance(response, dict):
            response["_module"] = module
        return response
