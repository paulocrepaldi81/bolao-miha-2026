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
