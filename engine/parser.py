"""
engine/parser.py — Lightweight NLP intent parser (no external deps).
Maps free-form Portuguese/English input to structured intents.
"""

import re
from typing import Optional

LEARN_KW = {
    "learn","aprender","ensina","ensinar","o que é","o que e","como funciona",
    "explica","explicar","tutorial","aula","estudar","entender",
    "como usar","how to","what is","me explica","me ensina","quero aprender",
    "quero entender","quero saber","o que são","o que sao","pra que serve",
    "para que serve","como é","como e","me conta","me fala",
}
FIX_KW = {
    "fix","resolver","problema","erro","error","bug","broken",
    "não funciona","nao funciona","falhando","parou","crashed",
    "lento","devagar","cheio","sem espaço","sem internet",
    "conserta","consertar","corrigir","help me fix","how do i fix",
    "diagnose","diagnosticar","não abre","nao abre","travando",
    "não conecta","nao conecta","não instala","nao instala",
}
SCAN_KW = {
    "scan","verificar","verificação","checar","check","status",
    "saúde","saude","system health","health check","analisar",
    "análise","analise","monitorar","monitoramento",
}

LEARN_STRIP = re.compile(
    r"^(learn|aprender|ensina(?:r)?|o que [eé]|explica(?:r)?|"
    r"como (?:usar|funciona)|tutorial|me (?:explica|ensina|conta|fala)|"
    r"how to|what is|quero (?:aprender|entender|saber)|"
    r"pra que serve|para que serve|como [eé])\s+",
    re.IGNORECASE
)
FIX_STRIP = re.compile(
    r"^(fix|resolver|conserta(?:r)?|corrigir|diagnosticar|help me fix|how do i fix)\s+",
    re.IGNORECASE
)

SETUP_KW = {
    "setup","config","configurar","configuração","configuracao",
    "provider","alterar chave",
    "mudar chave","trocar modelo","trocar provider",
}

# Prefixos a remover do input (nome do programa, saudações, etc.)
NOISE_STRIP = re.compile(
    r"^(terminus\s*[,:]?\s*|terminus2\s*[,:]?\s*|oi\s*[,:]?\s*|"
    r"olá\s*[,:]?\s*|hey\s*[,:]?\s*|ei\s*[,:]?\s*)+",
    re.IGNORECASE
)

SHELL_CMDS = {
    "ls","cd","mkdir","rm","cp","mv","cat","grep","find","chmod","chown",
    "ps","kill","df","du","apt","apt-get","dnf","yum","pacman","systemctl",
    "service","sudo","ping","curl","wget","tar","zip","unzip","ssh","scp",
    "git","python","python3","nano","vim","touch","echo","export","source",
    "bash","sh","which","whereis","top","htop","free","uname","lsblk",
    "ip","ifconfig","nmcli","journalctl","dmesg","lsof","ss","netstat",
}


class IntentParser:
    def parse(self, raw: str) -> dict:
        # Remover ruído do início (nome do programa, saudações)
        text  = NOISE_STRIP.sub("", raw.strip()).strip()
        lower = text.lower()

        # Setup / Config
        if lower.strip() in SETUP_KW or lower.startswith("setup") or lower.startswith("config"):
            topic = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
            return {"module": "setup", "topic": topic, "raw": text}

        # Explicit learn prefix
        for prefix in ("learn ", "aprender "):
            if lower.startswith(prefix):
                return {"module": "learn",
                        "topic":  LEARN_STRIP.sub("", text).strip(),
                        "raw":    text}

        # Explicit fix prefix
        for prefix in ("fix ", "resolver ", "conserta "):
            if lower.startswith(prefix):
                return {"module": "fix",
                        "topic":  FIX_STRIP.sub("", text).strip(),
                        "raw":    text}

        # scan
        if lower.strip() in ("scan", "verificar sistema", "checar sistema",
                              "system health", "analise do sistema"):
            return {"module": "scan", "raw": text}

        # Keyword scoring
        module, score = self._score(lower)
        if score >= 2:
            topic = self._extract_topic(lower, module, text)
            return {"module": module, "topic": topic, "raw": text}

        # Shell command heuristic
        if self._is_command(text):
            return {"module": "exec", "command": text, "raw": text}

        # Natural language → vai direto para a IA
        return {"module": "geral", "topic": text, "raw": text}

    def _score(self, lower: str) -> tuple[str, int]:
        scores = {
            "learn": sum(1 for kw in LEARN_KW if kw in lower),
            "fix":   sum(1 for kw in FIX_KW   if kw in lower),
            "scan":  sum(1 for kw in SCAN_KW   if kw in lower),
        }
        best = max(scores, key=scores.get)
        return best, scores[best]

    def _extract_topic(self, lower: str, module: str, original: str) -> str:
        if module == "learn":
            return LEARN_STRIP.sub("", original).strip() or original
        if module == "fix":
            return FIX_STRIP.sub("", original).strip() or original
        return original

    def _is_command(self, text: str) -> bool:
        first = text.strip().split()[0].lstrip("$").strip() if text.strip() else ""
        return first.lower() in SHELL_CMDS
