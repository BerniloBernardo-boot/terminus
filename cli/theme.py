"""
cli/theme.py — Nerd Fonts detection, icon sets, and color palette.
Falls back to clean ASCII if Nerd Fonts are unavailable.
"""

import os
import subprocess
from dataclasses import dataclass


# ── Nerd Fonts detection ──────────────────────────────────────────────

def _detect_nerd_fonts() -> bool:
    # Manual override via env var
    env = os.environ.get("TERMINUS_ICONS", "").lower()
    if env in ("1", "true", "yes"):
        return True
    if env in ("0", "false", "no"):
        return False

    # Terminals known to support Nerd Fonts out of the box
    nerd_terminals = {
        os.environ.get("KITTY_WINDOW_ID"),
        os.environ.get("WEZTERM_PANE"),
        os.environ.get("ALACRITTY_SOCKET"),
    }
    if any(v for v in nerd_terminals):
        return True

    # Check installed fonts via fc-list
    try:
        out = subprocess.run(
            ["fc-list"], capture_output=True, text=True, timeout=3
        ).stdout
        markers = ["NerdFont", "Nerd Font", "Hack Nerd", "FiraCode Nerd",
                   "JetBrainsMono Nerd", "MesloLGS NF", "Iosevka Nerd"]
        if any(m in out for m in markers):
            return True
    except Exception:
        pass

    return False


NERD_FONTS: bool = _detect_nerd_fonts()


# ── Icon sets ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Icons:
    ok: str;      warn: str;    error: str;   info: str
    learn: str;   fix: str;     scan: str;    ai: str
    exec_: str;   block: str;   dryrun: str
    arrow: str;   bullet: str;  step: str;    cmd: str
    tip: str;     history: str; plugin: str
    cpu: str;     ram: str;     disk: str;    net: str
    service: str; boot: str;    update: str;  root: str


ICONS_NERD = Icons(
    ok="[green] [/green]",      warn="[yellow] [/yellow]",
    error="[red] [/red]",       info="[cyan]󰋽 [/cyan]",
    learn="[cyan]󰈸 [/cyan]",    fix="[yellow]󰣪 [/yellow]",
    scan="[green]󰍉 [/green]",   ai="[magenta]󱜚 [/magenta]",
    exec_="[cyan]󰆍 [/cyan]",    block="[red]󱗆 [/red]",
    dryrun="[yellow]󱋱 [/yellow]",
    arrow="[cyan] [/cyan]",     bullet="[bright_black]󰧟 [/bright_black]",
    step="[yellow]󰑊 [/yellow]", cmd="[green] [/green]",
    tip="[magenta]󱠂 [/magenta]", history="[cyan]󰋚 [/cyan]",
    plugin="[blue]󰏗 [/blue]",
    cpu="[cyan]󰻟[/cyan]",       ram="[blue]󰍛[/blue]",
    disk="[yellow]󰋊[/yellow]",  net="[green]󰈀[/green]",
    service="[cyan]󱁉[/cyan]",   boot="[bright_black]󰓙[/bright_black]",
    update="[blue]󰚰[/blue]",    root="[red]󰘊[/red]",
)

ICONS_ASCII = Icons(
    ok="[green][OK][/green]",        warn="[yellow][!!][/yellow]",
    error="[red][XX][/red]",         info="[cyan][ii][/cyan]",
    learn="[cyan][>>][/cyan]",       fix="[yellow][##][/yellow]",
    scan="[green][..][/green]",      ai="[magenta][AI][/magenta]",
    exec_="[cyan][$>][/cyan]",       block="[red][--][/red]",
    dryrun="[yellow][DR][/yellow]",
    arrow="[cyan]->[/cyan]",         bullet="[bright_black]*[/bright_black]",
    step="[yellow]->[/yellow]",      cmd="[green]$[/green]",
    tip="[magenta]>>[/magenta]",     history="[cyan][H][/cyan]",
    plugin="[blue][P][/blue]",
    cpu="[cyan]CPU[/cyan]",          ram="[blue]RAM[/blue]",
    disk="[yellow]DSK[/yellow]",     net="[green]NET[/green]",
    service="[cyan]SVC[/cyan]",      boot="[bright_black]BT[/bright_black]",
    update="[blue]UP[/blue]",        root="[red]RT[/red]",
)

ICON = ICONS_NERD if NERD_FONTS else ICONS_ASCII


# ── Color palette ─────────────────────────────────────────────────────

class P:
    """Canonical color tokens used throughout the UI."""
    ok       = "bright_green"
    warn     = "yellow"
    err      = "bright_red"
    info     = "bright_cyan"
    muted    = "bright_black"
    title    = "bold white"
    sub      = "bold cyan"
    cmd      = "cyan"
    body     = "white"
    tip      = "magenta"
    ai       = "magenta"

    # Panel border colors by response type
    BORDERS = {
        "learn":   "cyan",
        "fix":     "yellow",
        "scan":    "green",
        "error":   "red",
        "warn":    "yellow",
        "success": "bright_green",
        "info":    "bright_cyan",
        "ai":      "magenta",
        "block":   "red",
    }

    @classmethod
    def border(cls, rtype: str) -> str:
        return cls.BORDERS.get(rtype, "bright_black")
