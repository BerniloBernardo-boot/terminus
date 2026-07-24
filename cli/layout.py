"""
cli/layout.py — Reusable Rich layout primitives for Terminus.
All visual blocks are built here; ui.py only calls these.
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.padding import Padding
from rich.rule import Rule
from rich.columns import Columns
from rich import box

from cli.theme import ICON, P


# ── Response panel ────────────────────────────────────────────────────

def response_panel(response: dict) -> Panel:
    """Build the main response Panel from a structured response dict."""
    rtype   = response.get("type", "info")
    title   = response.get("title", "")
    body    = response.get("body", "")
    steps   = response.get("steps", [])
    cmds    = response.get("commands", [])
    warning = response.get("warning", "")
    tip     = response.get("tip", "")
    ai_note = response.get("ai_note", "")

    content = Text()

    # Body paragraph
    if body:
        content.append(f"{body}\n", style=P.body)

    # Steps
    if steps:
        content.append("\n")
        for i, step in enumerate(steps, 1):
            label = step.get("label", "")
            desc  = step.get("description", "")
            cmd   = step.get("command", "")

            content.append(f"  [{i}] ", style=f"bold {P.warn}")
            content.append(f"{label}\n", style=f"bold {P.body}")
            if desc:
                content.append(f"      {desc}\n", style=P.muted)
            if cmd:
                content.append(f"      $ {cmd}\n", style=P.cmd)

    # Standalone commands
    if cmds:
        content.append("\n")
        for c in cmds:
            if isinstance(c, str):
                cmd_str, explain = c, ""
            else:
                cmd_str = c.get("cmd", "")
                explain = c.get("explain", "")
            content.append(f"  $ {cmd_str}\n", style=f"bold {P.cmd}")
            if explain:
                content.append(f"    {explain}\n", style=P.muted)

    # Warning
    if warning:
        content.append("\n")
        for line in warning.strip().split("\n"):
            content.append(f"  ⚠  {line}\n", style=P.warn)

    # Tip
    if tip:
        content.append(f"\n  󱠂  {tip}\n" if "󱠂" not in tip else f"\n  {tip}\n",
                       style=P.tip)

    # AI note
    if ai_note:
        content.append(f"\n  ✦ {ai_note}\n", style=P.ai)

    # Build title string with icon
    icon_map = {
        "learn": ICON.learn,  "fix": ICON.fix,   "scan": ICON.scan,
        "error": ICON.error,  "warn": ICON.warn,  "success": ICON.ok,
        "info":  ICON.info,   "ai":  ICON.ai,    "block": ICON.block,
    }
    icon = icon_map.get(rtype, ICON.info)
    panel_title = f"{icon}[bold white]{title}[/bold white]" if title else ""

    return Panel(
        content,
        title=panel_title,
        title_align="left",
        border_style=P.border(rtype),
        padding=(0, 2),
        box=box.ROUNDED,
    )


# ── Command preview block ─────────────────────────────────────────────

def command_preview(cmd: str, label: str = "Pré-visualização") -> Panel:
    """Render a shell command with syntax highlighting in a panel."""
    syntax = Syntax(f"$ {cmd}", "bash", theme="monokai",
                    background_color="default", word_wrap=True)
    return Panel(
        syntax,
        title=f"[yellow]{ICON.dryrun}[bold]{label}[/bold][/yellow]",
        title_align="left",
        border_style="yellow",
        padding=(0, 1),
        box=box.ROUNDED,
    )


# ── Confirm prompt ────────────────────────────────────────────────────

def confirm_text(question: str, dangerous: bool = False) -> Text:
    t = Text()
    if dangerous:
        t.append("  ⚠  OPERAÇÃO PERIGOSA  ", style=f"bold {P.err}")
        t.append("\n")
    t.append(f"  ? {question} ", style=f"bold {P.warn}")
    t.append("[s/y]", style=f"bold {P.ok}")
    t.append("/", style=P.muted)
    t.append("[N]", style=f"bold {P.err}")
    t.append(": ", style=P.muted)
    return t


# ── History table ─────────────────────────────────────────────────────

def history_table(entries: list) -> Table:
    t = Table(
        box=box.SIMPLE_HEAVY,
        border_style=P.muted,
        header_style=f"bold {P.sub}",
        show_lines=False,
        expand=True,
    )
    t.add_column("#",      style=P.muted,  width=4,  justify="right")
    t.add_column("Hora",   style=P.muted,  width=10)
    t.add_column("Módulo", style=P.cmd,    width=8)
    t.add_column("Input",  style=P.body)

    for i, e in enumerate(entries, 1):
        mod = e.get("module", "")
        mod_colors = {
            "learn": f"[cyan]{mod}[/cyan]",
            "fix":   f"[yellow]{mod}[/yellow]",
            "scan":  f"[green]{mod}[/green]",
            "ai":    f"[magenta]{mod}[/magenta]",
        }
        mod_display = mod_colors.get(mod, f"[bright_black]{mod}[/bright_black]")
        t.add_row(str(i), e.get("time", ""), mod_display, e.get("input", ""))
    return t


# ── Scan health table ─────────────────────────────────────────────────

def scan_table(checks: list) -> Table:
    t = Table(
        box=box.SIMPLE_HEAVY,
        border_style="green",
        header_style="bold green",
        show_lines=False,
        expand=True,
        padding=(0, 1),
    )
    t.add_column("Componente", style="bold white", min_width=22)
    t.add_column("Status",     style="white",      min_width=38)
    t.add_column("Ação",       style=P.cmd,        min_width=16)

    for check in checks:
        label   = check.get("label", "")
        desc    = check.get("description", "")
        cmd     = check.get("command", "") or "-"
        t.add_row(label, desc, cmd)
    return t


# ── Rule / separator ──────────────────────────────────────────────────

def section_rule(text: str = "", style: str = "bright_black") -> Rule:
    return Rule(text, style=style, align="left")


# ── Help table ────────────────────────────────────────────────────────

def help_table() -> Table:
    t = Table(
        box=box.SIMPLE,
        border_style=P.muted,
        show_header=False,
        padding=(0, 2),
    )
    t.add_column("cmd",  style=f"bold {P.ok}",   min_width=22)
    t.add_column("desc", style=P.body)

    rows = [
        ("help",                    "Mostra esta ajuda"),
        ("learn <tema>",            "Aula prática (ex: learn permissões)"),
        ("fix <problema>",          "Solução guiada (ex: fix disco cheio)"),
        ("scan",                    "Análise de saúde do sistema"),
        ("history",                 "Histórico da sessão"),
        ("clear",                   "Limpa a tela"),
        ("exit / quit",             "Sair do Terminus"),
        ("setup",                   "Configurar chave de API e modelo de IA"),
        ("setup status",            "Ver configuração actual"),
        ("setup test",              "Testar ligação à IA"),
        ("",                        ""),
        ("<linguagem natural>",      "Descreva o problema livremente"),
    ]
    for cmd, desc in rows:
        t.add_row(cmd, desc)
    return t
