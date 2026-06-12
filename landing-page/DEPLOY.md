# 🚀 Deploy do Bolão Miha 2026 — passo a passo

> **🔄 ATUALIZAÇÃO IMPORTANTE (11/jun):** com o robô de placar automático, o repositório
> agora deve ser a **pasta raiz do projeto** (`World Cup 26/`), que contém `landing-page/`,
> `engine/` e `.github/workflows/`. O `netlify.toml` da raiz já aponta o site para
> `landing-page/`. Nos passos abaixo, onde se lê "selecione a pasta landing-page",
> selecione a **pasta do projeto inteiro**. O `.gitignore` da raiz garante que nenhuma
> planilha `.xlsx` suba ao GitHub. Veja `engine/README.md` → "Modo automático".

Site **estático** (HTML + `data.json`). A cada rodada, você atualiza **um único arquivo** (`data.json`) e o site se republica sozinho.

> 🔒 **Privacidade:** o repositório contém só a pasta `landing-page`. As **planilhas dos jogadores ficam de fora** (estão no `.gitignore`). Nunca suba `.xlsx` ao GitHub.

---

## ✅ O que você vai precisar (uma vez só)

1. Conta no **GitHub** → https://github.com/signup (grátis)
2. Conta no **Netlify** → https://app.netlify.com/signup (grátis, pode entrar com o próprio GitHub)
3. **GitHub Desktop** (jeito mais fácil, sem terminal) → https://desktop.github.com

---

## 🟢 OPÇÃO A — GitHub Desktop + Netlify (recomendado, sem terminal)

### Parte 1 — Subir a pasta para o GitHub (uma vez)
1. Instale e abra o **GitHub Desktop** e faça login na sua conta GitHub.
2. Menu **File → Add Local Repository…**
3. Selecione a pasta:
   `/Users/paulocrepaldi/Documents/Claude/Projects/World Cup 26/landing-page`
4. Ele vai avisar que "não é um repositório git" → clique em **"create a repository"**.
5. Em **Name**, deixe `bolao-miha-2026` → **Create Repository**.
6. No topo, clique em **Publish repository**.
   - Marque **"Keep this code private"** (deixa o código privado; o site continua público).
   - **Publish repository**.

### Parte 2 — Conectar ao Netlify (uma vez)
1. Entre em https://app.netlify.com → **Add new site → Import an existing project**.
2. Escolha **Deploy with GitHub** e autorize o acesso.
3. Selecione o repositório **bolao-miha-2026**.
4. Em configurações de build, **não preencha nada** (o `netlify.toml` já cuida disso):
   - Build command: *(vazio)*
   - Publish directory: `.`
5. Clique em **Deploy**. Em ~30s o site fica no ar com uma URL tipo
   `https://nome-aleatorio.netlify.app`.

### Parte 3 — Dar um nome bonito ao link (uma vez)
1. No painel do site: **Site configuration → Change site name**.
2. Coloque, por ex., `bolao-miha-2026` → vira **https://bolao-miha-2026.netlify.app**.
3. Mande esse link no grupo do WhatsApp. (Dá pra gerar um QR code em qualquer gerador grátis.)

### 🔁 Atualizar a cada rodada (o passo do dia a dia)
1. Substitua o arquivo **`data.json`** na pasta `landing-page` pelo novo (gerado pelo motor de pontuação).
2. No **GitHub Desktop**: ele mostra a alteração → escreva um resumo (ex.: `Resultados rodada 1`) → **Commit to main** → **Push origin**.
3. Pronto. O Netlify republica sozinho em ~30 segundos. ✅

---

## 🔵 OPÇÃO B — Pelo Terminal (se preferir linha de comando)

> Requer autenticação no GitHub. O mais simples: `brew install gh` e depois `gh auth login`.

```bash
cd "/Users/paulocrepaldi/Documents/Claude/Projects/World Cup 26/landing-page"

# 1) Inicializar e subir (uma vez)
git init
git add .
git commit -m "Bolão Miha 2026 — landing page"
git branch -M main
gh repo create bolao-miha-2026 --private --source=. --push
# (ou crie o repo no site e use: git remote add origin URL ; git push -u origin main)
```

Depois, conecte ao Netlify como na **Parte 2** acima.

**Atualizar a cada rodada:**
```bash
cd "/Users/paulocrepaldi/Documents/Claude/Projects/World Cup 26/landing-page"
# (troque o data.json pelo novo)
git add data.json
git commit -m "Resultados rodada X"
git push
```

---

## 🟡 OPÇÃO C — Sem GitHub (Netlify Drop, mais manual)

1. Abra https://app.netlify.com/drop
2. **Arraste a pasta `landing-page` inteira** para a área indicada → site no ar na hora.
3. A cada atualização, entre no site em **Deploys** e **arraste a pasta de novo** sobre o site existente (para manter a mesma URL).

> Funciona, mas você re-arrasta a cada rodada. Para a Copa toda, a Opção A é bem melhor.

---

## 🏁 Quando a Copa começar (tirar o aviso de "protótipo")

No arquivo `data.json`, mude:
```json
"is_placeholder": true
```
para
```json
"is_placeholder": false
```
Faça commit/push. O aviso amarelo de protótipo e o seletor "Pré-Copa / Simulação" **somem automaticamente**, e o site passa a mostrar só os dados reais.

---

## 📦 O que vai publicado (e o que NÃO vai)

| Vai para o GitHub/Netlify | Fica de fora (privado) |
|---|---|
| `index.html` | `*.xlsx` (planilhas dos jogadores) |
| `data.json` (dados do site) | `_serve.py`, `*.log` |
| `data.sample.json`, `README.md`, `DEPLOY.md`, `netlify.toml` | pastas de editor (`.vscode/`, `.idea/`) |

---

## 🆘 Problemas comuns

- **O placar não atualiza no site:** o `netlify.toml` já manda `data.json` sem cache. Se ainda assim ficar velho, dê um *hard refresh* (Cmd+Shift+R) — o site também adiciona `?ts=` para furar o cache.
- **"Page not found" no Netlify:** confira que o **Publish directory** é `.` e que o `index.html` está na raiz do repositório (pasta `landing-page`).
- **Quero testar local antes de publicar:** `cd landing-page && python3 -m http.server 4321` → abra `http://localhost:4321`.
