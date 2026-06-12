# ⚽ Bolão Miha 2026

Sistema completo do bolão da Copa do Mundo FIFA 2026 — tradição da família e amigos desde 2006.

🔗 **Site (leaderboard ao vivo):** https://bolaomiha26.netlify.app

## Como funciona

```
planilhas dos apostadores → motor de pontuação → data.json → Netlify → site no ar
                                    ↑
                  robô (GitHub Actions) busca placares oficiais a cada 20 min
```

| Pasta | O quê |
|---|---|
| [`landing-page/`](landing-page/) | O site (HTML/CSS/JS estático) — leaderboard, jogos, prêmio, estatísticas, Hall da Fama |
| [`engine/`](engine/) | Motor de pontuação em Python (lê as planilhas, aplica as regras, gera o `data.json`) — [docs](engine/README.md) |
| [`.github/workflows/`](.github/workflows/) | Robô que busca placares e republica o site automaticamente |

## Estado atual

- ✅ Site no ar (modo protótipo, dados de exemplo)
- ⏸️ Robô em modo de espera (liga quando as apostas reais forem carregadas)
- ⏳ Aguardando as planilhas das 84 apostas

## Regras do bolão (resumo)

Acertou vencedor/empate: **3 pts** (jogo normal) ou **5 pts** (especial). Placar exato: bônus = nº de gols (mín. 2).
Campeão **15** · Vice **10** · 3º **5**. Artilheiro 8/4/3 (+5). Curiosidades 5 cada.
Prêmio (só apostas pagas, R$60): Lanterna de Ouro recebe a aposta de volta; do restante, 40% campeão · 25% vice · 10% 3º · 5% 4º · 20% Bom de Palpite (1ª fase).

> Bolão de **palpites** entre amigos, por pontos e diversão. Não é casa de apostas. 🎉
> Organização: Ricardo Mihalik · Site e motor: Paulo Crepaldi + Claude
