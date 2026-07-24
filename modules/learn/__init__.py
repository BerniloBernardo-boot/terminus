"""
modules/learn/__init__.py — LearnModule
Camada rica sobre o Tutor engine.

Pipeline:
  1. engine/tutor (base local)
  2. base estendida interna (10+ tópicos novos)
  3. AI engine (se configurado)
  4. fallback contextual (nunca vazio)
"""

from __future__ import annotations
from engine.tutor import Tutor
from core.config  import Config

# ── Base de tópicos estendida ───────────────────────────────────────
_EXTENDED_HINTS: dict[str, dict] = {
    "docker": {
        "body": "Docker isola aplicações em containers leves e portáteis. Cada container tem seu próprio filesystem, processos e rede.",
        "steps": [
            {"label": "Listar containers",     "description": "Ver containers em execução",         "command": "docker ps"},
            {"label": "Listar imagens",         "description": "Ver imagens disponíveis localmente", "command": "docker images"},
            {"label": "Rodar container",        "description": "Executar imagem interativa",         "command": "docker run -it ubuntu bash"},
            {"label": "Parar container",        "description": "Parar pelo ID ou nome",              "command": "docker stop <id>"},
            {"label": "Remover container",      "description": "Liberar espaço",                     "command": "docker rm <id>"},
            {"label": "Ver logs",               "description": "Inspecionar saída do container",      "command": "docker logs <id>"},
        ],
        "tip":     "Use 'docker compose' para orquestrar múltiplos serviços.",
        "warning": "Containers são efêmeros — dados não persistem sem volumes.",
    },
    "git": {
        "body": "Git rastreia mudanças no código permitindo colaboração, histórico e reversão de qualquer alteração.",
        "steps": [
            {"label": "Iniciar repositório", "description": "Criar repositório local",          "command": "git init"},
            {"label": "Ver status",          "description": "Arquivos modificados/pendentes",    "command": "git status"},
            {"label": "Adicionar arquivos",  "description": "Preparar para commit",              "command": "git add ."},
            {"label": "Criar commit",        "description": "Salvar snapshot do projeto",        "command": "git commit -m 'mensagem'"},
            {"label": "Ver histórico",       "description": "Log compacto de commits",           "command": "git log --oneline"},
            {"label": "Criar branch",        "description": "Trabalhar em feature isolada",      "command": "git checkout -b nome-branch"},
            {"label": "Enviar para remoto",  "description": "Publicar no GitHub/GitLab",         "command": "git push origin main"},
        ],
        "tip":     "Use 'git stash' para guardar mudanças temporariamente.",
        "warning": "Nunca force push em branches compartilhadas com outras pessoas.",
    },
    "bash": {
        "body": "Bash é o shell padrão do Linux — interpreta comandos interativos e scripts de automação.",
        "steps": [
            {"label": "Criar script",       "description": "Arquivo executável",               "command": "touch script.sh && chmod +x script.sh"},
            {"label": "Shebang",            "description": "Primeira linha obrigatória",        "command": "#!/bin/bash"},
            {"label": "Variáveis",          "description": "Declarar e usar variáveis",         "command": 'NOME="valor" && echo $NOME'},
            {"label": "Condicional",        "description": "Bloco if/else básico",              "command": "if [ -f arquivo ]; then echo existe; fi"},
            {"label": "Loop for",           "description": "Iterar sobre lista",                "command": "for i in 1 2 3; do echo $i; done"},
            {"label": "Executar script",    "description": "Rodar arquivo criado",              "command": "bash script.sh"},
        ],
        "tip":     "Use 'shellcheck script.sh' para validar sintaxe do script.",
        "warning": 'Aspas importam! Use "$VAR" para evitar word splitting.',
    },
    "vim": {
        "body": "Vim é um editor modal com modos distintos para navegar, editar e executar comandos.",
        "steps": [
            {"label": "Abrir arquivo",     "description": "Entrar no Vim",                    "command": "vim arquivo.txt"},
            {"label": "Modo inserção",     "description": "Começar a digitar",                "command": "i  (pressione a tecla i)"},
            {"label": "Voltar ao normal",  "description": "Sair do modo inserção",            "command": "ESC"},
            {"label": "Salvar",            "description": "Gravar alterações",                "command": ":w"},
            {"label": "Salvar e sair",     "description": "Gravar e fechar",                  "command": ":wq"},
            {"label": "Sair sem salvar",   "description": "Descartar mudanças",               "command": ":q!"},
            {"label": "Buscar texto",      "description": "Pesquisa no arquivo",              "command": "/texto  (Enter para confirmar)"},
        ],
        "tip":     "Use 'vimtutor' no terminal para o tutorial oficial interativo.",
        "warning": "Pressione ESC antes de qualquer comando — sempre.",
    },
    "python": {
        "body": "Python é uma linguagem versátil com ecosistema rico. Sempre use ambientes virtuais para isolar dependências.",
        "steps": [
            {"label": "Criar virtualenv",    "description": "Ambiente isolado de pacotes",     "command": "python3 -m venv .venv"},
            {"label": "Ativar virtualenv",   "description": "Usar o ambiente criado",          "command": "source .venv/bin/activate"},
            {"label": "Instalar pacote",     "description": "Adicionar dependência",           "command": "pip install requests"},
            {"label": "Listar pacotes",      "description": "Ver instalados no ambiente",      "command": "pip list"},
            {"label": "Salvar dependências", "description": "Exportar requirements",           "command": "pip freeze > requirements.txt"},
            {"label": "Executar script",     "description": "Rodar arquivo Python",            "command": "python3 script.py"},
        ],
        "tip":     "Sempre use virtualenv — nunca instale pacotes globalmente com sudo pip.",
        "warning": "Python 2 está descontinuado. Use sempre python3.",
    },
    "systemd": {
        "body": "Systemd gerencia serviços, processos de boot e logs centralizados do sistema.",
        "steps": [
            {"label": "Status de serviço",   "description": "Ver estado atual",               "command": "systemctl status nginx"},
            {"label": "Iniciar serviço",     "description": "Ativar serviço agora",            "command": "sudo systemctl start nginx"},
            {"label": "Parar serviço",       "description": "Desativar serviço",               "command": "sudo systemctl stop nginx"},
            {"label": "Reiniciar serviço",   "description": "Parar e iniciar",                 "command": "sudo systemctl restart nginx"},
            {"label": "Habilitar no boot",   "description": "Iniciar automaticamente",         "command": "sudo systemctl enable nginx"},
            {"label": "Ver logs",            "description": "Journalctl filtrado",             "command": "journalctl -u nginx -n 50"},
            {"label": "Listar serviços",     "description": "Todos serviços ativos",           "command": "systemctl list-units --type=service"},
        ],
        "tip":     "Use 'journalctl -xe' para ver erros recentes do sistema.",
        "warning": "Reiniciar serviços críticos pode interromper conexões ativas.",
    },
    "firewall": {
        "body": "UFW simplifica a gestão de regras iptables para controlar tráfego de entrada e saída.",
        "steps": [
            {"label": "Status do firewall",  "description": "Ver regras ativas",              "command": "sudo ufw status verbose"},
            {"label": "Ativar firewall",      "description": "Habilitar proteção",             "command": "sudo ufw enable"},
            {"label": "Liberar SSH",          "description": "Permitir acesso remoto",         "command": "sudo ufw allow 22"},
            {"label": "Liberar HTTP",         "description": "Permitir tráfego web",           "command": "sudo ufw allow 80"},
            {"label": "Liberar HTTPS",        "description": "Permitir tráfego seguro",        "command": "sudo ufw allow 443"},
            {"label": "Bloquear IP",          "description": "Negar acesso de endereço",       "command": "sudo ufw deny from 1.2.3.4"},
        ],
        "tip":     "Libere a porta 22 ANTES de ativar o firewall em servidores remotos.",
        "warning": "Ativar UFW sem liberar SSH bloqueia acesso remoto imediatamente.",
    },
    "nginx": {
        "body": "Nginx é um servidor web de alta performance usado como web server, reverse proxy e load balancer.",
        "steps": [
            {"label": "Instalar nginx",      "description": "Instalação via apt",              "command": "sudo apt install nginx"},
            {"label": "Status",              "description": "Verificar se está rodando",       "command": "sudo systemctl status nginx"},
            {"label": "Testar configuração", "description": "Validar antes de aplicar",        "command": "sudo nginx -t"},
            {"label": "Recarregar config",   "description": "Aplicar sem interromper",         "command": "sudo systemctl reload nginx"},
            {"label": "Ver sites ativos",    "description": "Links em sites-enabled",          "command": "ls -la /etc/nginx/sites-enabled/"},
            {"label": "Logs de erro",        "description": "Últimas 50 linhas",               "command": "sudo tail -50 /var/log/nginx/error.log"},
        ],
        "tip":     "Use 'certbot --nginx' para SSL grátis via Let's Encrypt.",
        "warning": "Sempre teste com 'nginx -t' antes de qualquer reload.",
    },
    "segurança": {
        "body": "Hardening básico reduz drasticamente a superfície de ataque. Priorize SSH, firewall e atualizações.",
        "steps": [
            {"label": "Desabilitar root SSH",  "description": "Impede login direto como root",   "command": "sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config"},
            {"label": "Instalar fail2ban",     "description": "Bloquear tentativas de força",    "command": "sudo apt install fail2ban"},
            {"label": "Ver tentativas falhas", "description": "Acessos SSH negados",             "command": "sudo journalctl -u ssh | grep Failed"},
            {"label": "Atualizar sistema",     "description": "Fechar vulnerabilidades",         "command": "sudo apt update && sudo apt upgrade -y"},
            {"label": "Verificar portas",      "description": "Portas abertas no sistema",       "command": "ss -tlnp"},
        ],
        "tip":     "Use autenticação por chave SSH — desative login por senha.",
        "warning": "Teste SEMPRE as novas configs SSH antes de fechar a sessão atual.",
    },
    "crontab": {
        "body": "Cron agenda tarefas automáticas baseadas em tempo sem intervenção manual.",
        "steps": [
            {"label": "Editar crontab",     "description": "Abrir editor de tarefas",          "command": "crontab -e"},
            {"label": "Ver tarefas ativas", "description": "Listar agendamentos do usuário",   "command": "crontab -l"},
            {"label": "Formato cron",       "description": "min hora dia mês dia-semana cmd",   "command": "# * * * * * /caminho/script.sh"},
            {"label": "Todo dia às 2h",     "description": "Agendamento diário",               "command": "0 2 * * * /home/user/backup.sh"},
            {"label": "A cada hora",        "description": "Execução horária",                 "command": "0 * * * * /home/user/script.sh"},
            {"label": "Log do cron",        "description": "Checar execuções passadas",        "command": "grep CRON /var/log/syslog | tail -20"},
        ],
        "tip":     "Use crontab.guru para testar expressões cron visualmente.",
        "warning": "Scripts cron precisam de caminhos absolutos — aliases não funcionam.",
    },
}

# Keyword → chave em _EXTENDED_HINTS
_KEYWORD_MAP: dict[str, str] = {
    "docker": "docker",      "container": "docker",   "dockerfile": "docker",
    "git":    "git",         "commit":    "git",       "branch":    "git",
    "bash":   "bash",        "script":    "bash",      "shell":     "bash",
    "vim":    "vim",         "vi":        "vim",
    "python": "python",      "pip":       "python",    "venv":      "python",
    "systemd":"systemd",     "systemctl": "systemd",   "service":   "systemd",
    "firewall":"firewall",   "ufw":       "firewall",  "iptables":  "firewall",
    "nginx":  "nginx",       "apache":    "nginx",     "proxy":     "nginx",
    "segurança":"segurança", "security":  "segurança", "hardening": "segurança",
    "cron":   "crontab",     "crontab":   "crontab",   "agendamento":"crontab",
}


def _is_valid(r: object) -> bool:
    """Resposta válida: body não-vazio, não erro, não fallback do Tutor."""
    if not isinstance(r, dict): return False
    if not r.get("body", "").strip(): return False
    if r.get("type") == "error": return False
    # Rejeitar fallback genérico do Tutor
    title = r.get("title", "")
    if "Sem tutorial para" in title or "Sem tutorial" in title:
        return False
    return True


class LearnModule:
    """
    Módulo de aprendizado com pipeline de 4 níveis.
    Garante que SEMPRE retorna conteúdo útil ao utilizador.
    """

    def __init__(self):
        self._tutor = Tutor()
        self._cfg   = Config()

    def teach(self, topic: str) -> dict:
        # Nível 1 — base local (tutorials.json)
        result = self._tutor.teach(topic)
        if _is_valid(result):
            return result

        # Nível 2 — base estendida interna
        extended = self._extended(topic)
        if extended:
            return extended

        # Nível 3 — AI engine (se configurado)
        ai_result = self._try_ai(topic)
        if _is_valid(ai_result):
            return ai_result

        # Nível 4 — fallback contextual (nunca vazio)
        return self._smart_fallback(topic)

    def _extended(self, topic: str) -> dict | None:
        t = topic.lower().strip()
        # Busca direta na base
        if t in _EXTENDED_HINTS:
            return self._fmt(t, _EXTENDED_HINTS[t])
        # Busca por keyword
        for kw, key in _KEYWORD_MAP.items():
            if kw in t:
                return self._fmt(key, _EXTENDED_HINTS[key])
        return None

    def _fmt(self, key: str, data: dict) -> dict:
        return {
            "type":    "learn",
            "title":   f"Tutorial: {key.capitalize()}",
            "body":    data["body"],
            "steps":   data.get("steps", []),
            "tip":     data.get("tip", ""),
            "warning": data.get("warning", ""),
        }

    def _try_ai(self, topic: str) -> dict | None:
        if not self._cfg.get("ai_enabled", True):
            return None
        api_key = self._cfg.get_active_key()
        if not api_key:
            return None
        try:
            from engine.ai import AIEngine
            result = AIEngine(api_key).interpret(f"me ensina sobre: {topic}")
            if isinstance(result, dict) and result.get("type") != "error":
                result["type"] = "learn"
                return result
        except Exception:
            pass
        return None

    def _smart_fallback(self, topic: str) -> dict:
        t = topic.lower()
        sugestao = ""
        for kw, key in _KEYWORD_MAP.items():
            if kw[:3] in t or t[:3] in kw:
                sugestao = f"\n\n  Talvez você queira: learn {key}"
                break

        return {
            "type":  "info",
            "title": f"Tutorial não encontrado: {topic}",
            "body":  (
                f"Não tenho tutorial local sobre '{topic}'.{sugestao}\n\n"
                "Tópicos disponíveis (base local):\n"
                "  permissões · processos · disco · rede · pacotes\n"
                "  usuários · ssh · cron · logs · variáveis-ambiente\n\n"
                "Tópicos disponíveis (base estendida):\n"
                "  docker · git · bash · vim · python · systemd\n"
                "  firewall · nginx · segurança · crontab\n\n"
                "Para QUALQUER outro tema, ative a IA (grátis):"
            ),
            "tip":     "export GEMINI_API_KEY='AIza...'  →  aistudio.google.com/app/apikey",
            "warning": "",
        }
