"""
Monta a classificação a partir das apostas pontuadas:
ranking + desempate + movimentação (vs rodada anterior) + pontos em jogo / vivo.

Desempate (regra do dono): EMPATE em pontos = MESMA posição (mesmo rank). Os empatados
DIVIDEM, em partes iguais, os prêmios das posições que ocupam (ex.: 3 empatados em 1º dividem
1º+2º+3º; 5 empatados em 4º dividem o 4º). A ordem da LISTA dentro do empate é só visual
(mais placares exatos → mais acertos → ordem de envio).
"""
import config as C


def remaining_group_points(catalog, results):
    """Máximo ainda obtível nos jogos de grupo não disputados (1 aposta qualquer)."""
    total = 0
    for m in catalog:
        r = results.get(m["match_id"])
        # jogo ainda rende pontos se NÃO estiver encerrado
        if not r or r.get("status") != "finished" or r.get("home_score") is None:
            base = C.PTS_OUTCOME_SPECIAL if m["special"] else C.PTS_OUTCOME_NORMAL
            total += base + C.MAX_BONUS_CAP
    return total


def build(scored, roster, catalog, results, real_final, facts, prev_snapshot):
    """
    scored: lista de dicts (saída de scoring.score_bet)
    roster: {alias_lower: {"paid":bool, "order":int}}
    prev_snapshot: {alias: {"rank":int, "total":int}}  (rodada anterior; pode ser {})
    Retorna lista de participantes prontos para o data.json + flags de movimento.
    """
    rem_groups = remaining_group_points(catalog, results)
    final_open = not (real_final and any(real_final.values()))
    extras_open_max = sum([
        (0 if facts.get("artilheiro_nome") else C.PTS_ART_NOME),
        (0 if facts.get("artilheiro_equipe") else C.PTS_ART_EQUIPE),
        (0 if facts.get("artilheiro_gols") is not None else C.PTS_ART_GOLS),
        C.PTS_ART_BONUS if not all(facts.get(k) not in (None, "") for k in
                                   ("artilheiro_nome", "artilheiro_equipe", "artilheiro_gols")) else 0,
    ]) + C.PTS_CURIOSIDADE * sum(1 for k in C.CURIOSIDADES if facts.get(k) in (None, ""))
    # "máx possível" REAL: só o que o motor de fato pontua = jogos de grupo restantes +
    # classificação final (30) + categorias extras. O mata-mata jogo-a-jogo ainda não é
    # pontuado (v1); quando entrar (v2), os pontos dele somam aqui de verdade — sem placeholder.

    for s in scored:
        info = roster.get(s["alias"].lower(), {"paid": False, "order": 9999})
        s["paid"] = info["paid"]
        s["order"] = info["order"]
        s["points_available"] = rem_groups + (30 if final_open else 0) + extras_open_max
        s["max_possible"] = s["total"] + s["points_available"]

    # Ordenação + desempate determinístico
    scored.sort(key=lambda s: (-s["total"], -s["exact_scores"], -s["correct_outcomes"], s["order"]))
    leader_total = scored[0]["total"] if scored else 0

    out = []
    for i, s in enumerate(scored, start=1):
        # Ranking de COMPETIÇÃO: mesmos pontos = mesmo rank (ex.: 1,1,3). Reflete a regra de
        # prêmio (empatados dividem os prêmios das posições que ocupam). A ordem da lista é a do
        # sort acima (estável); só o NÚMERO do rank empata.
        rank = 1 + sum(1 for o in scored if o["total"] > s["total"])
        prev = prev_snapshot.get(s["alias"], {})
        prev_rank = prev.get("rank", rank)
        out.append({
            "alias": s["alias"],
            "score": s["total"],
            "phase1_points": s["group_pts"],
            "rank": rank,
            "previous_rank": prev_rank,
            "rank_change": prev_rank - rank,
            "last_match_points": max(0, s["total"] - prev.get("total", s["total"])),
            "exact_scores": s["exact_scores"],
            "correct_outcomes": s["correct_outcomes"],
            "max_possible": s["max_possible"],
            "points_available": s["points_available"],
            # + KNOCKOUT_POTENTIAL: o mata-mata ainda não pontua (v1), mas vale pontos de verdade —
            # sem essa folga, ao fechar a 1ª fase alguém seria marcado "eliminado" sem estar.
            "eliminated": (s["total"] + s["points_available"] + C.KNOCKOUT_POTENTIAL) < leader_total,
            "paid": s["paid"],
        })
    return out
