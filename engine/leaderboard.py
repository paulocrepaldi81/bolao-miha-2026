"""
Monta a classificação a partir das apostas pontuadas:
ranking + desempate + movimentação (vs rodada anterior) + pontos em jogo / vivo.

Desempate (PROVISÓRIO — a confirmar com o organizador):
  1) mais pontos  2) mais placares exatos  3) mais acertos de vencedor
  4) ordem de envio (quem entregou antes fica na frente)
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
    knockout_open = True   # v1: sem resultados de mata-mata ainda
    knockout_potential = C.KNOCKOUT_POTENTIAL if knockout_open else 0

    for s in scored:
        info = roster.get(s["alias"].lower(), {"paid": False, "order": 9999})
        s["paid"] = info["paid"]
        s["order"] = info["order"]
        s["points_available"] = (rem_groups + (30 if final_open else 0)
                                 + extras_open_max + knockout_potential)
        s["max_possible"] = s["total"] + s["points_available"]

    # Ordenação + desempate determinístico
    scored.sort(key=lambda s: (-s["total"], -s["exact_scores"], -s["correct_outcomes"], s["order"]))
    leader_total = scored[0]["total"] if scored else 0

    out = []
    for i, s in enumerate(scored, start=1):
        prev = prev_snapshot.get(s["alias"], {})
        prev_rank = prev.get("rank", i)
        out.append({
            "alias": s["alias"],
            "score": s["total"],
            "phase1_points": s["group_pts"],
            "rank": i,
            "previous_rank": prev_rank,
            "rank_change": prev_rank - i,
            "last_match_points": max(0, s["total"] - prev.get("total", s["total"])),
            "exact_scores": s["exact_scores"],
            "correct_outcomes": s["correct_outcomes"],
            "max_possible": s["max_possible"],
            "points_available": s["points_available"],
            "eliminated": (s["total"] + s["points_available"]) < leader_total,
            "paid": s["paid"],
        })
    return out
