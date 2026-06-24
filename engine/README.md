# ⚙️ Motor de Pontuação — Bolão Miha 2026

Lê as planilhas preenchidas dos apostadores, aplica as regras, monta a classificação
e gera o `data.json` que alimenta a landing page. **Recalcula tudo do zero a partir dos
inputs** (não confia na classificação que a planilha calcula) — isso evita o problema de
cache de fórmula e dá verificação independente.

## Instalação (uma vez)
```bash
cd engine
pip3 install -r requirements.txt
```

## Setup único (quando as 88 planilhas chegarem)
1. Coloque as planilhas em **`engine/bets/`** (1 arquivo por aposta; nome do arquivo / célula B2 = apelido).
2. Preencha **`engine/data/roster.csv`**: `alias, paid (sim/não), order (ordem de envio)`.
3. Gere os caches que o robô usa (planilhas NÃO sobem ao GitHub):
   ```bash
   python3 catalog.py          # → data/catalog.json (72 jogos + especiais)
   python3 extract_bets.py     # → data/bets_extracted.json (só os palpites)
   ```
4. Confira `data/validation_report.txt` e peça reenvio das planilhas com problema.
5. Commit + push. Pronto — o robô assume.

## Modo automático (durante a Copa) — GitHub Actions
O workflow **`.github/workflows/atualiza-placar.yml`** é disparado por um **pinger externo
(cron-job.org)** a cada **~5 min** (o cron nativo do GitHub é instável para este repo):
busca placares na **ESPN** (com conferência cruzada na football-data.org) → atualiza
`results.csv` → repontua (`build_data.py --from-json`) → commita `data.json` → **GitHub Pages** republica.
- **Setup**: chave grátis da 2ª fonte em https://www.football-data.org/client/register, salva no
  GitHub em *Settings → Secrets and variables → Actions* como `FOOTBALL_DATA_TOKEN`.
- **Correção manual vence**: linha com `lock=sim` no `results.csv` nunca é sobrescrita pelo robô
  (placar sempre na **orientação da planilha**, não a da ESPN).
- ✅ Em produção, validado ao vivo durante a Copa (ESPN primária; football-data só confere).

## Modo manual (fallback que sempre funciona)
1. Edite **`engine/data/results.csv`** com os placares (ids em `data/matches_reference.csv`).
2. ```bash
   python3 build_data.py --from-json --out ../landing-page/data.json
   ```
3. `git push`. (No fim da Copa, preencha **`data/facts.json`** com campeão real + categorias.)

## Arquivos
| Arquivo | O quê |
|---|---|
| `config.py` | Mapa das células e regras de pontuação |
| `catalog.py` | Lê os 72 jogos da planilha-modelo + detecta especiais (verde) |
| `read_bets.py` | Lê uma aposta → inputs |
| `scoring.py` | Regras de pontuação (puro, testado) |
| `leaderboard.py` | Ranking, desempate, movimentação, "matematicamente vivo" |
| `build_data.py` | Orquestra tudo → `data.json` |
| `data/results.csv` | Placares oficiais (você preenche) |
| `data/facts.json` | Fatos das categorias + campeão real |
| `data/roster.csv` | Quem pagou + ordem de envio |
| `data/matches_reference.csv` | Gerado: `match_id` ↔ jogo |
| `data/validation_report.txt` | Gerado: avisos por planilha |
| `data/history.json` | Gerado: snapshots p/ movimentação |

## Testes
```bash
python3 -m pytest tests -q     # 16 testes da pontuação
```

## Desempate (PROVISÓRIO — confirmar com o organizador)
mais pontos → mais placares exatos → mais acertos de vencedor → ordem de envio.

## Privacidade
`engine/bets/*.xlsx` são dados privados dos apostadores — **não** sobem ao GitHub
(estão no `.gitignore`). Só o `data.json` agregado é publicado.

## Regra de edição dos palpites (importante p/ o mata-mata)
Apostas fechadas no início. Depois da 1ª fase, cada um pode **atualizar os placares do
mata-mata** até a véspera de cada jogo — MAS **campeão/vice/3º e categorias extras ficam
FIXOS** da aposta inicial até o fim.
→ No v2, o motor deve ler **Classificação Final + Categorias da aposta INICIAL** e os
**placares de mata-mata do arquivo mais recente** de cada apostador. Convenção sugerida:
`bets/inicial/<apelido>.xlsx` (trava final+extras) e `bets/mata/<apelido>.xlsx` (placares atualizados).

## Conformidade com a aba "Regras" (checklist do motor)
- ✅ Vencedor/empate 3 (normal) / 5 (especial=verde); bônus exato = nº de gols, mín. 2.
- ✅ Classificação final 15/10/5 + 3 (top-3 em posição errada); lida do chaveamento (AC9/13/17).
- ✅ Artilheiro 8/4/3 (+5 completo); 8 curiosidades × 5.
- ✅ Pontos da 1ª fase **não zeram** (acumulam); vencedor da fase segue elegível aos prêmios finais.
- ✅ Final + Categorias **fixos** da aposta inicial (trava no v2 via pasta `bets/inicial`).
- 📝 **Prêmios só para PAGANTES**: Lanterna de Ouro, Bom de Palpite (20%) e top-4 (40/25/10/5)
  são apurados **somente entre apostas pagas**. Lanterna devolve a aposta (R$60) por cima; % sobre o resto.
- 📝 **Lanterna de Ouro = último PAGANTE ao fim da 1ª FASE** (não o último geral ao vivo) — apurar no fim da fase de grupos.
- 📝 **Bom de Palpite = líder PAGANTE ao fim da 1ª fase**.
- ⚠️ **v2 — mata-mata**: resultado **até o fim da prorrogação** (empate permitido); **pênaltis NÃO pontuam** (só apontam quem avança); bônus usa os gols incluindo prorrogação.
- ⚠️ **v2 — curiosidades**: "resultados e total de gols **incluindo prorrogações**" — os fatos em `facts.json` devem já considerar a prorrogação.

## Pendente (v2)
- Pontuação do **mata-mata** (mesma função `score_match`; falta o catálogo do chaveamento, que só existe após a fase de grupos) + regra de edição acima.
- Probabilidade por simulação (Monte Carlo) — opcional, decidido para depois.
