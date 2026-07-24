# Como Configurar a IA no Terminus

## Opção 1 — Google Gemini (GRÁTIS, recomendado)

### Passo 1: Obter a chave

1. Acede a: https://aistudio.google.com/app/apikey
2. Clica em **"Create API Key"**
3. Copia a chave (exemplo: `AIza...XYZ123`)

### Passo 2: Guardar a chave (escolha UMA)

**Opção A — Uma única sessão:**
```bash
export GEMINI_API_KEY="AIza...sua_chave"
terminus
```

**Opção B — Para sempre (recomendado):**
```bash
echo 'export GEMINI_API_KEY="AIza...sua_chave"' >> ~/.bashrc
source ~/.bashrc
```

**Opção C — Via menu setup:**
```bash
terminus setup
# Escolhe opção 1 → Google Gemini → cola a chave
```

---

## Opção 2 — OpenRouter (GRÁTIS ou Pago)

Modelos grátis:
- `google/gemini-2.0-flash-exp:free`
- `meta-llama/llama-3.3-70b-instruct:free`
- `deepseek/deepseek-chat:free`

### Passo 1: Obter a chave

1. Acedes a: https://openrouter.ai/keys
2. Cria conta e gera a chave

### Passo 2: Guardar

```bash
echo 'export OPENROUTER_API_KEY="sk-or-...sua_chave"' >> ~/.bashrc
source ~/.bashrc
```

Depois:
```bash
terminus setup
# Escolhe opção 1 → OpenRouter → cola a chave
# Escolhe opção 2 → selecciona modelo grátis
```

---

## Testar se funciona

```bash
terminus setup test
```

Se aparecer "Ligação com sucesso!", está tudo certo.

---

## Sem IA configurada?

Sem problema! O Terminus funciona 100% offline:

```bash
terminus fix wifi
terminus fix disco cheio
terminus fix sistema lento
terminus learn docker
terminus learn git
terminus scan
```

Só não conseguirá responder perguntas livres em linguagem natural como:
```
> como configurar um proxy reverso no nginx?
```

Para isso, precisa de IA configurada.
