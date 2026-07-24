"""
plugins/__init__.py — Expõe o loader de plugins.
"""
from plugins.loader import loader, PluginLoader

__all__ = ["loader", "PluginLoader"]
