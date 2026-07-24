```
  ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗
  ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝
     ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗
     ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║
     ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║
     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝
```

> **Assistente inteligente de terminal Linux — aprende, diagnostica e executa com segurança.**

---

## O que é o Terminus?

O Terminus é uma ferramenta de linha de comando para Linux que combina **inteligência artificial** com uma **base de conhecimento offline** para ajudar qualquer pessoa — do iniciante ao avançado — a usar o Linux com confiança.

Não é um manual. Não é um chatbot genérico. É um assistente que:

- **Entende o que você escreve** — em linguagem natural, sem decorar sintaxe
- **Ensina o porquê** — não só o comando, mas o que ele faz e por quê funciona
- **Resolve problemas reais** — WiFi, disco cheio, permissões, serviços parados, SSH
- **Executa com segurança** — mostra o que vai fazer antes de fazer, pede confirmação
- **Funciona offline** — base local de soluções e tutoriais sem precisar de internet
- **Usa IA quando disponível** — responde qualquer pergunta sobre Linux com contexto da sua conversa

---

## Para quem é?

| Perfil | Como o Terminus ajuda |
|---|---|
| **Iniciante** | Aprende Linux na prática, com explicações em português |
| **Utilizador intermédio** | Resolve problemas sem procurar no Google |
| **Administrador** | Diagnóstico rápido de sistema, serviços e rede |
| **Programador** | Aprende Docker, Git, Bash, Python, Nginx sem sair do terminal |

---

## O que o Terminus faz na prática?

**Exemplo 1 — Problema de WiFi:**
```
terminus❯ meu wifi parou de funcionar depois de atualizar

→ Diagnostica a interface de rede
→ Verifica o estado do NetworkManager
→ Mostra 7 passos para resolver
→ Explica o que cada comando faz antes de executar
→ Pede confirmação antes de qualquer acção
```

**Exemplo 2 — Aprender Docker:**
```
terminus❯ learn docker

→ Explica o que são containers e por quê existem
→ Guia passo a passo: instalar, executar, parar, remover
→ Mostra os comandos mais usados com exemplos reais
```

**Exemplo 3 — Disco cheio:**
```
terminus❯ fix disco cheio

→ Mostra o uso de cada partição
→ Identifica as pastas mais pesadas
→ Oferece formas seguras de libertar espaço
→ Avisa o que NUNCA apagar
```

**Exemplo 4 — Qualquer pergunta (com IA):**
```
terminus❯ como configurar o nginx como proxy reverso para o meu app node?

→ A IA responde com o contexto do seu sistema
→ Passos específicos, não genéricos
→ Lembra o que foi dito antes na conversa
```

---

## O que torna o Terminus diferente?

- **Não executa nada sem mostrar primeiro** — dry-run antes de qualquer acção
- **Comandos destrutivos são bloqueados permanentemente** — sem excepções
- **Funciona sem internet** — base local cobre os problemas mais comuns
- **Vários providers de IA** — Gemini, OpenRouter, Anthropic, DeepSeek — troca automaticamente se um falhar
- **Guarda o contexto da conversa** — a IA lembra o que foi dito antes
- **Detecta o seu Linux** — adapta os comandos à sua distro e gestor de pacotes

---

## Instalar

### Passo 1 — Extrair o ficheiro

```bash
unzip TERMINUS2_FINAL.zip
cd terminus_v2
```

### Passo 2 — Instalar

```bash
bash install.sh
```

O script trata de tudo:
- Verifica o Python 3.8+
- Instala as dependências
- Cria o comando `terminus` disponível em qualquer terminal
- Cria o ficheiro `.env` para guardar as suas chaves

### Passo 3 — Abrir novo terminal

```bash
source ~/.bashrc
```

### Passo 4 — Testar

```bash
terminus --version
```

---

## Usar

```bash
terminus              # modo interactivo (recomendado)
terminus fix wifi     # comando directo
terminus learn docker
terminus scan
terminus setup        # configurar IA
```

---

## Comandos

| Comando | O que faz |
|---|---|
| `fix <problema>` | Diagnostica e resolve (wifi, disco, permissão, ssh...) |
| `learn <tema>` | Tutorial passo a passo (docker, git, bash, nginx...) |
| `scan` | Saúde do sistema: disco, RAM, CPU, serviços |
| `setup` | Configurar chave de API e modelo de IA |
| `setup status` | Ver configuração actual |
| `setup test` | Testar ligação à IA |
| `history` | Ver o que foi digitado nesta sessão |
| `help` | Lista de comandos |
| `exit` | Sair |

---

## Configurar IA (grátis)

O Terminus funciona **offline sem IA**. Com IA configurada, responde qualquer pergunta sobre Linux.

### Google Gemini — grátis, sem cartão

1. Acede a: **https://aistudio.google.com/app/apikey**
2. Clica em **"Create API Key"** e copia a chave
3. No terminal:

```bash
terminus setup
```

Escolhe a opção `1` → selecciona `Google Gemini` → cola a chave.

A chave fica guardada automaticamente. Não precisas de fazer isto novamente.

---

## Providers de IA suportados

No menu `terminus setup` podes adicionar e trocar entre qualquer provider:

| Provider | Custo | Onde obter a chave |
|---|---|---|
| Google Gemini | **Grátis** | aistudio.google.com/app/apikey |
| OpenRouter | Grátis / Pago | openrouter.ai/keys |
| Anthropic Claude | Pago | console.anthropic.com/keys |
| DeepSeek | Pago (barato) | platform.deepseek.com/api_keys |

Podes adicionar várias chaves. Se a principal falhar, o Terminus usa outra automaticamente.

---

## Escolher o modelo de IA

No menu `terminus setup`, opção `2`:

**Grátis via OpenRouter:**
- `google/gemini-2.0-flash-exp:free` — recomendado
- `meta-llama/llama-3.3-70b-instruct:free`
- `deepseek/deepseek-chat:free`

**Gemini directo:**
- `gemini-2.0-flash` — rápido, recomendado
- `gemini-1.5-pro` — mais inteligente

A escolha fica guardada. Podes alterar a qualquer momento.

---

## Segurança

O Terminus **nunca executa** sem confirmação. Comandos destrutivos são bloqueados permanentemente, sem excepções:

```
rm -rf /         → BLOQUEADO
dd of=/dev/sda   → BLOQUEADO
mkfs /dev/...    → BLOQUEADO
curl ... | bash  → BLOQUEADO
fork bomb        → BLOQUEADO
```

Operações com `sudo` pedem **confirmação dupla**.

---

## Problemas na instalação

**"terminus: command not found"**
```bash
source ~/.bashrc
# ou abra um novo terminal
```

**"No module named 'rich'"**
```bash
pip install rich python-dotenv google-genai --break-system-packages
```

**"IA não responde"**
```bash
terminus setup test
```

---

## Estrutura do projecto

```
terminus_v2/
├── main.py              ← Entrada (CLI e modo interactivo)
├── cli/                 ← Interface visual (Rich)
├── core/
│   ├── config.py        ← Multi-provider, modelos, persistência
│   ├── router.py        ← IA primeiro, base local como fallback
│   └── context.py       ← Histórico multi-turn para a IA
├── engine/
│   ├── ai.py            ← Gemini · OpenRouter · Anthropic · DeepSeek
│   ├── brain.py         ← Classificação de intenção
│   ├── safety.py        ← Bloqueia comandos destrutivos
│   └── executor.py      ← Execução segura com dry-run
├── modules/
│   ├── fix/             ← Diagnóstico de problemas
│   ├── learn/           ← Tutoriais
│   ├── scan/            ← Health check do sistema
│   └── setup/           ← Configuração de IA
├── utils/
│   ├── validator.py     ← Sanitização de input
│   └── os_detect.py     ← Detecta distro e gestor de pacotes
├── data/
│   ├── problems.json    ← Base offline de problemas
│   └── tutorials.json   ← Base offline de tutoriais
└── tests/test_all.py    ← 45 testes automáticos
```

---

## Direitos de autor

© 2025 Terminus. Todos os direitos reservados.

Este software é propriedade exclusiva do seu autor.
Não é permitida a cópia, distribuição, modificação ou uso comercial
sem autorização expressa e por escrito.
