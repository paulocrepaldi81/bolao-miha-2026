"""
validate_data.py — o "freio de mão" que impede o robô de publicar data.json quebrado. Antes
desta suite, o próprio script de segurança do pipeline tinha ZERO testes: um bug aqui faria o
robô publicar dado ruim (ou travar publicação boa) sem ninguém perceber até o estrago acontecer.
Testa que cada checagem CRÍTICA realmente bloqueia (sys.exit(1)) e que dado bom passa (exit 0).
Rode: cd engine && python3 -m pytest tests -q
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import validate_data as V
import catalog as CAT

CATALOGO_FAKE = [{"match_id": "A1", "group": "A", "home": "Brasil", "away": "Argélia",
                 "date": "11/jun 16h", "special": False}]


def _baseline():
    """1 aposta, 1 jogo de grupo (encerrado), 11 extras (nenhuma definida ainda) — o mínimo
    estruturalmente válido pra passar em TODAS as checagens críticas."""
    return {
        "meta": {"is_placeholder": False},
        "participants": [{
            "alias": "Fulano", "rank": 1, "score": 10,
            "phase1_points": 10, "exact_scores": 1, "correct_outcomes": 1,
            "max_possible": 50, "points_available": 40,
            "picks": {"groups": {"A1": [2, 1, 3]}},
        }],
        "matches": [{"match_id": "A1", "status": "finished", "home_score": 2, "away_score": 1}],
        "extras_summary": [{"key": f"cat{i}", "label": f"Cat {i}", "points": 5,
                            "real": None, "partial": None, "winners": []}
                           for i in range(len(V.CFG.EXTRA_CELLS))],
        "stats": {"best_exact": {"alias": "Fulano"}, "cursed": {"alias": "Fulano"}},
        "movement": {},
        "audit": None,
    }


def _run(tmp_path, monkeypatch, data, catalogo=CATALOGO_FAKE, bets_json=None, knockout_forms=None):
    """Escreve `data` num data.json temporário, aponta OUT/DATA/get_catalog pra lá, roda main()
    e devolve o código de saída (sys.exit) — nunca deixa main() escrever no data.json REAL."""
    out = tmp_path / "data.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    data_dir = tmp_path / "data"; data_dir.mkdir(exist_ok=True)
    if bets_json is not None:
        (data_dir / "bets_extracted.json").write_text(json.dumps({"bets": bets_json}), encoding="utf-8")
    if knockout_forms is not None:
        (data_dir / "knockout_forms.json").write_text(json.dumps(knockout_forms), encoding="utf-8")
    monkeypatch.setattr(V, "OUT", str(out))
    monkeypatch.setattr(V, "DATA", str(data_dir))
    monkeypatch.setattr(V, "REPORT", str(data_dir / "audit_report.txt"))
    monkeypatch.setattr(CAT, "get_catalog", lambda *a, **k: catalogo)
    try:
        V.main()
    except SystemExit as e:
        return e.code
    return None   # main() sempre chama sys.exit — None só se isso mudar (bug)


def test_dado_bom_passa(tmp_path, monkeypatch):
    assert _run(tmp_path, monkeypatch, _baseline()) == 0


def test_placeholder_ligado_por_engano_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["meta"]["is_placeholder"] = True
    assert _run(tmp_path, monkeypatch, d) == 1


def test_sem_participantes_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["participants"] = []
    assert _run(tmp_path, monkeypatch, d) == 1


def test_rank_inconsistente_com_pontuacao_bloqueia(tmp_path, monkeypatch):
    # 2 apostas com pontos DIFERENTES mas mesmo rank -- viola "empate = mesma posição"
    d = _baseline()
    p2 = dict(d["participants"][0]); p2["alias"] = "Ciclano"; p2["score"] = 999   # deveria ser rank 1
    d["participants"].append(p2)   # ambos com rank=1, mas Ciclano tem mais pontos -> inconsistente
    assert _run(tmp_path, monkeypatch, d) == 1


def test_rank_empate_correto_nao_bloqueia(tmp_path, monkeypatch):
    # 2 apostas com os MESMOS pontos e mesmo rank -- empate válido, não deve bloquear
    d = _baseline()
    p2 = dict(d["participants"][0]); p2["alias"] = "Ciclano"
    d["participants"].append(p2)
    assert _run(tmp_path, monkeypatch, d) == 0


def test_aposta_sem_campo_obrigatorio_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); del d["participants"][0]["max_possible"]
    assert _run(tmp_path, monkeypatch, d) == 1


def test_aposta_sem_picks_groups_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["participants"][0]["picks"] = {"groups": {}}
    assert _run(tmp_path, monkeypatch, d) == 1


def test_jogo_encerrado_sem_placar_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["matches"][0]["home_score"] = None
    assert _run(tmp_path, monkeypatch, d) == 1


def test_numero_de_extras_errado_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["extras_summary"] = d["extras_summary"][:-1]   # tira 1 categoria (10 de 11)
    assert _run(tmp_path, monkeypatch, d) == 1


def test_categoria_com_vencedor_sem_valor_real_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["extras_summary"][0]["winners"] = ["Fulano"]   # real continua None -> inconsistente
    assert _run(tmp_path, monkeypatch, d) == 1


def test_campeao_com_nome_de_selecao_invalido_bloqueia(tmp_path, monkeypatch):
    # pega typo silencioso (manual ou de uma futura automação via ESPN) antes de zerar os
    # 15/10/5 pts de todo mundo -- a categoria de maior peso do bolão.
    d = _baseline(); d["final_result"] = {"champion": "Espanhã", "vice": "Argentina", "third": None}
    assert _run(tmp_path, monkeypatch, d) == 1


def test_campeao_com_nomes_validos_nao_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["final_result"] = {"champion": "Espanha", "vice": "Argentina", "third": "Inglaterra"}
    assert _run(tmp_path, monkeypatch, d) == 0


def test_final_result_vazio_nao_bloqueia_fase_de_grupos(tmp_path, monkeypatch):
    d = _baseline(); d["final_result"] = {"champion": None, "vice": None, "third": None}
    assert _run(tmp_path, monkeypatch, d) == 0


def test_stat_apontando_apelido_inexistente_bloqueia(tmp_path, monkeypatch):
    d = _baseline(); d["stats"]["best_exact"]["alias"] = "Ninguem Com Esse Nome"
    assert _run(tmp_path, monkeypatch, d) == 1


def test_nbets_diferente_de_apostas_extraidas_bloqueia(tmp_path, monkeypatch):
    d = _baseline()   # 1 participante no data.json, mas bets_extracted.json diz que tem 2
    assert _run(tmp_path, monkeypatch, d, bets_json=[{"alias": "Fulano"}, {"alias": "Ciclano"}]) == 1


def test_fase_TER_coberta_pela_rodada_FIN_nao_gera_aviso_falso(tmp_path, monkeypatch):
    # BUG corrigido (15/jul): TER (3º lugar) não tem rodada própria em knockout_forms.json --
    # vem no MESMO Form da FIN (mesmo prazo). Antes do fix, isso gerava um aviso falso de "fase
    # sem Form configurado" mesmo com FIN já cobrindo os dois jogos.
    d = _baseline()
    d["matches"].append({"match_id": "TER", "phase": "TER", "slot": "TER", "status": "scheduled",
                         "home_score": None, "away_score": None,
                         "kickoff_sao_paulo": "2026-07-18T18:00:00-03:00"})
    kf = {"rounds": [{"round": "FIN", "deadline": "2026-07-18 12:00",
                      "csv": "http://exemplo.com/fin.csv"}]}
    assert _run(tmp_path, monkeypatch, d, knockout_forms=kf) == 0
    report = (tmp_path / "data" / "audit_report.txt").read_text(encoding="utf-8")
    assert "fase TER" not in report


def test_fase_realmente_sem_form_ainda_gera_aviso(tmp_path, monkeypatch):
    # confere que o aviso ainda dispara pra uma fase de verdade sem Form (não é regressão muda)
    d = _baseline_with_ko(slot="QF-01")
    assert _run(tmp_path, monkeypatch, d) == 0   # é só AVISO, não bloqueia
    report = (tmp_path / "data" / "audit_report.txt").read_text(encoding="utf-8")
    assert "fase QF tem jogos mas SEM Form configurado" in report


def _baseline_with_ko(slot="QF-01", kickoff="2026-07-09T17:00:00-03:00"):
    d = _baseline()
    d["matches"].append({
        "match_id": slot, "phase": "QF", "slot": slot, "status": "scheduled",
        "home_score": None, "away_score": None, "kickoff_sao_paulo": kickoff,
    })
    return d


def test_prazo_do_mata_mata_depois_do_kickoff_bloqueia(tmp_path, monkeypatch):
    # PRIVACIDADE: se o prazo (18h) vier DEPOIS do kickoff (17h), os cards agregados de "jogo de
    # agora" poderiam mostrar o placar de alguém antes do prazo de atualizar fechar -- bloqueia.
    d = _baseline_with_ko()
    kf = {"rounds": [{"round": "QF", "deadline": "2026-07-09 18:00"}]}
    assert _run(tmp_path, monkeypatch, d, knockout_forms=kf) == 1


def test_prazo_do_mata_mata_antes_do_kickoff_nao_bloqueia(tmp_path, monkeypatch):
    d = _baseline_with_ko()
    kf = {"rounds": [{"round": "QF", "deadline": "2026-07-09 12:00"}]}   # ANTES do kickoff (17h) -> ok
    assert _run(tmp_path, monkeypatch, d, knockout_forms=kf) == 0


def test_avisos_nao_bloqueiam_movimento_vazio_e_extras_indefinidas(tmp_path, monkeypatch):
    # movement vazio e nenhuma extra definida são avisos LEGÍTIMOS no início da Copa -- não bloqueiam
    d = _baseline()   # já vem com movement={} e todas as extras com real=None
    assert _run(tmp_path, monkeypatch, d) == 0
    report = (tmp_path / "data" / "audit_report.txt").read_text(encoding="utf-8")
    assert "CRÍTICO" not in report.split("STATUS:")[1].split("\n")[0]
    assert "Avisos" in report   # os avisos aparecem no relatório, só não bloqueiam
