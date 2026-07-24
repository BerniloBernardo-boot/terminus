"""
modules/fix/__init__.py — FixModule
Camada rica sobre o Solver engine.

Pipeline:
  1. engine/solver (problems.json)
  2. base de fixes contextuais internos (keyword map)
  3. AI engine (se configurado)
  4. fallback inteligente por categoria (nunca vazio)
"""

from __future__ import annotations
from engine.solver import Solver
from core.config   import Config

# ── Mapa contextual de problemas → categoria ────────────────────────
# Quando solver e AI falham, retorna guia específico por palavra-chave
_CONTEXT_MAP: dict[str, dict] = {
    "tela_preta": {
        "keywords": ["tela preta", "tela escura", "black screen", "não aparece nada",
                     "monitor apagado", "sem imagem", "sem vídeo"],
        "title": "Tela Preta — Diagnóstico",
        "body":  (
            "Tela preta geralmente indica problema no servidor gráfico (Xorg/Wayland), "
            "driver de GPU ou no display manager."
        ),
        "steps": [
            {"label": "Mudar para TTY",         "description": "Aceder ao terminal sem interface gráfica",  "command": "Ctrl+Alt+F2  (ou F3, F4)"},
            {"label": "Ver logs do Xorg",        "description": "Identificar erro no servidor gráfico",      "command": "cat /var/log/Xorg.0.log | grep EE"},
            {"label": "Reiniciar display manager","description": "Pode resolver travamento do login",        "command": "sudo systemctl restart gdm  # ou sddm, lightdm"},
            {"label": "Ver driver GPU",          "description": "Verificar driver instalado",                "command": "lspci -k | grep -A2 VGA"},
            {"label": "Reinstalar driver NVIDIA","description": "Se usar GPU NVIDIA",                        "command": "sudo ubuntu-drivers autoinstall"},
            {"label": "Modo recovery",           "description": "Boot em modo de recuperação",               "command": "Reinicie → segure Shift → escolha recovery mode"},
        ],
        "tip":     "Ctrl+Alt+F7 ou F1 volta para o ambiente gráfico.",
        "warning": "Não force desligar o PC com tela preta — use o TTY para diagnóstico.",
    },
    "wifi": {
        "keywords": ["wifi", "wi-fi", "sem internet", "internet caiu", "rede caiu",
                     "não conecta", "sem conexão", "network", "sem rede"],
        "title": "Wi-Fi / Rede — Diagnóstico",
        "body":  (
            "Problemas de rede geralmente são: interface desativada, DNS mal configurado, "
            "driver ausente ou credenciais incorretas."
        ),
        "steps": [
            {"label": "Ver interfaces",          "description": "Listar adaptadores de rede",                "command": "ip link show"},
            {"label": "Status do NetworkManager","description": "Serviço de rede do sistema",                "command": "systemctl status NetworkManager"},
            {"label": "Listar redes Wi-Fi",      "description": "Escanear redes disponíveis",               "command": "nmcli dev wifi list"},
            {"label": "Reconectar à rede",       "description": "Conectar por linha de comando",             "command": "nmcli dev wifi connect 'NOME_REDE' password 'SENHA'"},
            {"label": "Testar conectividade",    "description": "Ping para servidor público",                "command": "ping -c 4 8.8.8.8"},
            {"label": "Testar DNS",              "description": "Resolução de nomes",                        "command": "nslookup google.com"},
            {"label": "Reiniciar rede",          "description": "Reinicializar NetworkManager",              "command": "sudo systemctl restart NetworkManager"},
        ],
        "tip":     "Se ping 8.8.8.8 funciona mas DNS falha, edite /etc/resolv.conf.",
        "warning": "Nunca edite /etc/network/interfaces se usar NetworkManager.",
    },
    "disco_cheio": {
        "keywords": ["disco cheio", "sem espaço", "no space left", "disk full",
                     "espaço", "storage", "partição cheia", "armazenamento"],
        "title": "Disco Cheio — Limpeza Segura",
        "body":  (
            "Disco cheio bloqueia o sistema. Priorize: cache do APT, logs antigos e "
            "arquivos temporários — são sempre seguros de remover."
        ),
        "steps": [
            {"label": "Ver uso por partição",    "description": "Percentual usado em cada disco",    "command": "df -h"},
            {"label": "Top 10 diretórios grandes","description": "Identificar onde está o problema",  "command": "sudo du -sh /* 2>/dev/null | sort -rh | head -10"},
            {"label": "Limpar cache do APT",     "description": "Pacotes baixados e não usados",      "command": "sudo apt clean"},
            {"label": "Remover pacotes órfãos",  "description": "Dependências não mais necessárias",  "command": "sudo apt autoremove"},
            {"label": "Limpar logs do journald", "description": "Manter apenas últimos 7 dias",       "command": "sudo journalctl --vacuum-time=7d"},
            {"label": "Limpar /tmp",             "description": "Arquivos temporários",               "command": "sudo rm -rf /tmp/* 2>/dev/null"},
            {"label": "Limpar thumbnails",       "description": "Cache de miniaturas do usuário",     "command": "rm -rf ~/.cache/thumbnails/*"},
        ],
        "tip":     "ncdu é uma ferramenta visual excelente: sudo apt install ncdu && ncdu /",
        "warning": "Nunca remova arquivos sem identificar o que são primeiro.",
    },
    "sistema_lento": {
        "keywords": ["lento", "devagar", "travando", "lag", "congelando",
                     "cpu alta", "ram cheia", "pesado", "slow"],
        "title": "Sistema Lento — Diagnóstico de Performance",
        "body":  (
            "Sistema lento geralmente tem causa identificável: processo consumindo CPU/RAM, "
            "swap excessivo, disco cheio ou serviço em loop."
        ),
        "steps": [
            {"label": "Ver processos pesados",   "description": "Top por CPU em tempo real",          "command": "top  (ou htop se instalado)"},
            {"label": "Verificar RAM",           "description": "Uso atual de memória",               "command": "free -h"},
            {"label": "Verificar swap",          "description": "Swap excessivo indica RAM esgotada", "command": "swapon --show"},
            {"label": "Ver load average",        "description": "Carga do sistema",                   "command": "uptime"},
            {"label": "Processos por RAM",       "description": "Ordenar por consumo de memória",     "command": "ps aux --sort=-%mem | head -10"},
            {"label": "Matar processo travado",  "description": "Encerrar processo pelo PID",         "command": "kill -9 <PID>"},
            {"label": "Verificar disco",         "description": "I/O de disco pode causar lentidão",  "command": "iostat -x 1 3  # requer sysstat"},
        ],
        "tip":     "Instale htop: sudo apt install htop — visualização muito melhor que top.",
        "warning": "Nunca mate processos do sistema (kworker, systemd, etc.).",
    },
    "permissoes": {
        "keywords": ["permission denied", "permissão negada", "permissão", "permission",
                     "acesso negado", "chmod", "chown", "cannot access"],
        "title": "Erro de Permissões — Diagnóstico",
        "body":  (
            "'Permission denied' significa que o utilizador não tem direito de leitura, "
            "escrita ou execução no arquivo ou diretório."
        ),
        "steps": [
            {"label": "Ver permissões do arquivo","description": "Listar com detalhes",                "command": "ls -la /caminho/arquivo"},
            {"label": "Ver utilizador atual",     "description": "Quem está logado",                   "command": "whoami && id"},
            {"label": "Ver dono do arquivo",      "description": "Owner e grupo",                      "command": "stat /caminho/arquivo"},
            {"label": "Dar permissão de leitura", "description": "Todos podem ler",                    "command": "chmod 644 arquivo"},
            {"label": "Dar permissão de execução","description": "Tornar executável",                  "command": "chmod +x script.sh"},
            {"label": "Mudar proprietário",       "description": "Transferir dono do arquivo",         "command": "sudo chown usuario:grupo arquivo"},
            {"label": "Permissão de diretório",   "description": "Acessar e listar pasta",             "command": "chmod 755 diretório"},
        ],
        "tip":     "Use 'sudo' apenas quando realmente necessário — não como atalho.",
        "warning": "Nunca use chmod 777 — remove toda segurança do arquivo.",
    },
    "servico_parado": {
        "keywords": ["serviço parado", "service failed", "serviço falhou", "service down",
                     "daemon", "não inicia", "crashed", "service stopped"],
        "title": "Serviço com Falha — Diagnóstico",
        "body":  (
            "Serviços falham por: configuração inválida, porta ocupada, "
            "dependência ausente ou arquivo de log cheio."
        ),
        "steps": [
            {"label": "Ver status detalhado",    "description": "Diagnóstico completo do serviço",   "command": "sudo systemctl status nome-servico"},
            {"label": "Ver logs do serviço",     "description": "Últimas 50 linhas de log",           "command": "journalctl -u nome-servico -n 50"},
            {"label": "Tentar iniciar",          "description": "Iniciar serviço manualmente",        "command": "sudo systemctl start nome-servico"},
            {"label": "Ver porta em uso",        "description": "Checar conflito de porta",           "command": "sudo ss -tlnp | grep :80"},
            {"label": "Verificar configuração",  "description": "Sintaxe do arquivo de config",       "command": "sudo nginx -t  # adapte para seu serviço"},
            {"label": "Listar serviços falhos",  "description": "Todos os que falharam",              "command": "systemctl list-units --failed"},
        ],
        "tip":     "'journalctl -xe' mostra os erros mais recentes com contexto completo.",
        "warning": "Identifique a causa antes de reiniciar — reiniciar não resolve config errada.",
    },
    "ssh": {
        "keywords": ["ssh", "connection refused", "refused", "ssh timeout",
                     "acesso remoto", "remote", "connection reset"],
        "title": "SSH — Diagnóstico de Conexão",
        "body":  (
            "Falhas SSH geralmente são: serviço parado, porta bloqueada, "
            "chave incorreta ou firewall bloqueando."
        ),
        "steps": [
            {"label": "Testar conectividade",    "description": "Verificar se host responde",         "command": "ping -c 4 servidor"},
            {"label": "Verificar porta SSH",     "description": "Testar se porta 22 está aberta",     "command": "nc -zv servidor 22"},
            {"label": "Conectar com debug",      "description": "Ver mensagens de erro detalhadas",   "command": "ssh -v usuario@servidor"},
            {"label": "Verificar chave",         "description": "Permissões corretas da chave",       "command": "ls -la ~/.ssh/"},
            {"label": "Corrigir permissão chave","description": "SSH exige permissão 600 na chave",   "command": "chmod 600 ~/.ssh/id_rsa"},
            {"label": "Status do sshd",          "description": "Serviço SSH no servidor remoto",     "command": "sudo systemctl status sshd"},
        ],
        "tip":     "Use 'ssh -i chave.pem usuario@host' para especificar chave manualmente.",
        "warning": "Nunca compartilhe sua chave privada (~/.ssh/id_rsa).",
    },
}


def _is_valid(r: object) -> bool:
    """Resposta válida: dict com body não vazio e tipo não-error."""
    return (
        isinstance(r, dict)
        and bool(r.get("body", "").strip())
        and r.get("type") != "error"
    )


def _score_context(query: str) -> dict | None:
    """Encontra contexto mais relevante por keywords."""
    q = query.lower()
    best_key, best_score = None, 0
    for key, data in _CONTEXT_MAP.items():
        score = sum(1 for kw in data["keywords"] if kw in q)
        if score > best_score:
            best_key, best_score = key, score
    if best_score >= 1 and best_key:
        return _CONTEXT_MAP[best_key]
    return None


class FixModule:
    """
    Módulo de resolução de problemas com pipeline de 4 níveis.
    Garante que SEMPRE retorna orientação útil e contextual.
    """

    def __init__(self):
        self._solver = Solver()
        self._cfg    = Config()

    def fix(self, topic: str) -> dict:
        # Nível 1 — solver local (problems.json)
        result = self._solver.solve(topic)
        if _is_valid(result):
            return result

        # Nível 2 — mapa contextual interno
        ctx = _score_context(topic)
        if ctx:
            return self._fmt_context(ctx)

        # Nível 3 — AI engine (se configurado)
        ai_result = self._try_ai(topic)
        if _is_valid(ai_result):
            return ai_result

        # Nível 4 — fallback inteligente por keyword (nunca vazio)
        return self._smart_fallback(topic)

    def _fmt_context(self, ctx: dict) -> dict:
        return {
            "type":    "fix",
            "title":   ctx["title"],
            "body":    ctx["body"],
            "steps":   ctx.get("steps", []),
            "tip":     ctx.get("tip", ""),
            "warning": ctx.get("warning", ""),
        }

    def _try_ai(self, topic: str) -> dict | None:
        if not self._cfg.get("ai_enabled", True):
            return None
        api_key = self._cfg.get_active_key()
        if not api_key:
            return None
        try:
            from engine.ai import AIEngine
            result = AIEngine(api_key).interpret(f"como resolver: {topic}")
            if isinstance(result, dict) and result.get("type") != "error":
                result["type"] = "fix"
                return result
        except Exception:
            pass
        return None

    def _smart_fallback(self, topic: str) -> dict:
        # Sugerir categoria mais próxima por substring
        q = topic.lower()
        sugestoes = []
        pairs = [
            ("tela", "fix tela preta"),
            ("wifi", "fix wifi"),
            ("rede", "fix wifi"),
            ("disco", "fix disco cheio"),
            ("espaço", "fix disco cheio"),
            ("lento", "fix sistema lento"),
            ("permissão", "fix permissão negada"),
            ("serviço", "fix serviço parado"),
            ("service", "fix serviço parado"),
            ("ssh", "fix ssh"),
        ]
        for kw, cmd in pairs:
            if kw in q:
                sugestoes.append(cmd)

        sugestao_txt = ""
        if sugestoes:
            sugestao_txt = "\n\nComandos sugeridos:\n" + "\n".join(f"  {s}" for s in sugestoes[:3])

        return {
            "type":  "info",
            "title": f"Sem solução específica para: {topic}",
            "body":  (
                f"Não encontrei solução local para '{topic}'.{sugestao_txt}\n\n"
                "Problemas com solução local:\n"
                "  fix tela preta    · fix wifi           · fix disco cheio\n"
                "  fix sistema lento · fix permissão      · fix serviço parado\n"
                "  fix ssh           · fix pacote quebrado · fix boot\n\n"
                "Para qualquer outro problema, ative a IA (grátis):"
            ),
            "tip":     "export GEMINI_API_KEY='AIza...'  →  aistudio.google.com/app/apikey",
            "warning": "",
        }
