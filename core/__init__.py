"""
core/__init__.py — Núcleo do sistema Terminus.
"""
from core.config  import Config
from core.context import SessionContext
from core.router  import Router

__all__ = ["Config", "SessionContext", "Router"]
