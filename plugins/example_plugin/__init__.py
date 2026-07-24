"""
plugins/example_plugin/__init__.py — Plugin de exemplo.
Copie esta pasta e adapte para criar seu próprio plugin.
"""

PLUGIN_META = {
    "name":        "example-plugin",
    "version":     "1.0.0",
    "description": "Plugin de demonstração — remova ou adapte",
    "author":      "terminus2",
    "commands":    ["exemplo"],
}


def register(router) -> None:
    """Chamado automaticamente pelo PluginLoader ao carregar."""
    # Exemplo: registrar handler de comando
    # router.register_plugin("exemplo", _handle_exemplo)
    pass


def _handle_exemplo(topic: str) -> dict:
    return {
        "type":  "info",
        "title": "Plugin de Exemplo",
        "body":  "Este é um plugin de demonstração.\nSubstitua pela sua lógica.",
        "tip":   "Consulte plugins/loader.py para a estrutura completa.",
    }
