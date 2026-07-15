"""
compute_tournament_extras (fetch_facts.py) — mais_gols_jogo/mais_goleadora/menos_vazada contam
o TORNEIO INTEIRO (grupo + mata-mata encerrado). Bug real corrigido 07/jul: antes só olhava os
72 jogos de grupo, deixando o parcial "ao vivo" parado mesmo com jogos de mata-mata já encerrados
(chegou a mostrar um time já eliminado como líder de "sem sofrer gol"). Rode:
cd engine && python3 -m pytest tests -q
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_facts as FF


def _j(home, away, hs, aws):
    return ({"home": home, "away": away}, {"home_score": hs, "away_score": aws})


def test_vazio_retorna_dict_vazio():
    assert FF.compute_tournament_extras([]) == {}


def test_combina_grupo_e_mata_mata_e_muda_o_lider():
    # Sem mata-mata: GER lidera sozinho com 4 gols (POR/ARG/FRA ficam menores). Com o jogo de
    # mata-mata ARG x GER (5x4) somado, os dois empatam em 8 -- é o cenário exato do bug: só
    # olhando o grupo, o líder real (e o empate) ficam escondidos.
    grupo = [
        _j("POR", "KOR", 3, 1),
        _j("ARG", "JPN", 3, 0),
        _j("FRA", "ESP", 1, 1),
        _j("GER", "ITA", 4, 0),
    ]
    mata_mata = [
        _j("POR", "FRA", 1, 1),   # R32, decidido nos pênaltis -> placar aqui é só até a prorrogação
        _j("ARG", "GER", 5, 4),   # R16 -- 9 gols, novo máximo, e está no MATA-MATA
        _j("ESP", "ITA", 0, 0),   # R32, decidido nos pênaltis
        _j("JPN", "KOR", 1, 0),   # R16
    ]
    out = FF.compute_tournament_extras(grupo + mata_mata)
    assert out["mais_gols_jogo"] == "9 gols (ARG 5×4 GER)"
    assert out["mais_goleadora"] == "2 seleções com 8 gols: ARG, GER"   # empate explícito
    assert out["menos_vazada"] == "ESP (1 sofrido(s))"                  # vencedor único


def test_so_grupo_sem_mata_mata_ainda_funciona():
    # nenhum jogo de mata-mata encerrado ainda -> comportamento idêntico ao de antes do fix
    grupo = [_j("BRA", "ARG", 2, 1), _j("FRA", "GER", 1, 1)]
    out = FF.compute_tournament_extras(grupo)
    assert out["mais_gols_jogo"] == "3 gols (BRA 2×1 ARG)"
    assert out["mais_goleadora"] == "BRA (2 gols)"


def test_menos_vazada_zero_gols_sofridos_lista_todos_empatados():
    jogos = [_j("A", "B", 3, 0), _j("C", "D", 2, 0), _j("A", "C", 1, 0)]
    # sofridos: B=3, D=2, C=1(+0 do 2º jogo dela como mandante)=1, A=0
    out = FF.compute_tournament_extras(jogos)
    assert out["menos_vazada"] == "A (0 sofrido(s))"


def test_mais_gols_jogo_com_multiplos_jogos_empatados():
    jogos = [_j("A", "B", 3, 3), _j("C", "D", 4, 2), _j("E", "F", 1, 0)]
    out = FF.compute_tournament_extras(jogos)
    assert "6 gols — 2 jogos" in out["mais_gols_jogo"]
    assert "A 3×3 B" in out["mais_gols_jogo"] and "C 4×2 D" in out["mais_gols_jogo"]


def test_penalty_partial_conta_so_jogos_encerrados_decididos_nos_penaltis():
    ko_fix = {
        "R32-01": {"status": "finished", "decided_by": "pen"},
        "R32-02": {"status": "finished", "decided_by": "normal"},
        "R32-03": {"status": "finished", "decided_by": "pen"},
        "R32-04": {"status": "scheduled", "decided_by": None},   # ainda não jogado -> não conta
    }
    assert FF.compute_penalty_partial(ko_fix, 32) == "2 até agora (3/32 jogos de mata-mata encerrados)"


def test_penalty_partial_sem_jogo_encerrado_retorna_none():
    ko_fix = {"QF-01": {"status": "scheduled", "decided_by": None}}
    assert FF.compute_penalty_partial(ko_fix, 32) is None


def test_penalty_partial_bracket_vazio_retorna_none():
    assert FF.compute_penalty_partial({}, 32) is None


def test_penalty_partial_zero_penaltis_ainda_mostra_contagem():
    ko_fix = {"R32-01": {"status": "finished", "decided_by": "normal"}}
    assert FF.compute_penalty_partial(ko_fix, 32) == "0 até agora (1/32 jogos de mata-mata encerrados)"


# ---- compute_final_classification: campeão/vice/3º REAIS via ESPN (não o palpite de ninguém) ----

def test_classificacao_final_vazia_sem_FIN_nem_TER():
    assert FF.compute_final_classification({}) == {}


def test_classificacao_final_FIN_ausente_nao_gera_champion():
    ko_fix = {"TER": {"status": "finished", "winner": "França", "home": "França", "away": "Inglaterra"}}
    out = FF.compute_final_classification(ko_fix)
    assert "champion" not in out and "vice" not in out
    assert out["third"] == "França"


def test_classificacao_final_FIN_nao_encerrado_ainda_nao_gera_nada():
    ko_fix = {"FIN": {"status": "scheduled", "winner": None, "home": "Espanha", "away": "Argentina"}}
    assert FF.compute_final_classification(ko_fix) == {}


def test_classificacao_final_FIN_encerrado_sem_winner_ainda_nao_gera_nada():
    # ESPN pode marcar 'finished' um instante antes de popular o 'winner' -- fail-safe, espera
    ko_fix = {"FIN": {"status": "finished", "winner": None, "home": "Espanha", "away": "Argentina"}}
    assert FF.compute_final_classification(ko_fix) == {}


def test_classificacao_final_so_FIN_TER_ainda_pendente():
    # Final decidida antes do 3º lugar (times diferentes) -- champion/vice já saem, third não
    ko_fix = {"FIN": {"status": "finished", "winner": "Espanha", "home": "Espanha", "away": "Argentina"}}
    out = FF.compute_final_classification(ko_fix)
    assert out == {"champion": "Espanha", "vice": "Argentina"}


def test_classificacao_final_vice_e_o_time_perdedor_nao_o_mandante():
    # o vencedor é o AWAY (Argentina) -- vice tem que ser o HOME (Espanha), não sempre "o outro campo fixo"
    ko_fix = {"FIN": {"status": "finished", "winner": "Argentina", "home": "Espanha", "away": "Argentina"}}
    out = FF.compute_final_classification(ko_fix)
    assert out["champion"] == "Argentina" and out["vice"] == "Espanha"


def test_classificacao_final_completa_FIN_e_TER():
    ko_fix = {
        "FIN": {"status": "finished", "winner": "Espanha", "home": "Espanha", "away": "Argentina"},
        "TER": {"status": "finished", "winner": "Inglaterra", "home": "França", "away": "Inglaterra"},
    }
    assert FF.compute_final_classification(ko_fix) == {
        "champion": "Espanha", "vice": "Argentina", "third": "Inglaterra"}


def test_classificacao_final_reflete_vencedor_pos_penaltis():
    # dado real desta Copa (R32-01): placar que pontua fica empatado, mas o winner da ESPN já
    # reflete quem avançou de verdade nos pênaltis -- a função só lê o campo, não recalcula nada.
    ko_fix = {"TER": {"status": "finished", "winner": "Paraguai", "home": "Paraguai", "away": "Alemanha",
                      "decided_by": "pen", "pen_home": 4, "pen_away": 3}}
    assert FF.compute_final_classification(ko_fix)["third"] == "Paraguai"
