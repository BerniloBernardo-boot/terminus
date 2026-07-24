"""
engine/brain.py — Brain: motor de decisão central.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.context import SessionContext

class Brain:
    _SETUP_KW    = {"setup","config","configurar","api","chave","provider","modelo"}
    _FIX_PRE     = ("fix ","resolver ","consertar ","corrigir ","diagnosticar ")
    _LEARN_PRE   = ("learn ","aprender ","ensina ","ensinar ","explica ","tutorial ")
    _SCAN_EXACT  = {"scan","verificar","status","analise"}
    _FIX_KW      = {"erro","error","bug","problema","fix","nao funciona","falhando","parou","lento","travando"}
    _LEARN_KW    = {"learn","aprender","ensina","explicar","tutorial","aula","entender","estudar"}
    _SCAN_KW     = {"scan","verificar","check","saude","health","analisar"}
    _SHELL       = {"ls","cd","mkdir","rm","cp","mv","cat","grep","find","chmod","chown","ps","kill",
                    "df","du","apt","dnf","pacman","systemctl","sudo","ping","curl","wget","tar",
                    "git","python","python3","nano","vim","echo","bash","sh","top","htop","free",
                    "uname","ip","ifconfig","journalctl"}

    def __init__(self, ctx: "SessionContext"):
        self.ctx = ctx

    def decide(self, raw: str) -> str:
        self.ctx.add_input(raw)
        return self._classify(raw)

    def _classify(self, raw: str) -> str:
        l = raw.strip().lower()
        if l in ("exit","quit","sair"):  return "BUILTIN_EXIT"
        if l in ("help","ajuda","?"):    return "BUILTIN_HELP"
        if l == "history":               return "BUILTIN_HISTORY"
        if l == "clear":                 return "BUILTIN_CLEAR"
        if l.split()[0] in self._SETUP_KW if l else False: return "MODULE_SETUP"
        if l in self._SCAN_EXACT or l.startswith("scan "): return "MODULE_SCAN"
        if any(l.startswith(p) for p in self._FIX_PRE):   return "MODULE_FIX"
        if any(l.startswith(p) for p in self._LEARN_PRE): return "MODULE_LEARN"
        first = raw.strip().split()[0].lstrip("$").lower() if raw.strip() else ""
        if first in self._SHELL: return "MODULE_EXEC"
        s = {
            "MODULE_FIX":   sum(1 for k in self._FIX_KW   if k in l),
            "MODULE_LEARN": sum(1 for k in self._LEARN_KW  if k in l),
            "MODULE_SCAN":  sum(1 for k in self._SCAN_KW   if k in l),
        }
        best = max(s, key=s.get)
        return best if s[best] >= 2 else "AI"
