#!/usr/bin/env python3
"""
Terminus 2.0 — AI-powered Linux terminal assistant.

Uso:
  terminus                  → modo interativo
  terminus fix wifi         → diagnóstico directo
  terminus learn docker     → tutorial directo
  terminus scan             → saúde do sistema
  terminus setup            → configurar API e modelo
  terminus --version        → versão
"""

import sys
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

VERSION = "2.0.0"


def _check_python():
    if sys.version_info < (3, 8):
        print("ERRO: Python 3.8+ necessário.", file=sys.stderr)
        sys.exit(1)


def _check_deps() -> bool:
    try:
        import rich
        return True
    except ImportError:
        print("ERRO: Execute: pip install -r requirements.txt", file=sys.stderr)
        return False


def _print_help():
    print(f"""
Terminus {VERSION} — Assistente inteligente de terminal Linux

USO:
  terminus                  Modo interativo (REPL)
  terminus fix <problema>   Diagnosticar e resolver problema
  terminus learn <tema>     Tutorial prático sobre Linux
  terminus scan             Análise de saúde do sistema
  terminus setup            Configurar chave de API e modelo de IA

EXEMPLOS:
  terminus fix wifi
  terminus fix disco cheio
  terminus learn docker
  terminus learn git
  terminus scan
  terminus setup

OPÇÕES:
  --version   Versão actual
  --help      Esta ajuda
""")


def _run_oneshot(args: list) -> None:
    if not _check_deps():
        sys.exit(1)

    user_input = " ".join(args)

    from rich.console import Console
    from rich.spinner import Spinner
    from rich.live import Live
    from cli.layout import response_panel
    from cli.ui import TerminusUI

    console = Console(highlight=False)
    ui = TerminusUI()

    # Setup em modo interativo mesmo na linha de comando
    if args[0].lower() in ("setup", "config", "configurar"):
        from modules.setup import run_setup
        topic = " ".join(args[1:]) if len(args) > 1 else ""
        result = run_setup(topic=topic, ui=ui)
        if result:
            console.print(response_panel(result))
        return

    with Live(
        Spinner("dots", text=f"[bright_black]Processando: {user_input}[/bright_black]"),
        console=console, transient=True, refresh_per_second=12,
    ):
        response = ui.router.route(user_input, ui=ui)

    if response.get("type") == "scan":
        ui._render_scan(response)
    elif response:
        console.print(response_panel(response))


def main():
    _check_python()
    args = sys.argv[1:]

    if not args:
        if not _check_deps():
            sys.exit(1)
        from cli.ui import TerminusUI
        TerminusUI().run()
        return

    first = args[0].lower()

    if first in ("--version", "-v", "version"):
        print(f"Terminus {VERSION}")
        return

    if first in ("--help", "-h", "help", "ajuda"):
        _print_help()
        return

    _run_oneshot(args)


if __name__ == "__main__":
    main()
