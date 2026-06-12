"""
Regras de pontuação do Bolão Miha 2026. Funções puras e testáveis.

Resumo das regras (aba "Regras"):
  - Vencedor/empate correto: 3 pts (normal) ou 5 pts (especial = célula verde).
  - Bônus por placar exato: nº de gols na partida, mínimo 2 (só se cravar o placar).
  - Mata-mata: pontua pelo resultado até a prorrogação; pênaltis só apontam quem avança.
  - Classificação final: campeão 15, vice 10, 3º 5; equipe no top-3 em posição errada: 3.
  - Artilheiro: nome 8, equipe 4, gols 3, +5 se acertar os três.
  - 8 curiosidades: 5 pts cada.
"""
import config as C


def _sign(d):
    return (d > 0) - (d < 0)


def score_match(pred_h, pred_a, act_h, act_a, special=False):
    """Pontos de um jogo. pred/act são placares inteiros; act None = não disputado."""
    if act_h is None or act_a is None:
        return 0
    if pred_h is None or pred_a is None:
        return 0
    pts = 0
    if _sign(pred_h - pred_a) == _sign(act_h - act_a):           # vencedor/empate correto
        pts += C.PTS_OUTCOME_SPECIAL if special else C.PTS_OUTCOME_NORMAL
        if pred_h == act_h and pred_a == act_a:                  # placar exato
            pts += max(C.BONUS_MIN, act_h + act_a)
    return pts


def score_final(pred_final, real_final):
    """Classificação final. pred/real = dict {champion, vice, third} (nomes de seleções)."""
    if not real_final or not any(real_final.values()):
        return 0
    real = {k: (v.strip() if v else v) for k, v in real_final.items()}
    real_top3 = {v for v in real.values() if v}
    slot_pts = {"champion": C.PTS_CHAMP, "vice": C.PTS_VICE, "third": C.PTS_THIRD}
    pts = 0
    for slot, full in slot_pts.items():
        guess = (pred_final.get(slot) or "").strip()
        if not guess:
            continue
        if guess == real.get(slot):
            pts += full                      # posição exata
        elif guess in real_top3:
            pts += C.PTS_TOP3_WRONG_POS      # no top-3, posição errada
    return pts


def score_extras(pred, facts):
    """Categorias extras. facts = dict com os valores reais (None = ainda não definido)."""
    pts = 0
    # Artilheiro
    nome_ok = facts.get("artilheiro_nome") and _eq(pred.get("artilheiro_nome"), facts["artilheiro_nome"])
    equipe_ok = facts.get("artilheiro_equipe") and _eq(pred.get("artilheiro_equipe"), facts["artilheiro_equipe"])
    gols_ok = facts.get("artilheiro_gols") is not None and pred.get("artilheiro_gols") == facts["artilheiro_gols"]
    if nome_ok:
        pts += C.PTS_ART_NOME
    if equipe_ok:
        pts += C.PTS_ART_EQUIPE
    if gols_ok:
        pts += C.PTS_ART_GOLS
    if nome_ok and equipe_ok and gols_ok:
        pts += C.PTS_ART_BONUS
    # Curiosidades
    for k in C.CURIOSIDADES:
        if facts.get(k) is not None and _match_fact(pred.get(k), facts[k]):
            pts += C.PTS_CURIOSIDADE
    return pts


def _eq(a, b):
    return a is not None and b is not None and str(a).strip().lower() == str(b).strip().lower()


def _match_fact(pred, real):
    """Curiosidade pode ser número (empates, pênaltis...) ou nome de seleção."""
    if isinstance(real, (int, float)) or isinstance(pred, (int, float)):
        try:
            return int(pred) == int(real)
        except (TypeError, ValueError):
            return False
    return _eq(pred, real)


def score_bet(bet, results, catalog, real_final, facts):
    """Pontuação total de uma aposta + detalhamento.

    results = {match_id: {"home_score":h, "away_score":a, "status":...}}
    catalog = lista de jogos (define special por match_id)
    """
    special = {m["match_id"]: m["special"] for m in catalog}
    by_match, group_pts, exact = {}, 0, 0
    for mid, (ph, pa) in bet["group_preds"].items():
        r = results.get(mid)
        # só pontua jogo ENCERRADO com placar — nunca ao vivo nem placar residual
        if not r or r.get("status") != "finished" or r.get("home_score") is None:
            continue
        p = score_match(ph, pa, r["home_score"], r["away_score"], special.get(mid, False))
        by_match[mid] = p
        group_pts += p
        if ph == r["home_score"] and pa == r["away_score"]:
            exact += 1
    final_pts = score_final(bet["final"], real_final)
    extra_pts = score_extras(bet["extras"], facts)
    total = group_pts + final_pts + extra_pts
    return {
        "alias": bet["alias"],
        "total": total,
        "group_pts": group_pts,
        "final_pts": final_pts,
        "extra_pts": extra_pts,
        "exact_scores": exact,
        "correct_outcomes": sum(1 for v in by_match.values() if v > 0),
        "by_match": by_match,
    }
