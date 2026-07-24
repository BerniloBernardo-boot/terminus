"""
cli/ui.py — Terminus 2.0 main REPL.
Owns the input loop, rendering pipeline, and user confirmations.
"""

import sys
import os

try:
    import readline
    readline.parse_and_bind("tab: complete")
    readline.set_history_length(500)
except Exception:
    pass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from rich.padding import Padding
from rich import box

from cli.theme import ICON, P, NERD_FONTS
from cli.layout import (
    response_panel, command_preview, confirm_text,
    history_table, help_table, section_rule
)
from core.router import Router
from core.context import SessionContext
from utils.os_detect import OSDetector

VERSION = "2.0.0"

BANNER = r"""[bold cyan]
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗
  ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝[/bold cyan]"""


class TerminusUI:
    def __init__(self):
        self.console   = Console(highlight=False)
        self.ctx       = SessionContext()
        self.router    = Router(self.ctx)
        self.os_info   = OSDetector().detect()

    # ── Banner ────────────────────────────────────────────────────────
    def _print_banner(self):
        self.console.print(BANNER)

        os_str  = f"{self.os_info.get('distro','Linux')} {self.os_info.get('version','')}".strip()
        pm      = self.os_info.get("pkg_manager", "apt")
        is_root = self.os_info.get("is_root", False)
        is_wsl  = self.os_info.get("is_wsl", False)

        tags = [
            f"[bright_black]v{VERSION}[/bright_black]",
            f"[green]{os_str}[/green]",
            f"[cyan]{pm}[/cyan]",
        ]
        if is_wsl:
            tags.append("[yellow]WSL[/yellow]")
        if NERD_FONTS:
            tags.append("[bright_black]Nerd Fonts[/bright_black]")
        if is_root:
            tags.append(f"[bold red]{ICON.root} root[/bold red]")

        self.console.print("  " + "  ·  ".join(tags))
        self.console.print(
            f"  [bright_black]Digite [/bright_black][bold green]help[/bold green]"
            f"[bright_black] para começar — ou descreva seu problema livremente.[/bright_black]\n"
        )

    # ── Help panel ────────────────────────────────────────────────────
    def _print_help(self):
        self.console.print(Panel(
            help_table(),
            title=f"[bold cyan]{ICON.info} Terminus — Comandos[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(0, 1),
            box=box.ROUNDED,
        ))

    # ── Spinner while processing ──────────────────────────────────────
    def _with_spinner(self, label: str, fn, *args, **kwargs):
        with Live(
            Spinner("dots", text=f"[bright_black]{label}[/bright_black]"),
            console=self.console,
            transient=True,
            refresh_per_second=12,
        ):
            return fn(*args, **kwargs)

    # ── Render a full response dict ───────────────────────────────────
    def _render(self, response: dict):
        # Special render for scan (uses table layout)
        if response.get("type") == "scan":
            self._render_scan(response)
            return

        self.console.print(response_panel(response))

    def _render_scan(self, response: dict):
        from cli.layout import scan_table
        checks  = response.get("steps", [])
        warning = response.get("warning", "")
        tip     = response.get("tip", "")

        self.console.print(Panel(
            scan_table(checks),
            title=f"[bold green]{ICON.scan} Saúde do Sistema[/bold green]",
            title_align="left",
            border_style="green",
            padding=(0, 1),
            box=box.ROUNDED,
        ))
        if warning:
            for line in warning.strip().split("\n"):
                self.console.print(f"  [yellow]{ICON.warn}{line}[/yellow]")
        if tip:
            self.console.print(f"  [magenta]{ICON.tip} {tip}[/magenta]")
        self.console.print()

    # ── Confirmation prompts ──────────────────────────────────────────
    def confirm(self, question: str, dangerous: bool = False) -> bool:
        self.console.print(confirm_text(question, dangerous), end="")
        try:
            ans = input().strip().lower()
            return ans in ("s", "y", "sim", "yes")
        except (KeyboardInterrupt, EOFError):
            return False

    def confirm_double(self, question: str) -> bool:
        if not self.confirm(question, dangerous=True):
            return False
        self.console.print(f"  [bold red]Confirme uma segunda vez:[/bold red] ", end="")
        try:
            return input().strip().lower() in ("s", "y", "sim", "yes")
        except (KeyboardInterrupt, EOFError):
            return False

    # ── Execution flow (called by router when needed) ─────────────────
    def run_command_flow(self, command: str, is_dangerous: bool = False) -> dict:
        """Show dry-run → confirm → execute. Returns result dict."""
        from engine.executor import Executor
        executor = Executor()

        # Step 1 — dry run preview
        dry = executor.dry_run(command)
        self.console.print(command_preview(command, "Simulação (nenhuma mudança)"))
        if dry.get("output"):
            self.console.print(
                Panel(
                    f"[bright_black]{dry['output']}[/bright_black]",
                    border_style="bright_black",
                    padding=(0, 2),
                    box=box.ROUNDED,
                )
            )

        # Step 2 — confirm
        confirmed = (self.confirm_double if is_dangerous else self.confirm)(
            f"Executar: [cyan]{command}[/cyan]"
        )

        if not confirmed:
            return {
                "type":  "info",
                "title": "Execução cancelada",
                "body":  "Nenhum comando foi executado. Isso é seguro.",
            }

        # Step 3 — execute
        with self._spinner_ctx("Executando..."):
            result = executor.run(command)

        return {
            "type":  "success" if result.get("success") else "error",
            "title": "Resultado",
            "body":  result.get("output", ""),
        }

    def _spinner_ctx(self, label: str):
        return Live(
            Spinner("dots", text=f"[bright_black]{label}[/bright_black]"),
            console=self.console,
            transient=True,
            refresh_per_second=12,
        )

    # ── History view ──────────────────────────────────────────────────
    def _show_history(self):
        entries = self.ctx.get_history()
        if not entries:
            self.console.print(
                f"  [bright_black]{ICON.info} Nenhuma interação ainda nesta sessão.[/bright_black]\n"
            )
            return
        self.console.print(Panel(
            history_table(entries),
            title=f"[bold cyan]{ICON.history} Histórico da sessão[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(0, 1),
            box=box.ROUNDED,
        ))

    # ── Main REPL loop ────────────────────────────────────────────────
    def run(self):
        self._print_banner()

        while True:
            try:
                raw = input(self._prompt()).strip()
            except (KeyboardInterrupt, EOFError):
                self.console.print(f"\n  [bright_black]Até logo![/bright_black]\n")
                break

            if not raw:
                continue

            cmd = raw.lower().strip()

            # ── Built-in commands ────────────────────────────────────
            if cmd in ("exit", "quit", "sair"):
                self.console.print(f"\n  [bright_black]Encerrando Terminus.[/bright_black]\n")
                break

            if cmd == "clear":
                self.console.clear()
                self._print_banner()
                continue

            if cmd in ("help", "ajuda", "?"):
                self._print_help()
                continue

            if cmd == "history":
                self._show_history()
                continue

            # ── Setup / Config ───────────────────────────────────────
            _first = cmd.split()[0] if cmd.split() else ""
            if _first in ("setup", "config", "configurar", "api"):
                from modules.setup import run_setup
                parts = raw.strip().split(maxsplit=1)
                topic = parts[1] if len(parts) > 1 else ""
                self.ctx.add_input(raw)  # L1: registar no histórico
                result = run_setup(topic=topic, ui=self)
                if result:
                    self._render(result)
                    self.ctx.add_response(result)
                continue

            # ── Route to engine ──────────────────────────────────────
            self.ctx.add_input(raw)
            response = self._with_spinner(
                "Processando...", self.router.route, raw, ui=self
            )
            if response:
                self._render(response)
                self.ctx.add_response(response)

    def _prompt(self) -> str:
        # Rich markup can't go inside input(), so we print it before
        from rich.text import Text
        t = Text()
        t.append("terminus", style="bold green")
        t.append("❯ ", style="bright_black")
        self.console.print(t, end="")
        return ""
