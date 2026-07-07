"""
Testes das estatísticas divertidas (gêmeo de aposta, sabedoria do bolão, perfil quente/frio,
jornada de ranking). Rode: cd engine && python3 -m pytest tests -q
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fun_stats as FS


def _bet(alias, preds):
    return {"alias": alias, "group_preds": preds}


def test_twins_identico_e_mais_diferente():
    # A e B apostaram EXATAMENTE igual (distância 0) nos 20 jogos; C apostou tudo diferente.
    base = {f"G{i}": (1, 0) for i in range(20)}
    oposto = {f"G{i}": (0, 3) for i in range(20)}  # |1-0|+|0-3| = 4 por jogo -> dist 80
    bets = [_bet("A", dict(base)), _bet("B", dict(base)), _bet("C", oposto)]
    out = FS.compute_twins(bets)
    assert out["A"]["twin"] == {"aliases": ["B"], "distance": 0}
    assert out["A"]["rival"] == {"aliases": ["C"], "distance": 80}
    assert out["B"]["twin"] == {"aliases": ["A"], "distance": 0}   # simétrico


def test_twins_empate_lista_todos():
    base = {f"G{i}": (1, 0) for i in range(20)}
    igual1 = dict(base)
    igual2 = dict(base)
    bets = [_bet("A", base), _bet("B", igual1), _bet("C", igual2)]
    out = FS.compute_twins(bets)
    # B e C empatam como gêmeos de A (distância 0 com ambos) -> lista os DOIS, não escolhe 1
    assert out["A"]["twin"]["distance"] == 0
    assert out["A"]["twin"]["aliases"] == ["B", "C"]


def test_twins_exige_cobertura_minima():
    # apostas com poucos jogos em comum (< MIN_COMMON_GAMES) não entram no cálculo
    bets = [_bet("A", {"G1": (1, 0)}), _bet("B", {"G1": (1, 0)})]
    out = FS.compute_twins(bets)
    assert out["A"]["twin"] is None and out["A"]["rival"] is None


def test_wisdom_consenso_cravado():
    catalog = [{"match_id": "G1", "home": "Brasil", "away": "Argentina"}]
    results = {"G1": {"status": "finished", "home_score": 2, "away_score": 1}}
    # mediana do bolão bate 2x1 exato; indivíduos variam ao redor
    bets = [_bet("A", {"G1": (2, 1)}), _bet("B", {"G1": (2, 1)}),
            _bet("C", {"G1": (0, 0)}), _bet("D", {"G1": (4, 3)})]
    w = FS.compute_wisdom(bets, results, catalog)
    assert w["games_evaluated"] == 1
    assert w["consensus_avg_error"] == 0.0   # mediana (2,1) == real (2,1)
    assert w["individual_avg_error"] > 0     # C e D erraram
    assert w["pct_better"] == 100.0          # consenso 100% melhor (erro 0)


def test_wisdom_sem_jogo_encerrado_retorna_none():
    catalog = [{"match_id": "G1", "home": "Brasil", "away": "Argentina"}]
    results = {"G1": {"status": "scheduled"}}
    bets = [_bet("A", {"G1": (2, 1)})]
    assert FS.compute_wisdom(bets, results, catalog) is None


def test_goal_profile_quente_e_frio():
    # 10 jogos cada, pra passar do MIN_FILLED_GAMES=10. 6 apostas "médias" formam um núcleo
    # estável (desvio-padrão pequeno) pra que quente/frio realmente cruzem z>1 / z<-1.
    quente = {f"G{i}": (5, 4) for i in range(10)}          # média 9 gols/jogo
    frio = {f"G{i}": (0, 0) for i in range(10)}            # média 0 gols/jogo
    medio = {f"G{i}": (1.5, 1.5) for i in range(10)}       # média 3 gols/jogo
    bets = [_bet("Quente", quente), _bet("Frio", frio)]
    bets += [_bet(f"Medio{i}", medio) for i in range(6)]
    out = FS.compute_goal_profile(bets)
    assert out["Quente"]["z"] > 1 and out["Quente"]["label"] == "quente"
    assert out["Frio"]["z"] < -1 and out["Frio"]["label"] == "frio"
    assert out["Medio0"]["label"] == "equilibrado"


def test_goal_profile_poucos_jogos_vira_none():
    bets = [_bet("A", {"G1": (1, 0)}), _bet("B", {f"G{i}": (1, 0) for i in range(15)})]
    out = FS.compute_goal_profile(bets)
    assert out["A"] is None   # só 1 jogo preenchido (< MIN_FILLED_GAMES)


def test_rank_history_downsample_1_por_dia_e_ignora_alias_ausente():
    history = [
        {"ts": "2026-06-12T09:00:00-03:00", "ranks": {"X": {"rank": 2, "total": 10}}},
        {"ts": "2026-06-12T15:00:00-03:00", "ranks": {"X": {"rank": 1, "total": 20}}},  # mesmo dia, sobrescreve
        {"ts": "2026-06-13T09:00:00-03:00", "ranks": {"X": {"rank": 1, "total": 25}, "Y": {"rank": 2, "total": 20}}},
    ]
    dates, series = FS.compute_rank_history(history, ["X", "Y"])
    assert dates == ["2026-06-12", "2026-06-13"]
    assert series["X"] == [[1, 20], [1, 25]]     # dia 12 ficou com o ÚLTIMO snapshot do dia (15h, não 9h)
    assert series["Y"] == [None, [2, 20]]        # Y não existia no dia 12 -> None, sem quebrar


def test_rank_history_vazio_e_fail_safe():
    dates, series = FS.compute_rank_history([], ["X"])
    assert dates == [] and series == {"X": []}


def _p(alias, rank, score):
    return {"alias": alias, "rank": rank, "score": score}


def test_classico_vizinhos_ignora_empate_acha_menor_gap_positivo():
    # A e B empatados em 1º (gap 0, não é disputa) -> deve pular pro próximo par real: B/C (gap 1)
    parts = [_p("A", 1, 100), _p("B", 1, 100), _p("C", 3, 99), _p("D", 4, 80)]
    out = FS.compute_classico_vizinhos(parts)
    assert out == {"a": "B", "a_rank": 1, "b": "C", "b_rank": 3, "gap": 1}


def test_classico_vizinhos_empate_no_menor_gap_fica_com_o_mais_alto():
    # dois candidatos empatam no menor gap (1): topo(100/99) e base(50/49) -> fica com o do topo
    parts = [_p("A", 1, 100), _p("B", 2, 99), _p("C", 3, 50), _p("D", 4, 49)]
    out = FS.compute_classico_vizinhos(parts)
    assert out == {"a": "A", "a_rank": 1, "b": "B", "b_rank": 2, "gap": 1}


def test_classico_vizinhos_todo_mundo_empatado_retorna_none():
    parts = [_p("A", 1, 50), _p("B", 1, 50), _p("C", 1, 50)]
    assert FS.compute_classico_vizinhos(parts) is None


def test_novela_conta_troca_de_posicao_ignorando_empate():
    history = [
        {"ranks": {"A": {"rank": 1}, "B": {"rank": 2}}},   # A na frente
        {"ranks": {"A": {"rank": 1}, "B": {"rank": 1}}},   # empate -> não conta como troca
        {"ranks": {"A": {"rank": 2}, "B": {"rank": 1}}},   # B ultrapassa A -> 1ª troca
        {"ranks": {"A": {"rank": 1}, "B": {"rank": 2}}},   # A retoma -> 2ª troca
    ]
    out = FS.compute_novela_ultrapassagens(history, ["A", "B"])
    assert out == {"a": "A", "b": "B", "count": 2}


def test_novela_sem_troca_retorna_none():
    history = [
        {"ranks": {"A": {"rank": 1}, "B": {"rank": 2}}},
        {"ranks": {"A": {"rank": 1}, "B": {"rank": 2}}},
    ]
    assert FS.compute_novela_ultrapassagens(history, ["A", "B"]) is None


def test_novela_historico_insuficiente_retorna_none():
    history = [{"ranks": {"A": {"rank": 1}, "B": {"rank": 2}}}]
    assert FS.compute_novela_ultrapassagens(history, ["A", "B"]) is None
