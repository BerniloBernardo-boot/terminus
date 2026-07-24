"""
engine/ai.py — Motor de IA multi-provider.

Providers suportados:
  1. Google Gemini    (grátis, principal)
  2. Anthropic Claude (pago, poderoso)
  3. OpenRouter       (modelo configurável)
  4. DeepSeek         (barato e potente)

Lógica de fallback:
  - Tenta o provider activo primeiro
  - Se falhar (erro, 429, timeout), tenta os outros providers
  - Só mostra erro ao utilizador quando TODOS falharam
  - Nunca bloqueia o utilizador com retries desnecessários
"""

import json
import os
import urllib.request
import urllib.error

SYSTEM_PROMPT = """\
Você é o Terminus — um assistente Linux experiente e professor paciente.

REGRAS:
1. Responda SEMPRE em português
2. Explique O QUÊ e POR QUÊ, não só o comando
3. Se a pergunta for vaga, peça mais detalhes (type: "question")
4. Nunca sugira comandos destrutivos sem aviso claro

FORMATO — retorne APENAS JSON válido, sem markdown:
{
  "type": "fix" | "learn" | "info" | "question",
  "title": "Título curto",
  "body": "Explicação principal",
  "steps": [
    {"label": "Nome do passo", "description": "O que faz e por quê", "command": "comando"}
  ],
  "warning": "Aviso de segurança ou string vazia",
  "tip": "Dica extra ou string vazia",
  "followup": "Pergunta de follow-up ou string vazia"
}
"""


def _is_answer(r: object) -> bool:
    """
    Retorna True APENAS para respostas reais da IA.
    Dicts de erro (type="error") retornam False para
    permitir que o fallback chain continue.
    """
    return (
        isinstance(r, dict)
        and bool(r.get("body", "").strip())
        and len(r.get("body", "")) > 10
        and r.get("type") not in (None, "error")
    )


def _is_rate_limit(r: object) -> bool:
    """Identifica especificamente erros de rate limit."""
    return (
        isinstance(r, dict)
        and r.get("type") == "error"
        and r.get("_error_code") == 429
    )


class AIEngine:
    def __init__(self, api_key: str = "", openrouter_key: str = ""):
        from core.config import Config
        self._cfg = Config()
        self._provider   = self._cfg.get("ai_provider", "gemini")
        self._model      = self._cfg.get("ai_model", "gemini-2.0-flash")

        # Chaves de todos os providers
        self._gemini_key     = self._cfg.get("gemini_key", "")     or os.environ.get("GEMINI_API_KEY", "")
        self._openrouter_key = openrouter_key or self._cfg.get("openrouter_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
        self._anthropic_key  = self._cfg.get("anthropic_key", "")  or os.environ.get("ANTHROPIC_API_KEY", "")
        self._deepseek_key   = self._cfg.get("deepseek_key", "")   or os.environ.get("DEEPSEEK_API_KEY", "")

    def interpret(self, query: str, history: list = None) -> dict:
        """
        Tenta obter resposta da IA com fallback automático entre providers.
        Só retorna erro quando TODOS os providers falharam.
        """
        history = history or []
        last_error = {}

        # Ordem de tentativa: provider activo + fallbacks
        plan = self._build_plan(query, history)

        for pid, key, fn in plan:
            if not key:
                continue
            result = fn()

            if _is_answer(result):
                return result  # ✓ resposta real

            # Guardar o último erro para mostrar se tudo falhar
            if isinstance(result, dict) and result.get("type") == "error":
                last_error = result
                # Rate limit: tentar próximo provider imediatamente
                # (não bloquear o utilizador com sleep)
                if _is_rate_limit(result):
                    continue
                # Erro de autenticação: não tentar de novo com mesmo provider
                if result.get("_error_code") in (401, 403):
                    continue

        # Todos os providers falharam
        if last_error:
            return self._format_final_error(last_error)

        return self._err(
            "IA indisponível",
            "Nenhum provider de IA respondeu.\n\n"
            "Verifique:\n"
            "  1. Conexão com internet\n"
            "  2. Chave de API válida: setup → opção 4 (testar)\n\n"
            "O Terminus continua offline: fix · learn · scan",
            "setup test",
        )

    def _build_plan(self, query: str, history: list) -> list:
        """
        Constrói a ordem de tentativas: provider activo primeiro,
        depois os outros por ordem de custo (grátis antes de pago).
        """
        all_providers = [
            ("gemini",     self._gemini_key,     lambda: self._try_gemini(query, history)),
            ("openrouter", self._openrouter_key, lambda: self._try_openrouter(query, history, self._model if self._provider == "openrouter" else "google/gemini-2.0-flash-exp:free")),
            ("deepseek",   self._deepseek_key,   lambda: self._try_deepseek(query, history)),
            ("anthropic",  self._anthropic_key,  lambda: self._try_anthropic(query, history)),
        ]
        # Provider activo vai primeiro
        active = [(pid, key, fn) for pid, key, fn in all_providers if pid == self._provider]
        others = [(pid, key, fn) for pid, key, fn in all_providers if pid != self._provider]
        return active + others

    # ── Google Gemini (REST directo, sem google-genai) ─────────────
    def _try_gemini(self, query: str, history: list) -> dict:
        if not self._gemini_key:
            return {}
        models_to_try = [
            self._model if self._provider == "gemini" else "gemini-2.0-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash",
        ]
        # Remover duplicados mantendo ordem
        seen = set()
        models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

        for model in models_to_try:
            result = self._gemini_request(query, history, model)
            if _is_answer(result):
                return result
            # 404 → tentar próximo modelo
            if result.get("_error_code") == 404:
                continue
            # Qualquer outro resultado (incluindo 429) → retornar
            return result

        return self._err("Gemini indisponível", "Todos os modelos Gemini falharam.")

    def _gemini_request(self, query: str, history: list, model: str) -> dict:
        """Faz uma chamada REST ao Gemini e retorna o resultado."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self._gemini_key}"
        )
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": query}]})

        payload = json.dumps({
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500},
        }).encode()

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())

            candidates = data.get("candidates", [])
            if not candidates:
                return self._err(
                    "Resposta filtrada",
                    "O Gemini bloqueou esta resposta por políticas de segurança.\n"
                    "Reformule a pergunta.",
                    "Tente: fix <problema> ou learn <tema>",
                )
            try:
                text = candidates[0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError):
                return {}
            return self._parse(text, query, source=f"gemini/{model}")

        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "Gemini")
        except urllib.error.URLError:
            return self._err("Sem internet", "Verifique sua conexão.", "", code=0)
        except Exception:
            return {}

    # ── OpenRouter ─────────────────────────────────────────────────
    def _try_openrouter(self, query: str, history: list, model: str) -> dict:
        if not self._openrouter_key:
            return {}
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        payload = json.dumps({
            "model":       model,
            "messages":    messages,
            "max_tokens":  1200,
            "temperature": 0.4,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._openrouter_key}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/terminus2",
                "X-Title":       "Terminus2",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
            if "error" in data:
                msg = data["error"].get("message", "Erro desconhecido")
                return self._err("OpenRouter", msg)
            text = data["choices"][0]["message"]["content"].strip()
            return self._parse(text, query, source=f"openrouter/{model}")
        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "OpenRouter")
        except Exception:
            return {}

    # ── Anthropic Claude ───────────────────────────────────────────
    def _try_anthropic(self, query: str, history: list) -> dict:
        if not self._anthropic_key:
            return {}
        model = self._model if self._provider == "anthropic" else "claude-3-5-haiku-20241022"
        messages = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        payload = json.dumps({
            "model":      model,
            "max_tokens": 1500,
            "system":     SYSTEM_PROMPT,
            "messages":   messages,
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key":         self._anthropic_key,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
            text = data["content"][0]["text"].strip()
            return self._parse(text, query, source="anthropic")
        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "Anthropic")
        except Exception:
            return {}

    # ── DeepSeek ───────────────────────────────────────────────────
    def _try_deepseek(self, query: str, history: list) -> dict:
        if not self._deepseek_key:
            return {}
        model = self._model if self._provider == "deepseek" else "deepseek-chat"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        payload = json.dumps({
            "model":       model,
            "messages":    messages,
            "max_tokens":  1200,
            "temperature": 0.4,
        }).encode()

        req = urllib.request.Request(
            "https://api.deepseek.com/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._deepseek_key}",
                "Content-Type":  "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
            text = data["choices"][0]["message"]["content"].strip()
            return self._parse(text, query, source="deepseek")
        except urllib.error.HTTPError as e:
            return self._handle_http_error(e, "DeepSeek")
        except Exception:
            return {}

    # ── Error handling central ─────────────────────────────────────
    def _handle_http_error(self, e: urllib.error.HTTPError, provider: str) -> dict:
        """Trata erros HTTP de forma consistente para todos os providers."""
        try:
            body = json.loads(e.read().decode())
            msg  = (body.get("error", {}) or {}).get("message", "") or str(e)
        except Exception:
            msg = str(e)

        if e.code == 401 or e.code == 403:
            return self._err(
                f"Chave {provider} inválida",
                f"A chave foi rejeitada.\n\nVerifica e reconfigura em: setup → opção 1",
                "setup",
                code=e.code,
            )
        if e.code == 429:
            return self._err(
                f"{provider}: limite de requisições",
                f"Atingiste o limite do plano grátis ({provider}).\n"
                f"O Terminus vai tentar outro provider automaticamente.",
                "",
                code=429,
            )
        if e.code == 404:
            return self._err(
                f"Modelo não encontrado ({provider})",
                f"O modelo configurado não existe.\n\nExecuta: setup → opção 2",
                "setup → opção 2",
                code=404,
            )
        if e.code >= 500:
            return self._err(
                f"{provider}: erro do servidor",
                f"O servidor do {provider} está com problemas (HTTP {e.code}).\n"
                f"Tenta novamente em alguns minutos.",
                "",
                code=e.code,
            )
        return self._err(f"Erro {provider}", f"HTTP {e.code}: {msg}", "", code=e.code)

    def _format_final_error(self, last_error: dict) -> dict:
        """Formata o erro final quando todos os providers falharam."""
        code = last_error.get("_error_code", 0)
        if code == 429:
            return {
                "type":    "error",
                "title":   "Limite de requisições atingido",
                "body":    (
                    "Atingiste o limite do plano grátis da API.\n\n"
                    "Opções:\n"
                    "  1. Aguarda 1 minuto e tenta novamente\n"
                    "  2. Muda para modelo mais leve: setup → opção 2\n"
                    "  3. Adiciona outro provider: setup → opção 1\n\n"
                    "Enquanto isso, o Terminus funciona offline:\n"
                    "  fix wifi · fix disco cheio · learn docker · scan"
                ),
                "steps":   [],
                "warning": "",
                "tip":     "setup → opção 1",
                "followup": "",
            }
        if code in (401, 403):
            return {
                "type":    "error",
                "title":   "Chave de API inválida",
                "body":    "A chave configurada foi rejeitada pelo provider.\n\nExecuta: setup → opção 1 → reconfigura a chave.",
                "steps":   [],
                "warning": "",
                "tip":     "setup",
                "followup": "",
            }
        return last_error

    # ── Parser de resposta ─────────────────────────────────────────
    def _parse(self, raw: str, query: str, source: str = "ai") -> dict:
        # Remover blocos markdown se existirem
        if "```" in raw:
            lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
            raw = "\n".join(lines).strip()

        data = None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            s = raw.find("{")
            e = raw.rfind("}") + 1
            if s != -1 and e > s:
                try:
                    data = json.loads(raw[s:e])
                except Exception:
                    pass

        if not data:
            # Resposta em texto simples — aceitar como "info"
            return {
                "type": "info", "title": query[:60], "body": raw,
                "steps": [], "warning": "", "tip": "", "followup": "",
                "_source": source,
            }

        # Normalizar steps
        data["steps"] = [
            {
                "label":       s.get("label", s.get("title", "")),
                "description": s.get("description", ""),
                "command":     s.get("command", ""),
            }
            for s in data.get("steps", [])
            if isinstance(s, dict)
        ]
        data.setdefault("warning", "")
        data.setdefault("tip", "")
        data.setdefault("followup", "")
        data["_source"] = source
        return data

    @staticmethod
    def _err(title: str, body: str, tip: str = "", code: int = 0) -> dict:
        return {
            "type":        "error",
            "title":       title,
            "body":        body,
            "steps":       [],
            "warning":     "",
            "tip":         tip or "Use: fix <problema> ou learn <tema>",
            "followup":    "",
            "_error_code": code,
        }
