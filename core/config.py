"""
core/config.py — Configuração global persistente do Terminus.

Prioridade:
  1. Variáveis de ambiente (máxima prioridade)
  2. terminus.conf (preferências do utilizador)
  3. DEFAULTS (fallback)

Providers suportados:
  gemini      → Google Gemini (grátis, recomendado)
  openrouter  → Acesso a múltiplos modelos
  anthropic   → Claude da Anthropic
  deepseek    → DeepSeek (barato e potente)
"""

import os
import json
from pathlib import Path

# Carregar .env
try:
    from dotenv import load_dotenv
    _home_env = Path.home() / ".terminus" / ".env"
    _local_env = Path(__file__).parent.parent / ".env"
    load_dotenv(_home_env)
    load_dotenv(_local_env)
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.parent
_TERMINUS_HOME = Path.home() / ".terminus"
_TERMINUS_HOME.mkdir(exist_ok=True)
CONF_FILE = _TERMINUS_HOME / "terminus.conf"

# Modelos disponíveis por provider
PROVIDER_MODELS = {
    "gemini": {
        "name": "Google Gemini",
        "key_env": "GEMINI_API_KEY",
        "url_key": "https://aistudio.google.com/app/apikey",
        "free": True,
        "models": [
            {"id": "gemini-2.0-flash",         "label": "Gemini 2.0 Flash (recomendado)", "free": True},
            {"id": "gemini-2.0-flash-lite",    "label": "Gemini 2.0 Flash Lite (leve)",  "free": True},
            {"id": "gemini-1.5-flash-latest",  "label": "Gemini 1.5 Flash Latest",       "free": True},
            {"id": "gemini-1.5-pro-latest",    "label": "Gemini 1.5 Pro (avançado)",     "free": False},
        ],
        "default_model": "gemini-2.0-flash",
    },
    "openrouter": {
        "name": "OpenRouter",
        "key_env": "OPENROUTER_API_KEY",
        "url_key": "https://openrouter.ai/keys",
        "free": False,
        "models": [
            {"id": "google/gemini-2.0-flash-exp:free",        "label": "Gemini 2.0 Flash (grátis)",    "free": True},
            {"id": "meta-llama/llama-3.3-70b-instruct:free",  "label": "Llama 3.3 70B (grátis)",       "free": True},
            {"id": "mistralai/mistral-7b-instruct:free",       "label": "Mistral 7B (grátis)",          "free": True},
            {"id": "deepseek/deepseek-chat:free",              "label": "DeepSeek Chat (grátis)",       "free": True},
            {"id": "openai/gpt-4o-mini",                       "label": "GPT-4o Mini (pago)",           "free": False},
            {"id": "anthropic/claude-3-haiku",                 "label": "Claude 3 Haiku (pago)",        "free": False},
            {"id": "google/gemini-flash-1.5",                  "label": "Gemini Flash 1.5 (pago)",      "free": False},
            {"id": "deepseek/deepseek-chat",                   "label": "DeepSeek Chat (pago)",         "free": False},
            {"id": "meta-llama/llama-3.1-70b-instruct",        "label": "Llama 3.1 70B (pago)",         "free": False},
        ],
        "default_model": "google/gemini-2.0-flash-exp:free",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "key_env": "ANTHROPIC_API_KEY",
        "url_key": "https://console.anthropic.com/keys",
        "free": False,
        "models": [
            {"id": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku (rápido, barato)",  "free": False},
            {"id": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (inteligente)",   "free": False},
            {"id": "claude-3-haiku-20240307",   "label": "Claude 3 Haiku (económico)",         "free": False},
        ],
        "default_model": "claude-3-5-haiku-20241022",
    },
    "deepseek": {
        "name": "DeepSeek",
        "key_env": "DEEPSEEK_API_KEY",
        "url_key": "https://platform.deepseek.com/api_keys",
        "free": False,
        "models": [
            {"id": "deepseek-chat",    "label": "DeepSeek Chat (recomendado)", "free": False},
            {"id": "deepseek-coder",   "label": "DeepSeek Coder (programação)", "free": False},
        ],
        "default_model": "deepseek-chat",
    },
}

DEFAULTS = {
    "ai_enabled":    True,
    "ai_provider":   "gemini",
    "ai_model":      "gemini-2.0-flash",
    "dry_run":       True,
    "confirm_always": True,
    "language":      "pt",
    "mode":          "beginner",
    "log_enabled":   True,
    "max_history":   500,
}


class Config:
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._data = DEFAULTS.copy()
            cls._inst._load()
        return cls._inst

    def _load(self):
        # Carregar terminus.conf (preferências persistentes)
        if CONF_FILE.exists():
            try:
                saved = json.loads(CONF_FILE.read_text())
                self._data.update(saved)
            except Exception:
                pass

        # Corrigir modelos inválidos do Gemini guardados em versões antigas
        _INVALID_GEMINI = {"gemini-2.0-flash-lite", "gemini-1.5-flash-001"}
        if (self._data.get("ai_provider") == "gemini"
                and self._data.get("ai_model") in _INVALID_GEMINI):
            self._data["ai_model"] = "gemini-1.5-flash"

        # Variáveis de ambiente sobrepõem tudo
        # Provider e chaves
        if os.environ.get("GEMINI_API_KEY"):
            self._data["gemini_key"] = os.environ["GEMINI_API_KEY"]
            if self._data.get("ai_provider") not in ("openrouter", "anthropic", "deepseek"):
                self._data["ai_provider"] = "gemini"

        if os.environ.get("OPENROUTER_API_KEY"):
            self._data["openrouter_key"] = os.environ["OPENROUTER_API_KEY"]

        if os.environ.get("ANTHROPIC_API_KEY"):
            self._data["anthropic_key"] = os.environ["ANTHROPIC_API_KEY"]

        if os.environ.get("DEEPSEEK_API_KEY"):
            self._data["deepseek_key"] = os.environ["DEEPSEEK_API_KEY"]

        if os.environ.get("OPENROUTER_MODEL"):
            self._data["ai_model"] = os.environ["OPENROUTER_MODEL"]

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        # Nunca guardar chaves de API via set() — usar save_key_to_env()
        _PROTECTED = {"gemini_key","openrouter_key","anthropic_key","deepseek_key"}
        if key in _PROTECTED:
            raise ValueError(f"Use save_key_to_env() para guardar chaves de API, não set('{key}')")
        self._data[key] = value

    def save(self) -> tuple:
        """Guarda preferências (sem chaves) no terminus.conf.
        Retorna (True, "") em sucesso ou (False, motivo) em falha."""
        try:
            # Nunca guardar chaves de API no terminus.conf
            _KEY_FIELDS = {"gemini_key","openrouter_key","anthropic_key","deepseek_key"}
            safe = {k: v for k, v in self._data.items() if k not in _KEY_FIELDS}
            CONF_FILE.write_text(json.dumps(safe, indent=2))
            return True, ""
        except PermissionError:
            return False, f"Sem permissão de escrita em {CONF_FILE}"
        except OSError as e:
            return False, f"Erro ao guardar configuração: {e}"

    def save_key_to_env(self, provider: str, key: str) -> bool:
        """Guarda a chave de API no ficheiro .env local e recarrega a config."""
        env_var = PROVIDER_MODELS[provider]["key_env"]
        env_path = BASE_DIR / ".env"
        # Também guardar em ~/.terminus/.env para instalação global
        home_env = Path.home() / ".terminus" / ".env"
        try:
            for target in [env_path, home_env]:
                if not target.parent.exists():
                    continue
                lines = target.read_text().splitlines() if target.exists() else []
                # Remover linha antiga e comentários da variável
                lines = [l for l in lines if not l.strip().startswith(f"{env_var}=")]
                lines.append(f"{env_var}={key}")
                target.write_text("\n".join(lines) + "\n")
            # Actualizar env actual em memória
            os.environ[env_var] = key
            # Guardar provider actual antes de recarregar (evita reversão)
            current_provider = self._data.get("ai_provider", "gemini")
            # Recarregar estado interno
            self._load()
            # Restaurar provider se foi alterado pelo _load()
            if self._data.get("ai_provider") != current_provider:
                self._data["ai_provider"] = current_provider
            return True
        except Exception:
            return False

    def set_provider(self, provider: str) -> None:
        self._data["ai_provider"] = provider
        # Definir modelo padrão do provider
        default = PROVIDER_MODELS.get(provider, {}).get("default_model", "")
        if default:
            self._data["ai_model"] = default

    def set_model(self, model: str) -> None:
        self._data["ai_model"] = model

    def has_ai(self) -> bool:
        provider = self._data.get("ai_provider", "gemini")
        key_map = {
            "gemini":     "gemini_key",
            "openrouter": "openrouter_key",
            "anthropic":  "anthropic_key",
            "deepseek":   "deepseek_key",
        }
        key_field = key_map.get(provider, "gemini_key")
        return bool(self._data.get(key_field))

    def get_active_key(self) -> str:
        provider = self._data.get("ai_provider", "gemini")
        key_map = {
            "gemini":     "gemini_key",
            "openrouter": "openrouter_key",
            "anthropic":  "anthropic_key",
            "deepseek":   "deepseek_key",
        }
        return self._data.get(key_map.get(provider, "gemini_key"), "")

    def status(self) -> dict:
        provider = self._data.get("ai_provider", "gemini")
        return {
            "ai_enabled":      self._data.get("ai_enabled"),
            "ai_provider":     provider,
            "provider_name":   PROVIDER_MODELS.get(provider, {}).get("name", provider),
            "ai_model":        self._data.get("ai_model"),
            "has_gemini":      bool(self._data.get("gemini_key")),
            "has_openrouter":  bool(self._data.get("openrouter_key")),
            "has_anthropic":   bool(self._data.get("anthropic_key")),
            "has_deepseek":    bool(self._data.get("deepseek_key")),
            "has_ai":          self.has_ai(),
            "mode":            self._data.get("mode"),
        }

    @staticmethod
    def providers() -> dict:
        return PROVIDER_MODELS
