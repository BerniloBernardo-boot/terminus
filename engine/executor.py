"""
engine/executor.py — Safe command executor.
Dry-run by default. Real execution requires explicit confirmation.
"""

import subprocess
import os
from typing import Dict

SAFE_READ = {
    "ls","cat","echo","pwd","whoami","id","date","df","du","free",
    "ps","uname","hostname","uptime","lsblk","lscpu","lsusb","lspci",
    "ip","ifconfig","ping","nslookup","dig","find","grep","awk",
    "sed","head","tail","wc","env","printenv","which","whereis",
    "file","stat","lsof","netstat","ss","top","htop",
}


class Executor:
    def dry_run(self, command: str) -> Dict:
        first = command.strip().split()[0].lstrip("$").lower() if command.strip() else ""
        if first in SAFE_READ or self._is_read_only(command):
            return self._run(command, label="[simulação — leitura segura]")
        return {
            "success": True,
            "output": (
                f"Simulação de: {command}\n\n"
                "→ Nenhuma mudança foi feita ainda.\n"
                "→ Este comando será executado no shell atual após confirmação."
            ),
        }

    def run(self, command: str) -> Dict:
        return self._run(command)

    def _run(self, command: str, label: str = "") -> Dict:
        # Bloquear subshell injection mesmo com shell=True
        # shell=True é necessário para suportar pipes e redirects legítimos
        # mas bloqueamos os padrões mais perigosos aqui também
        _SUBSHELL = ["$(", "`", "&&rm", "&&dd", "&&mkfs", ";rm", ";dd", ";mkfs"]
        for pattern in _SUBSHELL:
            if pattern in command.replace(" ", "").lower():
                return {
                    "success": False,
                    "output": f"Bloqueado: padrão de injecção detectado ({pattern})",
                    "code": -1
                }
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=30, env=os.environ.copy(),
            )
            out = (r.stdout + r.stderr).strip() or "(sem saída)"
            if label:
                out = f"{label}\n\n{out}"
            return {"success": r.returncode == 0, "output": out, "code": r.returncode}
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Tempo limite (30s) excedido.", "code": -1}
        except Exception as e:
            return {"success": False, "output": f"Erro: {e}", "code": -1}

    @staticmethod
    def _is_read_only(cmd: str) -> bool:
        prefixes = ("ls ","cat ","echo ","df ","du ","free ","ps ",
                    "ip addr","ip link","ifconfig","uname","uptime","id","whoami","pwd")
        return cmd.strip().lower().startswith(prefixes)
