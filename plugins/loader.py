"""
plugins/loader.py — Sistema de plugins extensível.

Permite adicionar comandos e módulos sem alterar o core.

Estrutura de um plugin (plugins/meu_plugin/):
  __init__.py   → define PLUGIN_META e register(router)
  *.py          → lógica do plugin

Exemplo de plugin:
  PLUGIN_META = {
      "name":        "meu-plugin",
      "version":     "1.0.0",
      "description": "Descrição do plugin",
      "author":      "nome",
      "commands":    ["meu-comando"],
  }

  def register(router):
      # Adicionar handler ao router
      router.register_plugin("meu-comando", handler_func)
"""

import importlib
import sys
from pathlib import Path
from typing import Callable

PLUGINS_DIR = Path(__file__).parent


class PluginLoader:
    """
    Carregador de plugins com detecção automática.
    Carrega plugins da pasta plugins/ sem configuração manual.
    """

    def __init__(self):
        self._loaded:   dict[str, dict]     = {}
        self._failed:   dict[str, str]      = {}
        self._handlers: dict[str, Callable] = {}

    def load_all(self) -> dict:
        """
        Descobre e carrega todos os plugins válidos.
        Retorna sumário: {loaded: [...], failed: [...]}
        """
        for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
            # Ignorar arquivos e pastas do sistema
            if not plugin_dir.is_dir():
                continue
            if plugin_dir.name.startswith(("_", ".")):
                continue
            init = plugin_dir / "__init__.py"
            if not init.exists():
                continue
            self._load_one(plugin_dir)

        return {
            "loaded": list(self._loaded.keys()),
            "failed": list(self._failed.keys()),
            "count":  len(self._loaded),
        }

    def _load_one(self, plugin_dir: Path) -> None:
        name = plugin_dir.name
        module_path = f"plugins.{name}"
        try:
            # Adicionar path ao sys.path se necessário
            root = PLUGINS_DIR.parent
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))

            mod = importlib.import_module(module_path)

            # Validar estrutura mínima
            meta = getattr(mod, "PLUGIN_META", None)
            if not meta or not isinstance(meta, dict):
                self._failed[name] = "PLUGIN_META ausente ou inválido"
                return

            if not meta.get("name") or not meta.get("version"):
                self._failed[name] = "PLUGIN_META incompleto (name/version obrigatórios)"
                return

            self._loaded[name] = {
                "meta":   meta,
                "module": mod,
            }

        except ImportError as e:
            self._failed[name] = f"ImportError: {e}"
        except Exception as e:
            self._failed[name] = f"Erro ao carregar: {e}"

    def register_all(self, router) -> None:
        """Registra handlers de todos os plugins carregados no router."""
        for name, entry in self._loaded.items():
            mod = entry["module"]
            register_fn = getattr(mod, "register", None)
            if callable(register_fn):
                try:
                    register_fn(router)
                except Exception as e:
                    self._failed[name] = f"Erro no register(): {e}"
                    del self._loaded[name]

    def register_handler(self, command: str, fn: Callable) -> None:
        """Registra handler de plugin para um comando específico."""
        self._handlers[command.lower()] = fn

    def handle(self, command: str, *args, **kwargs):
        """Despacha comando para handler de plugin, se existir."""
        fn = self._handlers.get(command.lower())
        if fn:
            return fn(*args, **kwargs)
        return None

    def has_command(self, command: str) -> bool:
        return command.lower() in self._handlers

    @property
    def loaded(self) -> dict:
        return dict(self._loaded)

    @property
    def failed(self) -> dict:
        return dict(self._failed)

    def status_report(self) -> str:
        """Retorna relatório de status dos plugins para debug."""
        lines = [f"Plugins carregados: {len(self._loaded)}"]
        for name, entry in self._loaded.items():
            meta = entry["meta"]
            lines.append(f"  ✓ {meta['name']} v{meta['version']} — {meta.get('description', '')}")
        if self._failed:
            lines.append(f"\nPlugins com erro: {len(self._failed)}")
            for name, err in self._failed.items():
                lines.append(f"  ✗ {name}: {err}")
        return "\n".join(lines)


# Instância global reutilizável
loader = PluginLoader()
