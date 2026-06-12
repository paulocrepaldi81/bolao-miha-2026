"""
Testes unitários da pontuação. Rode:  python3 -m pytest engine/tests -q
(ou:  cd engine && python3 -m pytest tests -q)
Cobrem os exemplos validados com o usuário + casos de borda.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scoring as S


# ---------- score_match ----------
def test_placar_exato_vitoria():
    assert S.score_match(2, 1, 2, 1) == 6        # 3 (vencedor) + 3 (gols)

def test_empate_exato_zero_a_zero():
    assert S.score_match(0, 0, 0, 0) == 5        # 3 + bônus mínimo 2

def test_empate_correto_placar_errado():
    assert S.score_match(1, 1, 0, 0) == 3        # acertou empate, placar errado

def test_vencedor_correto_placar_errado():
    assert S.score_match(3, 0, 1, 0) == 3

def test_resultado_errado():
    assert S.score_match(2, 1, 0, 2) == 0

def test_jogo_especial_vale_mais():
    assert S.score_match(2, 1, 2, 1, special=True) == 8   # 5 + 3

def test_jogo_nao_disputado():
    assert S.score_match(2, 1, None, None) == 0

def test_palpite_em_branco():
    assert S.score_match(None, None, 1, 0) == 0

def test_bonus_grande():
    assert S.score_match(3, 2, 3, 2) == 8        # 3 + 5 gols


# ---------- score_final ----------
REAL = {"champion": "Brasil", "vice": "França", "third": "Argentina"}

def test_final_tudo_certo():
    assert S.score_final({"champion": "Brasil", "vice": "França", "third": "Argentina"}, REAL) == 30

def test_final_posicao_errada():
    # acerta times do top-3 mas troca vice/3º → 15 (campeão) + 3 + 3
    assert S.score_final({"champion": "Brasil", "vice": "Argentina", "third": "França"}, REAL) == 21

def test_final_um_fora_do_top3():
    assert S.score_final({"champion": "Brasil", "vice": "Espanha", "third": "Argentina"}, REAL) == 20  # 15+0+5

def test_final_nao_definido():
    assert S.score_final({"champion": "Brasil"}, {"champion": None, "vice": None, "third": None}) == 0


# ---------- score_extras ----------
def test_extras_artilheiro_completo():
    facts = {"artilheiro_nome": "Mbappé", "artilheiro_equipe": "França", "artilheiro_gols": 7}
    pred = {"artilheiro_nome": "Mbappé", "artilheiro_equipe": "França", "artilheiro_gols": 7}
    assert S.score_extras(pred, facts) == 8 + 4 + 3 + 5   # 20

def test_extras_curiosidade_numerica():
    facts = {"empates_1f": 9}
    assert S.score_extras({"empates_1f": 9}, facts) == 5
    assert S.score_extras({"empates_1f": 8}, facts) == 0

def test_extras_nada_definido():
    assert S.score_extras({"azarao": "Haiti"}, {}) == 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
