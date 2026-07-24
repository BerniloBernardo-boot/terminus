"""
modules/setup/__init__.py — Assistente de configuração interativo.

Comandos:
  setup          → menu principal
  setup status   → ver configuração actual
  setup test     → testar ligação à IA
"""

from __future__ import annotations
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.ui import TerminusUI


def run_setup(topic: str = "", ui: "TerminusUI" = None) -> dict:
    """Ponto de entrada do módulo setup."""
    topic = (topic or "").strip().lower()
    if topic in ("status", "ver", "show"):
        return _show_status()
    if topic in ("test", "teste", "testar"):
        return _test_connection(ui)
    # Menu interativo
    return _interactive_setup(ui)


def _show_status() -> dict:
    from core.config import Config, PROVIDER_MODELS
    cfg = Config()
    st = cfg.status()

    provider = cfg.get("ai_provider", "gemini")  # Usar cfg directo
    model    = cfg.get("ai_model", "gemini-2.0-flash")  # Usar cfg directo
    pname    = st["provider_name"]
    has_ai   = st["has_ai"]

    lines = []
    lines.append(f"Provider activo : {pname}")
    lines.append(f"Modelo          : {model}")
    lines.append(f"IA disponível   : {'Sim ✓' if has_ai else 'Não — sem chave configurada'}")
    lines.append("")
    lines.append("Chaves configuradas:")
    for pid, pdata in PROVIDER_MODELS.items():
        key_env = pdata["key_env"]
        has = bool(os.environ.get(key_env) or cfg.get(pid + "_key"))
        icon = "✓" if has else "✗"
        lines.append(f"  {icon}  {pdata['name']}")

    tip = ""
    if not has_ai:
        tip = "Execute 'setup' para configurar uma chave de API."
    else:
        tip = "Execute 'setup' para alterar provider ou modelo."

    return {
        "type":    "info",
        "title":   "Estado da Configuração",
        "body":    "\n".join(lines),
        "steps":   [],
        "tip":     tip,
        "warning": "",
    }


def _test_connection(ui) -> dict:
    from core.config import Config
    from engine.ai import AIEngine

    cfg = Config()
    if not cfg.has_ai():
        return {
            "type":    "error",
            "title":   "Sem chave de API configurada",
            "body":    "Execute 'setup' para adicionar uma chave de API.",
            "steps":   [],
            "tip":     "setup",
            "warning": "",
        }

    if ui:
        ui.console.print("  [bright_black]A testar ligação à IA...[/bright_black]")

    try:
        result = AIEngine().interpret("Responde apenas: OK")
        if result and result.get("type") != "error":
            provider = cfg.status()["provider_name"]
            model    = cfg.get("ai_model", "")
            return {
                "type":    "info",
                "title":   "Ligação com sucesso!",
                "body":    f"Provider: {provider}\nModelo: {model}\n\nA IA está funcionando correctamente.",
                "steps":   [],
                "tip":     "Pode agora fazer qualquer pergunta sobre Linux.",
                "warning": "",
            }
        else:
            return {
                "type":    "error",
                "title":   "Falha na ligação",
                "body":    result.get("body", "Erro desconhecido."),
                "steps":   [],
                "tip":     "Verifique a chave em 'setup'.",
                "warning": "",
            }
    except Exception as e:
        return {
            "type":    "error",
            "title":   "Erro ao testar",
            "body":    str(e),
            "steps":   [],
            "tip":     "setup",
            "warning": "",
        }


def _interactive_setup(ui) -> dict:
    """Menu interativo de configuração — roda no terminal."""
    if not ui:
        return _show_status()

    console = ui.console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from core.config import Config, PROVIDER_MODELS

    cfg = Config()

    while True:
        # ── Menu principal ────────────────────────────────────────
        console.print()
        console.print(Panel(
            _menu_table(),
            title="[bold cyan]⚙  Configuração do Terminus[/bold cyan]",
            title_align="left",
            border_style="cyan",
            padding=(0, 2),
            box=box.ROUNDED,
        ))

        try:
            choice = input("  Escolha [1-5] ou Enter para sair: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            break

        if not choice or choice == "0":
            break

        if choice == "1":
            _setup_provider(console, cfg)
        elif choice == "2":
            _setup_model(console, cfg)
        elif choice == "3":
            result = _show_status()
            console.print(f"\n  {result['body']}\n")
        elif choice == "4":
            result = _test_connection(ui)
            from cli.layout import response_panel
            console.print(response_panel(result))
        elif choice == "5":
            _clear_config(console, cfg)
        else:
            console.print("  [yellow]Opção inválida.[/yellow]")

    return {
        "type":  "info",
        "title": "Configuração concluída",
        "body":  _config_summary(cfg),
        "steps": [],
        "tip":   "Execute 'setup status' para ver o estado a qualquer momento.",
        "warning": "",
    }


def _menu_table():
    from rich.table import Table
    from rich import box
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column("n",    style="bold cyan",       width=4)
    t.add_column("cmd",  style="bold white",      width=28)
    t.add_column("desc", style="bright_black")
    rows = [
        ("1", "Adicionar / Alterar chave de API", "Configurar provider (Gemini, OpenRouter, etc.)"),
        ("2", "Escolher modelo de IA",            "Trocar o modelo dentro do provider activo"),
        ("3", "Ver configuração actual",           "Estado das chaves e provider"),
        ("4", "Testar ligação à IA",              "Verificar se a chave funciona"),
        ("5", "Limpar configuração",              "Remover provider e modelo guardados"),
    ]
    for n, c, d in rows:
        t.add_row(n, c, d)
    return t


def _setup_provider(console, cfg):
    from core.config import PROVIDER_MODELS
    import os

    console.print("\n  [bold]Escolha o provider de IA:[/bold]\n")
    providers = list(PROVIDER_MODELS.items())
    for i, (pid, pdata) in enumerate(providers, 1):
        has_key = bool(os.environ.get(pdata["key_env"]) or cfg.get(pid + "_key"))
        status  = "[green](chave configurada)[/green]" if has_key else "[bright_black](sem chave)[/bright_black]"
        free    = "[cyan]grátis[/cyan]" if pdata["free"] else "[yellow]pago[/yellow]"
        console.print(f"  [{i}] [bold]{pdata['name']}[/bold]  {free}  {status}")
        console.print(f"      Chave em: [bright_black]{pdata['url_key']}[/bright_black]")
        console.print()

    try:
        choice = input("  Escolha [1-{}] ou Enter para cancelar: ".format(len(providers))).strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not choice:
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(providers):
            raise ValueError
    except ValueError:
        console.print("  [yellow]Opção inválida.[/yellow]")
        return

    pid, pdata = providers[idx]

    # Pedir a chave
    console.print(f"\n  [bold]Configurar {pdata['name']}[/bold]")
    console.print(f"  Obter chave: [cyan]{pdata['url_key']}[/cyan]\n")

    try:
        key = input(f"  Cole a chave {pdata['key_env']}= ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not key:
        console.print("  [yellow]Nenhuma chave inserida.[/yellow]")
        return

    # Guardar
    ok = cfg.save_key_to_env(pid, key)
    cfg.set_provider(pid)
    cfg.save()[0]

    if ok:
        console.print(f"\n  [green]✓[/green]  Chave guardada no ficheiro .env")
        console.print(f"  [green]✓[/green]  Provider activo: [bold]{pdata['name']}[/bold]")
        console.print(f"  [green]✓[/green]  Modelo: [cyan]{cfg.get('ai_model')}[/cyan]\n")
        # Mostrar selecção de modelo
        _setup_model(console, cfg)
    else:
        console.print("  [red]Erro ao guardar a chave.[/red]")
        console.print(f"  Adicione manualmente ao ficheiro .env:\n  [cyan]{pdata['key_env']}={key}[/cyan]")


def _setup_model(console, cfg):
    from core.config import PROVIDER_MODELS

    provider = cfg.get("ai_provider", "gemini")
    pdata    = PROVIDER_MODELS.get(provider, {})
    models   = pdata.get("models", [])

    if not models:
        console.print(f"  [yellow]Nenhum modelo disponível para {provider}.[/yellow]")
        return

    console.print(f"\n  [bold]Modelos disponíveis — {pdata.get('name', provider)}:[/bold]\n")

    free_models = [m for m in models if m["free"]]
    paid_models = [m for m in models if not m["free"]]

    idx = 1
    model_list = []

    if free_models:
        console.print("  [cyan]GRÁTIS:[/cyan]")
        for m in free_models:
            current = " [green]← actual[/green]" if m["id"] == cfg.get("ai_model") else ""
            console.print(f"    [{idx}] {m['label']}{current}")
            console.print(f"        [bright_black]{m['id']}[/bright_black]")
            model_list.append(m["id"])
            idx += 1

    if paid_models:
        console.print("\n  [yellow]PAGO:[/yellow]")
        for m in paid_models:
            current = " [green]← actual[/green]" if m["id"] == cfg.get("ai_model") else ""
            console.print(f"    [{idx}] {m['label']}{current}")
            console.print(f"        [bright_black]{m['id']}[/bright_black]")
            model_list.append(m["id"])
            idx += 1

    console.print(f"\n    [{idx}] Personalizado (escrever o nome)")
    console.print()

    try:
        choice = input(f"  Escolha [1-{idx}] ou Enter para manter actual: ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if not choice:
        return

    try:
        c = int(choice)
        if c == idx:
            try:
                custom = input("  Nome do modelo: ").strip()
            except (KeyboardInterrupt, EOFError):
                return
            if custom:
                cfg.set_model(custom)
                cfg.save()[0]
                console.print(f"\n  [green]✓[/green]  Modelo configurado: [cyan]{custom}[/cyan]\n")
        elif 1 <= c < idx:
            chosen = model_list[c - 1]
            cfg.set_model(chosen)
            cfg.save()[0]
            console.print(f"\n  [green]✓[/green]  Modelo configurado: [cyan]{chosen}[/cyan]\n")
        else:
            raise ValueError
    except (ValueError, IndexError):
        console.print("  [yellow]Opção inválida.[/yellow]")


def _clear_config(console, cfg):
    try:
        confirm = input("  Limpar configuração de provider e modelo? [s/N]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return

    if confirm not in ("s", "y", "sim", "yes"):
        return

    from core.config import DEFAULTS, CONF_FILE
    cfg.set("ai_provider", DEFAULTS["ai_provider"])
    cfg.set("ai_model",    DEFAULTS["ai_model"])
    cfg.save()[0]
    # Remover terminus.conf se existir
    if CONF_FILE.exists():
        CONF_FILE.unlink()
    console.print("  [green]✓[/green]  Configuração de provider/modelo limpa.")
    console.print("  As chaves de API no ficheiro .env foram mantidas.\n")


def _config_summary(cfg) -> str:
    from core.config import PROVIDER_MODELS
    provider = cfg.get("ai_provider", "gemini")
    pname    = PROVIDER_MODELS.get(provider, {}).get("name", provider)
    model    = cfg.get("ai_model", "")
    has_ai   = cfg.has_ai()
    status   = "activa" if has_ai else "sem chave de API"
    return f"Provider: {pname}  ·  Modelo: {model}  ·  IA: {status}"
