# Bolão Miha 2026 — Landing Page (protótipo)

Protótipo responsivo da landing page do **Bolão Miha 2026** (Copa do Mundo FIFA 2026).
**Todos os dados são de exemplo (placeholder)** — servem só para mostrar o *look and feel*.

## Arquivos
- `index.html` — a página (HTML/CSS/JS, arquivo único, sem dependências de build).
- `data.sample.json` — o **modelo de dados** oficial (estrutura final). Hoje o `index.html` embute uma cópia desses dados na constante `DATA`.

## Como visualizar
- **Mais simples:** dê duplo clique em `index.html` (abre no navegador).
- **Servindo local** (recomendado para testar carregamento de JSON):
  ```bash
  cd landing-page
  python3 -m http.server 4321
  # abra http://localhost:4321
  ```

## Como vai funcionar com dados reais
1. Cada jogador preenche uma cópia da planilha `Bolão Miha 2026 Modelo v2.1.xlsx` e envia.
   O **nome do arquivo = apelido do jogador**.
2. Um motor de pontuação (a construir) lê as planilhas → gera `data.json` no formato de `data.sample.json`.
3. No `index.html`, troque a constante `DATA` embutida por:
   ```js
   const DATA = await (await fetch('data.json')).json();
   ```
4. O site se atualiza sozinho a cada novo `data.json`.

## Como publicar (link único para o grupo)
Site estático — hospede grátis em **Netlify**, **Vercel** ou **GitHub Pages**.
Gere um link curto + QR code para mandar no WhatsApp. Sem login, sem app.

## Pendências antes de valer
- Definir a lista de **"Jogos Especiais"** (valem 5 pts em vez de 3).
- Corrigir 3 fórmulas de empate na aba `Cálculos` da planilha (ver relatório).
- Conectar verificação automática do calendário/resultados (hoje: lançamento manual pelo organizador).

> Bolão de **palpites** por pontos e diversão. Não é casa de apostas, não processa pagamentos, não faz odds.
