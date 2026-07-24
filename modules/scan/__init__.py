"""
modules/scan/__init__.py — Expõe a API pública do módulo scan.

Uso correto após esta correção:
    from modules.scan import run_scan
    from modules.scan import scanner  # ainda funciona (retrocompatível)
"""

from modules.scan.scanner import run_scan

__all__ = ["run_scan", "scanner"]
