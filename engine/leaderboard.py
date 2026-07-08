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


def remaining_knockout_points(ko_results):
    """Máximo ainda obtível nos slots do MATA-MATA não encerrados (1 aposta qualquer) — mesma
    lógica de remaining_group_points, só que sobre config.KNOCKOUT_CELLS. Substitui o antigo
    buffer fixo KNOCKOUT_POTENTIAL=250: antes 'eliminated'/'max_possible' ignoravam de vez os
    pontos ainda em jogo no chaveamento; agora é uma cota real (upper bound honesto — nunca
    subestima, então nunca elimina errado, só não finge que o mata-mata vale infinito)."""
    total = 0
    for slot, _, _ in C.KNOCKOUT_CELLS:
        r = (ko_results or {}).get(slot)
        if not r or r.get("status") != "finished" or r.get("home_score") is None:
            base = C.PTS_OUTCOME_SPECIAL if slot in C.SPECIAL_SLOTS else C.PTS_OUTCOME_NORMAL
            total += base + C.MAX_BONUS_CAP
    return total


def build(scored, roster, catalog, results, real_final, facts, prev_snapshot, round_mids=frozenset(),
          ko_results=None):
    """
    scored: lista de dicts (saída de scoring.score_bet)
    roster: {alias_lower: {"paid":bool, "order":int}}
    prev_snapshot: {alias: {"rank":int, "total":int}}  (rodada anterior; pode ser {})
    round_mids: set de match_ids da RODADA corrente (jogos da janela 05:00→04:59 SP do dia
        seguinte) — usado só para somar "day_points" por aposta. É um valor PURAMENTE
        informativo de exibição: não afeta rank, movimentação, eliminado nem estatística.
    Retorna lista de participantes prontos para o data.json + flags de movimento.
    """
    rem_groups = remaining_group_points(catalog, results)
    rem_knockout = remaining_knockout_points(ko_results)
    final_open = not (real_final and any(real_final.values()))
    extras_open_max = sum([
        (0 if facts.get("artilheiro_nome") else C.PTS_ART_NOME),
        (0 if facts.get("artilheiro_equipe") else C.PTS_ART_EQUIPE),
        (0 if facts.get("artilheiro_gols") is not None else C.PTS_ART_GOLS),
        C.PTS_ART_BONUS if not all(facts.get(k) not in (None, "") for k in
                                   ("artilheiro_nome", "artilheiro_equipe", "artilheiro_gols")) else 0,
    ]) + C.PTS_CURIOSIDADE * sum(1 for k in C.CURIOSIDADES if facts.get(k) in (None, ""))
    # "máx possível" REAL: jogos de grupo restantes + slots do mata-mata ainda não encerrados +
    # classificação final (30) + categorias extras — tudo que o motor de fato ainda pode pontuar,
    # sem placeholder/buffer mágico (era KNOCKOUT_POTENTIAL=250 fixo até 08/jul).

    for s in scored:
        info = roster.get(s["alias"].lower(), {"paid": False, "order": 9999})
        s["paid"] = info["paid"]
        s["order"] = info["order"]
        s["points_available"] = rem_groups + rem_knockout + (30 if final_open else 0) + extras_open_max
        s["max_possible"] = s["total"] + s["points_available"]

    # Ordenação + desempate determinístico
    scored.sort(key=lambda s: (-s["total"], -s["exact_scores"], -s["correct_outcomes"], s["order"]))
    leader_total = scored[0]["total"] if scored else 0

    # ---- Semântica ÚNICA de ranking/prêmio (motor manda; o front só exibe) ----
    # Tudo abaixo é DERIVADO da mesma pontuação; cada bloco da página depois filtra o que lhe
    # cabe (Classificação = total; Bom de Palpite = só 1ª fase). Centralizar aqui evita que a
    # página recalcule rank/prêmio por conta própria e acabe divergindo entre blocos.
    all_phase1   = [s["group_pts"] for s in scored]                 # 1ª fase de todos (pago ou não)
    paid_totals  = [s["total"] for s in scored if s["paid"]]        # total só dos pagantes
    paid_phase1  = [s["group_pts"] for s in scored if s["paid"]]    # 1ª fase só dos pagantes
    # Bom de Palpite: maior pontuação de 1ª fase ENTRE PAGANTES (empate divide os 20%)
    bp_top = max(paid_phase1) if paid_phase1 else None
    bp_n   = sum(1 for v in paid_phase1 if v == bp_top) if bp_top is not None else 0

    out = []
    for i, s in enumerate(scored, start=1):
        # Ranking de COMPETIÇÃO: mesmos pontos = mesmo rank (ex.: 1,1,3). Reflete a regra de
        # prêmio (empatados dividem os prêmios das posições que ocupam). A ordem da lista é a do
        # sort acima (estável); só o NÚMERO do rank empata.
        rank = 1 + sum(1 for o in scored if o["total"] > s["total"])
        prev = prev_snapshot.get(s["alias"], {})
        prev_rank = prev.get("rank", rank)
        # rank de competição da 1ª FASE (mesma lógica do rank geral, mas por group_pts) — base do
        # Bom de Palpite. Inclui todos; o vencedor do prêmio (abaixo) é só entre pagantes.
        phase1_rank = 1 + sum(1 for v in all_phase1 if v > s["group_pts"])
        # posição de PRÊMIO entre PAGANTES (por total). Empate = mesma posição → empatados dividem.
        prize_pos = (1 + sum(1 for v in paid_totals if v > s["total"])) if s["paid"] else None
        in_money = bool(s["paid"] and prize_pos is not None and prize_pos <= 4)
        is_bp = bool(s["paid"] and bp_top is not None and s["group_pts"] == bp_top)
        out.append({
            "alias": s["alias"],
            "score": s["total"],
            "phase1_points": s["group_pts"],
            "knockout_pts": s.get("knockout_pts", 0),   # pontos do mata-mata (0 na fase de grupos)
            "rank": rank,
            "previous_rank": prev_rank,
            "rank_change": prev_rank - rank,
            "last_match_points": max(0, s["total"] - prev.get("total", s["total"])),
            # pontos da pessoa NA RODADA corrente = soma dos pontos dos jogos dessa rodada
            # (só jogos encerrados entram em by_match). Não soma final/artilheiro/curiosidades
            # — "rodada" são os JOGOS do dia. Campo de exibição; não entra em nenhum cálculo.
            "day_points": max(0, sum(s.get("by_match", {}).get(mid, 0) for mid in round_mids)),
            "exact_scores": s["exact_scores"],
            "correct_outcomes": s["correct_outcomes"],
            "max_possible": s["max_possible"],
            "points_available": s["points_available"],
            # "matematicamente vivo": points_available já inclui o mata-mata restante de verdade
            # (remaining_knockout_points) — nunca elimina errado, sem depender de buffer fixo.
            "eliminated": (s["total"] + s["points_available"]) < leader_total,
            "paid": s["paid"],
            # ---- flags de ranking/prêmio (derivadas; o front só lê, não recalcula) ----
            "phase1_rank": phase1_rank,        # posição na 1ª fase (Bom de Palpite)
            "prize_pos": prize_pos,            # posição entre pagantes por total (None se café)
            "in_the_money": in_money,          # pago e dentro das 4 posições de prêmio (selo 💰)
            "bom_palpite": is_bp,              # líder pagante da 1ª fase (leva os 20%)
            "bom_palpite_split": bool(is_bp and bp_n > 1),   # empate no topo pagante → divide
        })
    return out
