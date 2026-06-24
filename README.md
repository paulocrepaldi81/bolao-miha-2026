# ⚽ Bolão Miha 2026

Sistema completo do bolão da Copa do Mundo FIFA 2026 — tradição da família e amigos desde 2006.

🔗 **Site (leaderboard ao vivo):** https://paulocrepaldi81.github.io/bolao-miha-2026/
(host oficial: **GitHub Pages** · link privado/não-listado)

## Como funciona

```
planilhas dos apostadores → motor de pontuação → data.json → GitHub Pages → site no ar
                                    ↑
       robô (GitHub Actions, disparado por pinger externo) busca placares a cada ~5 min
```

| Pasta | O quê |
|---|---|
| [`landing-page/`](landing-page/) | O site (HTML/CSS/JS estático) — leaderboard, jogos, prêmio, estatísticas, Hall da Fama |
| [`engine/`](engine/) | Motor de pontuação em Python (lê as planilhas, aplica as regras, gera o `data.json`) — [docs](engine/README.md) |
| [`.github/workflows/`](.github/workflows/) | Robô que busca placares e republica o site automaticamente |

## Estado atual

- ✅ Site no ar com os dados reais (Copa em andamento)
- ✅ Robô ativo: busca placares e republica a cada ~5 min
- ✅ 88 apostas carregadas (83 pagas)

## Regras do bolão (resumo)

Acertou vencedor/empate: **3 pts** (jogo normal) ou **5 pts** (especial). Placar exato: bônus = nº de gols (mín. 2).
Campeão **15** · Vice **10** · 3º **5**. Artilheiro 8/4/3 (+5). Curiosidades 5 cada.
Prêmio (só apostas pagas, R$60): Lanterna de Ouro recebe a aposta de volta; do restante, 40% campeão · 25% vice · 10% 3º · 5% 4º · 20% Bom de Palpite (1ª fase).

> Bolão de **palpites** entre amigos, por pontos e diversão. Não é casa de apostas. 🎉
> Organização: Ricardo Mihalik · Site e motor: Paulo Crepaldi + Claude
