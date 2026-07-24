#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Terminus 2.0 — Installer
#  Usage:  bash install.sh
#  Remote: curl -fsSL https://your-url/install.sh | bash
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────
RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET}  $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $*"; }
err()  { echo -e "  ${RED}✗${RESET}  $*"; }
info() { echo -e "  ${CYAN}→${RESET}  $*"; }
sep()  { echo -e "${DIM}──────────────────────────────────────────────────────────${RESET}"; }

# ── Banner ────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
cat << 'EOF'
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗
  ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
EOF
echo -e "${RESET}  ${DIM}Installer v2.0.0${RESET}\n"

# ── Config ────────────────────────────────────────────────────
INSTALL_DIR="${HOME}/.terminus"
BIN_DIR="${HOME}/.local/bin"
BIN_PATH="${BIN_DIR}/terminus"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || pwd)"

# ── Step 1: Python check ──────────────────────────────────────
sep
echo -e "  ${BOLD}[1/6] Verificando Python${RESET}"
if ! command -v python3 &>/dev/null; then
    err "Python 3 não encontrado."
    echo ""
    echo "  Instale com:"
    echo -e "    ${CYAN}sudo apt install python3 python3-pip${RESET}    # Debian/Ubuntu"
    echo -e "    ${CYAN}sudo dnf install python3 python3-pip${RESET}    # Fedora"
    echo -e "    ${CYAN}sudo pacman -S python python-pip${RESET}         # Arch"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ]]; then
    err "Python ${PY_VER} encontrado. Terminus requer Python 3.8+."
    exit 1
fi
ok "Python ${PY_VER}"

# ── Step 2: pip check ─────────────────────────────────────────
sep
echo -e "  ${BOLD}[2/6] Verificando pip${RESET}"
if ! python3 -m pip --version &>/dev/null; then
    warn "pip não encontrado. Tentando instalar..."
    python3 -m ensurepip --upgrade 2>/dev/null || \
        sudo apt install -y python3-pip 2>/dev/null || \
        { err "Não foi possível instalar pip. Instale manualmente."; exit 1; }
fi
ok "pip disponível"

# ── Step 3: Instalar dependências ─────────────────────────────
sep
echo -e "  ${BOLD}[3/6] Instalando dependências${RESET}"
info "Instalando: rich anthropic"
python3 -m pip install --quiet --upgrade rich anthropic 2>&1 | \
    grep -v "already satisfied" | \
    grep -v "^$" | \
    sed 's/^/    /' || true

python3 -c "import rich, anthropic" 2>/dev/null && ok "Dependências instaladas" || \
    { err "Falha ao instalar dependências"; exit 1; }

# ── Step 4: Copiar arquivos ────────────────────────────────────
sep
echo -e "  ${BOLD}[4/6] Instalando Terminus em ${INSTALL_DIR}${RESET}"
mkdir -p "${INSTALL_DIR}"
cp -r "${SCRIPT_DIR}/." "${INSTALL_DIR}/"
ok "Arquivos copiados para ${INSTALL_DIR}"

# ── Step 5: Criar comando global ──────────────────────────────
sep
echo -e "  ${BOLD}[5/6] Criando comando global 'terminus'${RESET}"
mkdir -p "${BIN_DIR}"

# Try symlink to /usr/local/bin (if sudo available)
if command -v sudo &>/dev/null && sudo -n true 2>/dev/null; then
    sudo ln -sf "${INSTALL_DIR}/main.py" /usr/local/bin/terminus 2>/dev/null && \
        sudo chmod +x /usr/local/bin/terminus 2>/dev/null && \
        ok "Comando global criado: /usr/local/bin/terminus" && GLOBAL=true || GLOBAL=false
else
    GLOBAL=false
fi

# Fallback: ~/.local/bin wrapper
if [[ "${GLOBAL:-false}" == "false" ]]; then
    cat > "${BIN_PATH}" << LAUNCHER
#!/usr/bin/env bash
exec python3 "${INSTALL_DIR}/main.py" "\$@"
LAUNCHER
    chmod +x "${BIN_PATH}"
    ok "Launcher criado: ${BIN_PATH}"
fi

# ── Add to PATH if needed ─────────────────────────────────────
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
for RC in "${HOME}/.bashrc" "${HOME}/.zshrc" "${HOME}/.profile"; do
    if [[ -f "$RC" ]] && ! grep -qF '.local/bin' "$RC" 2>/dev/null; then
        echo "$PATH_LINE" >> "$RC"
        ok "PATH adicionado a ${RC}"
    fi
done

# ── Step 6: Nerd Fonts detection ──────────────────────────────
sep
echo -e "  ${BOLD}[6/6] Verificando Nerd Fonts${RESET}"

NERD_FOUND=false
if command -v fc-list &>/dev/null; then
    if fc-list 2>/dev/null | grep -qi "nerd\|hack nerd\|firacode nerd\|jetbrains"; then
        ok "Nerd Fonts detectada — ícones avançados ativados"
        NERD_FOUND=true
    fi
fi

if [[ "$NERD_FOUND" == "false" ]]; then
    warn "Nerd Fonts não detectada — usando ícones ASCII"
    echo ""
    echo -e "  ${DIM}Para ícones avançados, instale uma Nerd Font:${RESET}"
    echo -e "    ${CYAN}https://www.nerdfonts.com/font-downloads${RESET}"
    echo ""
    echo -e "  ${DIM}Recomendadas: JetBrainsMono Nerd Font · FiraCode Nerd Font · Hack Nerd Font${RESET}"
    echo ""
    echo -e "  ${DIM}Instalação rápida (Ubuntu/Debian):${RESET}"
    echo -e "    ${CYAN}mkdir -p ~/.local/share/fonts${RESET}"
    echo -e "    ${CYAN}cd ~/.local/share/fonts${RESET}"
    echo -e "    ${CYAN}curl -fLo 'JetBrainsMonoNerdFont-Regular.ttf' \\${RESET}"
    echo -e "    ${CYAN}  https://github.com/ryanoasis/nerd-fonts/raw/HEAD/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFontMono-Regular.ttf${RESET}"
    echo -e "    ${CYAN}fc-cache -fv${RESET}"
    echo ""
    echo -e "  ${DIM}Depois configure seu terminal para usar a fonte e reabra.${RESET}"
    echo ""
    echo -e "  ${DIM}Para forçar ícones Nerd Fonts sem instalar:${RESET}"
    echo -e "    ${CYAN}export TERMINUS_ICONS=1${RESET}"
fi

# ── AI / API Key ─────────────────────────────────────────────
sep
echo ""
if [[ -n "${GEMINI_API_KEY:-}" ]]; then
    ok "GEMINI_API_KEY detectada — IA habilitada (Google Gemini)"
else
    info "Para habilitar respostas com IA (GRÁTIS):"
    echo ""
    echo -e "    ${BOLD}1.${RESET} Acesse ${CYAN}https://aistudio.google.com/app/apikey${RESET}"
    echo -e "    ${BOLD}2.${RESET} Faça login com sua conta Google"
    echo -e "    ${BOLD}3.${RESET} Clique em ${BOLD}Create API Key${RESET}"
    echo -e "    ${BOLD}4.${RESET} Copie a chave e execute:"
    echo ""
    echo -e "    ${CYAN}export GEMINI_API_KEY='AIza...'${RESET}"
    echo -e "    ${DIM}# Para persistir, adicione a linha acima ao ~/.bashrc${RESET}"
    echo ""
    echo -e "    ${DIM}Plano gratuito: 15 req/min · 1M tokens/dia · sem cartão${RESET}"
fi

# ── Done ──────────────────────────────────────────────────────
sep
echo ""
echo -e "  ${GREEN}${BOLD}✓ Terminus 2.0 instalado com sucesso!${RESET}"
echo ""
echo -e "  Para começar:"
echo -e "    ${DIM}(abra um novo terminal ou execute)${RESET} ${CYAN}source ~/.bashrc${RESET}"
echo -e "    ${CYAN}terminus${RESET}"
echo ""
echo -e "  Ou rode diretamente:"
echo -e "    ${CYAN}python3 ${INSTALL_DIR}/main.py${RESET}"
echo ""
sep
