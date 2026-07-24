"""
utils/os_detect.py — Linux distro and environment detection.
"""

import os
import platform
from pathlib import Path
from functools import lru_cache
import shutil


class OSDetector:
    def detect(self) -> dict:
        """Detecta o sistema operativo. Resultado é cacheado na instância."""
        if hasattr(self, "_cache"): return self._cache
        info = {
            "distro":      "Linux",
            "version":     "",
            "pkg_manager": "apt",
            "init":        "systemd",
            "arch":        platform.machine(),
            "kernel":      platform.release(),
            "desktop":     os.environ.get("XDG_CURRENT_DESKTOP", ""),
            "is_root":     os.geteuid() == 0,
            "is_wsl":      self._is_wsl(),
        }
        rel = self._os_release()
        if rel:
            info["distro"]      = rel.get("NAME", "Linux").strip('"')
            info["version"]     = rel.get("VERSION_ID", "").strip('"')
            info["pkg_manager"] = self._pkg_manager(rel.get("ID", "").lower())
        info["init"] = self._init_system()
        self._cache = info
        return info

    @staticmethod
    def _os_release() -> dict:
        for p in ("/etc/os-release", "/usr/lib/os-release"):
            if Path(p).exists():
                out = {}
                for line in Path(p).read_text().splitlines():
                    if "=" in line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        out[k] = v.strip('"')
                return out
        return {}

    @staticmethod
    def _pkg_manager(distro_id: str) -> str:
        m = {
            "ubuntu":"apt","debian":"apt","mint":"apt","pop":"apt",
            "elementary":"apt","kali":"apt","parrot":"apt",
            "fedora":"dnf","rhel":"dnf","centos":"dnf","rocky":"dnf","alma":"dnf",
            "arch":"pacman","manjaro":"pacman","endeavouros":"pacman","garuda":"pacman",
            "opensuse":"zypper","suse":"zypper",
            "alpine":"apk","void":"xbps","gentoo":"emerge",
        }
        for k, v in m.items():
            if k in distro_id:
                return v
        return "apt"

    @staticmethod
    def _init_system() -> str:
        if Path("/run/systemd/private").exists():
            return "systemd"
        if Path("/sbin/openrc").exists():
            return "openrc"
        return "sysv"

    @staticmethod
    def _is_wsl() -> bool:
        try:
            return "microsoft" in Path("/proc/version").read_text().lower()
        except Exception:
            return False

    def install_cmd(self, pkg: str) -> str:
        pm = self.detect()["pkg_manager"]
        cmds = {
            "apt":    f"sudo apt install -y {pkg}",
            "dnf":    f"sudo dnf install -y {pkg}",
            "pacman": f"sudo pacman -S --noconfirm {pkg}",
            "zypper": f"sudo zypper install -y {pkg}",
            "apk":    f"sudo apk add {pkg}",
        }
        return cmds.get(pm, f"sudo apt install -y {pkg}")
