"""
Testes do leaderboard.build — o "miolo" de ranking/prêmio que faltava cobertura:
rank de competição (empate), prize_pos só entre pagantes, in_the_money (empate na borda),
Bom de Palpite (líder pagante + divide), e day_points (soma só os jogos da rodada).
Rode: cd engine && python3 -m pytest tests -q
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import leaderboard as L


def _build(specs, round_mids=frozenset()):
    """specs: dict alias -> {total, group_pts?, paid?, exact?, correct?, by_match?}.
    Constrói scored+roster mínimos e roda L.build (catálogo/resultados/facts vazios)."""
    scored, roster = [], {}
    for i, (a, d) in enumerate(specs.items()):
        scored.append({
            "alias": a, "total": d["total"], "group_pts": d.get("group_pts", d["total"]),
            "exact_scores": d.get("exact", 0), "correct_outcomes": d.get("correct", 0),
            "by_match": d.get("by_match", {}),
        })
        roster[a.lower()] = {"paid": d.get("paid", True), "order": i}
    out = L.build(scored, roster, [], {}, {}, {}, {}, round_mids)
    return {p["alias"]: p for p in out}


def test_rank_competicao_com_empate():
    r = _build({"A": {"total": 10}, "B": {"total": 8}, "C": {"total": 8}, "D": {"total": 5}})
    assert (r["A"]["rank"], r["B"]["rank"], r["C"]["rank"], r["D"]["rank"]) == (1, 2, 2, 4)


def test_in_the_money_empate_na_borda_inclui_todos():
    # 5 pagantes com empate no 4º lugar (ranks 1,2,2,4,4) → os 5 estão na grana
    r = _build({"A": {"total": 10}, "B": {"total": 8}, "C": {"total": 8},
                "D": {"total": 6}, "E": {"total": 6}})
    assert all(r[a]["in_the_money"] for a in "ABCDE")


def test_prize_pos_so_entre_pagantes_cafe_nao_ocupa_vaga():
    # café-com-leite no topo NÃO toma posição de prêmio nem entra na grana
    r = _build({"Cafe": {"total": 20, "paid": False}, "P1": {"total": 10}, "P2": {"total": 9}})
    assert r["Cafe"]["prize_pos"] is None and r["Cafe"]["in_the_money"] is False
    assert r["P1"]["prize_pos"] == 1 and r["P2"]["prize_pos"] == 2


def test_bom_palpite_e_lider_pagante_da_1a_fase():
    # café tem mais pontos de 1ª fase, mas o Bom de Palpite é o líder PAGANTE
    r = _build({"Cafe": {"total": 30, "group_pts": 30, "paid": False},
                "P1": {"total": 20, "group_pts": 20}, "P2": {"total": 18, "group_pts": 18}})
    assert r["Cafe"]["bom_palpite"] is False
    assert r["P1"]["bom_palpite"] is True and r["P1"]["bom_palpite_split"] is False


def test_bom_palpite_empate_divide():
    r = _build({"P1": {"total": 20, "group_pts": 20}, "P2": {"total": 19, "group_pts": 20},
                "P3": {"total": 5, "group_pts": 5}})
    assert r["P1"]["bom_palpite"] and r["P2"]["bom_palpite"]
    assert r["P1"]["bom_palpite_split"] and r["P2"]["bom_palpite_split"]


def test_day_points_soma_so_jogos_da_rodada():
    r = _build({"A": {"total": 10, "by_match": {"K1": 5, "L4": 3, "A1": 2}}},
               round_mids=frozenset({"K1", "L4"}))
    assert r["A"]["day_points"] == 8   # 5+3 (ignora A1, fora da rodada)


def test_phase1_rank_por_pontos_da_1a_fase():
    # rank da 1ª fase usa group_pts (não o total) e inclui todos
    r = _build({"A": {"total": 5, "group_pts": 30}, "B": {"total": 40, "group_pts": 10}})
    assert r["A"]["phase1_rank"] == 1 and r["B"]["phase1_rank"] == 2


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
