# Runbook — abrir cada nova fase do mata-mata (R16 → Final)

Faça isto **quando a fase anterior acabar** (R32 termina ~03/07; depois oitavas, quartas, semi, final/3º).
O robô já faz o trabalho de **dados** sozinho; o que sobra é **criar o Form** (o Google não deixa o robô criar formulários).

> Se NADA disso for feito, a fase nova **não some o site** (fail-closed), mas os palpites valem o
> **original** da planilha e ninguém consegue atualizar. Por isso o checklist.

## O que o robô já faz sozinho (não precisa mexer)
- **Resolve o chaveamento:** `resolve_bracket.py` gera os confrontos da nova fase a partir dos
  vencedores (oitavas, quartas, semi, final, e o 3º lugar = perdedores das semis). Eles entram no
  `knockout_bracket.json` e aparecem no site (hero/central/Minha Aposta) e no pôster.
- **Captura resultado + ao vivo** da nova fase (placar até a prorrogação, sem pênaltis).

## Checklist do organizador (por fase) — ~5 min

1. **Pegue os confrontos da fase.** Veja o log do robô (passo "Resolver chaveamento") ou rode
   `cd engine && python3 resolve_bracket.py --dry-run` — ele imprime um bloco **MATCHES pronto pra colar**.

2. **Crie o Form.** Templates prontos por fase: `forms/criar_form_R32.gs` (referência, já rodado),
   `criar_form_R16.gs`/`criar_form_QF.gs` (já rodados), `criar_form_SF.gs` e `criar_form_FIN.gs`
   (**Final + 3º lugar no MESMO Form** — mesmo prazo, Jogo 1 = Final/slot "FIN", Jogo 2 = 3º
   lugar/slot "TER", NÃO troque a ordem). Reusando o template certo da fase:
   - `FASE` → o nome da fase (ex.: `'Mata-mata · Oitavas de final'`).
   - `PASTA_ID` → mantém (a mesma pasta).
   - `MATCHES` → **cole o bloco** que o `resolve_bracket` imprimiu e ajuste o `quando` (data/hora BRT de cada jogo).
   - `ALIASES` → mantém (os 88).
   - Rode `criarFormularioR32` (autorize). Guarde os 3 links.

3. **⚠️ FUSO da planilha de respostas = (GMT-03:00) São Paulo** (Arquivo → Configurações) e faça
   **1 envio de teste** conferindo o carimbo. *(É o risco nº1 — sem isso, apostas legítimas somem em silêncio.)*

4. **Compartilhe a planilha** ("Qualquer pessoa com o link → Leitor") e pegue o **link de edição**
   (`.../d/`**`ID`**`/edit`). A URL de CSV confiável é: `https://docs.google.com/spreadsheets/d/ID/export?format=csv&gid=GID`.

5. **Ligue no robô:** adicione a rodada em `engine/data/knockout_forms.json`:
   ```json
   { "round": "R16", "deadline": "2026-07-04 23:00",
     "slot_deadlines": { "R16-01": "2026-07-04 11:00" },
     "csv": "https://docs.google.com/spreadsheets/d/ID/export?format=csv&gid=GID",
     "form_url": "<link PÚBLICO do Form da fase>" }
   ```
   - `round`: `R16` | `QF` | `SF` | `FIN` (a final e o 3º vêm no mesmo Form/rodada `FIN`; o slot do Jogo 1 = `FIN`, o Jogo 2 = `TER`).
   - `form_url`: o link público do Form (o que vai no zap). Faz aparecer o botão "Atualizar meus palpites" na landing — o texto muda sozinho por fase (ex.: **"...das Quartas de Finais"**, **"...da Final e do 3º Lugar"**), vem de `KO_BTN_TEXT` em `app.js` a partir do `round` acima.
   - `deadline`: prazo PADRÃO da fase. `slot_deadlines`: só para o(s) jogo(s) que começam mais cedo (trava por jogo).
   - **Limpe os `slot_deadlines` da fase anterior** (não copie os do R32).

6. **Mande o link público** no WhatsApp + o apelido de cada um (como no R32).

## Prazos combinados (BRT)
| Fase | Prazo padrão |
|---|---|
| Oitavas | 13h de sáb 04/07 |
| Quartas | 12h (meio-dia) de qui 09/07 |
| Semis | 12h (meio-dia) de ter 14/07 |
| 3º + Final | 12h (meio-dia) de sáb 18/07 |

(No R32 foi: África do Sul × Canadá meio-dia 28/06; resto 23h 28/06.)

> **MUDANÇA DE REGRA (definida 07/07, antes do Form de Quartas ser criado):** a partir das
> Quartas o prazo virou **meio-dia do MESMO DIA do 1º jogo da fase** (era "23h da véspera").
> Confirmado que dá folga real antes do 1º jogo (Quartas: QF-01 09/07 17h BRT — 5h de folga).
> **Antes de criar o Form de cada fase, reconfira se o 1º jogo dela kicka DEPOIS do meio-dia**
> (se algum jogo começar de manhã no mesmo dia do prazo, precisa de `slot_deadlines`
> específico pra esse jogo, como foi feito no R32). Nas Quartas isso já foi conferido: os 3
> confrontos definidos (QF-01/02/03) começam à tarde/noite, sem exceção necessária — falta só
> reconferir o QF-04 assim que resolver. **Avise explicitamente nessa mudança de regra na
> comunicação do WhatsApp** — "prazo mudou de 23h da véspera pra meio-dia do mesmo dia", não
> só o prazo novo (quem já se acostumou com o padrão antigo pode perder o prazo achando que
> ainda tem a noite inteira).

## Fim de Copa — feche `engine/data/facts.json` (passo final, ~5 min)

O robô resolve o mata-mata e a maioria das categorias extras sozinho — MAS um punhado de campos
fica em "parcial ao vivo" pra sempre e só vira **definitivo** quando o organizador escreve o
valor real em `facts.json` (o motor nunca sobrescreve um campo já preenchido, então isso é 100%
seguro de fazer a qualquer momento, mesmo antes do fim, se algum fato já estiver decidido).

**Depois que a Final + Disputa de 3º Lugar (`FIN`/`TER`) encerrarem, o robô já cuida disto sozinho:**

0. `champion`, `vice`, `third` — **AUTOMÁTICO desde 15/07** (`fetch_facts.py::compute_final_classification`):
   assim que a ESPN marcar `FIN`/`TER` como encerrados em `knockout_fixtures.json`, o robô lê o
   campo `winner` (que já reflete o resultado real, inclusive pênaltis) e preenche os 3 campos
   sozinho no próximo ciclo (~5 min) — a tela de Encerramento passa a mostrar o campeão certo sem
   precisar editar nada. Só mexa manualmente se, por algum motivo, precisar CORRIGIR um valor
   (o motor nunca sobrescreve um campo já preenchido — nem o que ele mesmo escreveu).

**Ainda preencha manualmente em `facts.json`** (sem dedução automática):

1. `artilheiro_nome`, `artilheiro_equipe`, `artilheiro_gols` — o motor só calcula PARCIAL (via
   football-data `/scorers`, plano grátis, pode ficar incompleto perto do fim). Confirme o
   artilheiro oficial da Copa numa fonte confiável (FIFA/ESPN) e digite os 3 campos.
2. `mais_goleadora`, `menos_vazada`, `mais_gols_jogo` — "torneio inteiro" (grupo + mata-mata).
   O motor só mostra parcial ao vivo (`compute_tournament_extras`, nunca escreve em
   `facts.json` sozinho). Confira o parcial mais recente na seção Extras da landing e
   confirme/ajuste o valor final (empate = liste todos, formato lista JSON: `["Time A", "Time B"]`).
3. `jogos_penaltis` — idem: só tem parcial ao vivo (`compute_penalty_partial`, contagem "N até
   agora"). Confirme o número final (é numérico, ex.: `3`) depois do último jogo de mata-mata.
4. `azarao` — decisão manual do organizador desde sempre (o time da lista de zebras que foi
   mais longe) — sem partial nenhum, sempre foi só no fim.
5. **NÃO mexa** em `empates_1f`, `equipe_1o_expulso`, `equipe_1o_gol_contra`, `champion`, `vice`,
   `third` — esses 6 o robô já trava/preenche sozinho (auto-definitivos, não ficam em parcial).

Depois de editar `facts.json`, é só esperar o próximo ciclo do robô (ou rodar `build_data.py`
manualmente) — ele repontua tudo e a landing (Categorias Extras + tela de Encerramento) atualiza
sozinha, sem precisar mexer em mais nada.
