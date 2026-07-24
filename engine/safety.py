"""
engine/safety.py — SafetyGuard.
Blocks destructive commands. No exceptions.
"""

import re
from typing import Tuple

# ── Hard blocks — never execute ───────────────────────────────────────
BLOCKED: list[tuple[str, str]] = [
    (r"rm\s+-[rf]{1,2}\s+/(\s|$)",            "Apagaria todo o sistema de arquivos raiz"),
    (r"rm\s+-[rf]{1,2}\s+/\*",               "Apagaria todo o conteúdo da raiz"),
    (r"--no-preserve-root",                    "Flag que permite destruir a raiz do sistema"),
    (r"rm\s+-[rf]{1,2}\s+~\s*$",             "Apagaria todo o diretório home"),
    (r"rm\s+-[rf]{1,2}\s+\$HOME\s*$",        "Apagaria todo o diretório home"),
    (r"dd\s+.*of=/dev/[shnv]",               "Sobrescreveria um disco inteiro"),
    (r"mkfs(\.\w+)?\s+/dev/",                "Formataria uma partição/disco"),
    (r":\(\)\s*\{.*:.*\|.*:.*\}",            "Fork bomb detectada"),
    (r">\s*/dev/[sh]d[a-z]",                 "Escrita direta em dispositivo de bloco"),
    (r">\s*/etc/(passwd|shadow|fstab|grub)", "Sobrescrita de arquivo crítico"),
    (r"(curl|wget).*\|\s*(ba)?sh",           "Execução de script remoto sem inspeção"),
    (r"shutdown\s+(-[hH]\s+now|now)",        "Desligamento imediato"),
    (r"\bpoweroff\b",                        "Desligamento imediato"),
    (r"\bhalt\b",                            "Parada do sistema"),
    (r"rmmod\s+\S+",                         "Remoção de módulo do kernel"),
    (r"kill\s+-9\s+1\b",                     "Matar o processo init travaria o sistema"),
]

# ── Dangerous — warn + double-confirm ────────────────────────────────
DANGEROUS = [
    r"sudo\s+",
    r"chmod\s+[0-7]*7[0-7]*\s+/",
    r"chown\s+.*\s+/[a-z]",
    r"apt(-get)?\s+(remove|purge|autoremove)",
    r"dnf\s+remove", r"yum\s+remove", r"pacman\s+-R",
    r"systemctl\s+(stop|disable)\s+(ssh|network|firewall|ufw)",
    r"iptables\s+-F", r"ufw\s+disable",
    r"pkill\s+-9",
]

CRITICAL_PATHS = ["/boot", "/etc", "/usr", "/lib", "/sbin", "/bin",
                  "/sys", "/proc", "/dev", "/root"]


class SafetyGuard:
    def check(self, cmd: str) -> Tuple[bool, str]:
        for pattern, reason in BLOCKED:
            if re.search(pattern, cmd, re.IGNORECASE):
                return True, reason
        return False, ""

    def is_dangerous(self, cmd: str) -> bool:
        return any(re.search(p, cmd, re.IGNORECASE) for p in DANGEROUS)

    def touches_critical(self, cmd: str) -> bool:
        return any(p in cmd for p in CRITICAL_PATHS)

    def audit(self, cmd: str) -> dict:
        blocked, reason = self.check(cmd)
        return {
            "command":       cmd,
            "blocked":       blocked,
            "block_reason":  reason,
            "dangerous":     self.is_dangerous(cmd),
            "critical_path": self.touches_critical(cmd),
        }
