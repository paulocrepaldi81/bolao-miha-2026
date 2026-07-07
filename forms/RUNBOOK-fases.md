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

2. **Crie o Form** (reusa `forms/criar_form_R32.gs`):
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
   - `form_url`: o link público do Form (o que vai no zap). Faz aparecer o botão **"Atualizar meus palpites do mata-mata"** na landing.
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
