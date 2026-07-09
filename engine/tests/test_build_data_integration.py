"""
build_data.py — o ORQUESTRADOR (685 linhas, zero cobertura antes desta suite). Teste de
integração de ponta a ponta: fixtures mínimas (catálogo de 2 jogos, 2 apostas, roster, results)
num tmp_path, roda main() de verdade (mesmo caminho que o robô usa) e confere que o data.json de
saída tem os campos essenciais certos. Rode: cd engine && python3 -m pytest tests -q

BLINDAGEM (sugerida pelo Agente 5 na revisão do painel): build_data.py lê/escreve em `DATA`
fixo (sem injeção de dependência) — um monkeypatch que falhasse silenciosamente escreveria por
cima dos dados REAIS da Copa ao vivo. Por isso todo teste aqui assert que o path usado nunca é
o repo de produção ANTES de chamar main().
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_data as BD
import catalog as CAT

CATALOGO_FAKE = [
    {"match_id": "A1", "group": "A", "home": "Brasil", "away": "Argélia",
     "date": "11/jun 16h", "special": False},
    {"match_id": "A2", "group": "A", "home": "Coreia do Sul", "away": "Rep Tcheca",
     "date": "12/jun 16h", "special": True},   # especial: aberto, vale pra remaining_group_points
]

BETS_FAKE = [
    {"alias": "Fulano", "file": "fulano.xlsx", "group_preds": {"A1": [2, 1]},
     "final": {}, "extras": {}, "issues": [], "knockout_orig": {}},
    {"alias": "Ciclano", "file": "ciclano.xlsx", "group_preds": {"A1": [1, 1]},
     "final": {}, "extras": {}, "issues": ["apelido com espaço extra"], "knockout_orig": {}},
]


def _setup(tmp_path, monkeypatch, catalogo=CATALOGO_FAKE, bets=BETS_FAKE):
    real_data_dir = os.path.abspath(os.path.join(BD.HERE, "data"))
    data_dir = tmp_path / "data"; data_dir.mkdir()
    # BLINDAGEM: nunca deixar o teste apontar sem querer pro diretório de dados de produção.
    assert os.path.abspath(str(data_dir)) != real_data_dir
    (data_dir / "results.csv").write_text(
        "match_id,status,home_score,away_score,verified,lock\nA1,finished,2,1,sim,\n", encoding="utf-8")
    (data_dir / "roster.csv").write_text(
        "alias,paid,order\nFulano,sim,1\nCiclano,sim,2\n", encoding="utf-8")
    (data_dir / "bets_extracted.json").write_text(json.dumps({"bets": bets}), encoding="utf-8")
    out = tmp_path / "landing-page" / "data.json"
    monkeypatch.setattr(BD, "DATA", str(data_dir))
    monkeypatch.setattr(CAT, "get_catalog", lambda *a, **k: catalogo)
    monkeypatch.setattr(sys, "argv", ["build_data.py", "--from-json", "--out", str(out)])
    return data_dir, out


def test_ponta_a_ponta_gera_data_json_com_campos_essenciais(tmp_path, monkeypatch):
    data_dir, out = _setup(tmp_path, monkeypatch)
    BD.main()
    assert out.exists()
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["meta"]["is_placeholder"] is False
    assert len(d["participants"]) == 2
    assert len(d["extras_summary"]) == len(BD.C.EXTRA_CELLS)
    grp_matches = [m for m in d["matches"] if not m.get("phase")]
    assert len(grp_matches) == len(CATALOGO_FAKE)


def test_placar_exato_pontua_e_define_o_lider(tmp_path, monkeypatch):
    data_dir, out = _setup(tmp_path, monkeypatch)
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    by_alias = {p["alias"]: p for p in d["participants"]}
    # Fulano cravou 2×1 (exato: 3 normal + bônus 3 gols = 6); Ciclano previu empate, saiu 2×1 (0 pts)
    assert by_alias["Fulano"]["score"] == 6
    assert by_alias["Ciclano"]["score"] == 0
    assert by_alias["Fulano"]["rank"] == 1 and by_alias["Ciclano"]["rank"] == 2
    assert by_alias["Fulano"]["exact_scores"] == 1


def test_jogo_de_grupo_aberto_conta_no_maximo_possivel(tmp_path, monkeypatch):
    # A2 é ESPECIAL e não tem resultado (scheduled) -> remaining_group_points soma 5+6=11 pra
    # TODOS igualmente (é um teto global, não depende do palpite de cada um).
    data_dir, out = _setup(tmp_path, monkeypatch)
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    for p in d["participants"]:
        assert p["points_available"] >= 11   # A2 aberto (11) + extras ainda indefinidas + final aberta


def test_planilha_com_avisos_nao_derruba_o_build(tmp_path, monkeypatch):
    # Ciclano tem "issues" (avisos de leitura) -- não deve impedir o build nem sumir da saída.
    data_dir, out = _setup(tmp_path, monkeypatch)
    BD.main()
    report = (data_dir / "validation_report.txt").read_text(encoding="utf-8")
    assert "Ciclano" in report and "apelido com espaço extra" in report
    d = json.loads(out.read_text(encoding="utf-8"))
    assert any(p["alias"] == "Ciclano" for p in d["participants"])


def test_sem_apostas_nao_quebra(tmp_path, monkeypatch):
    # bets_extracted.json vazio -- caminho degenerado (ainda ninguém enviou), não pode lançar.
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[])
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["participants"] == []


def test_mata_mata_oculto_antes_do_prazo(tmp_path, monkeypatch):
    # PRIVACIDADE (achado real, 09/jul): antes do prazo, o placar do mata-mata (used/orig) tem
    # que ficar oculto -- senão dá pra espiar o palpite do rival e mudar o seu antes do Form fechar.
    from datetime import datetime, timedelta
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[
        {"alias": "Fulano", "file": "f.xlsx", "group_preds": {},
         "final": {}, "extras": {}, "issues": [], "knockout_orig": {"R32-01": [2, 1]}},
    ])
    futuro = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    (data_dir / "knockout_forms.json").write_text(json.dumps(
        {"rounds": [{"round": "R32", "deadline": futuro, "csv": ""}]}), encoding="utf-8")
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    k = next(p for p in d["participants"] if p["alias"] == "Fulano")["picks"]["knockout"]["R32-01"]
    assert k["used"] is None and k["orig"] is None
    assert k["hidden_reason"] == "pending"


def test_mata_mata_revela_depois_do_prazo(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[
        {"alias": "Fulano", "file": "f.xlsx", "group_preds": {},
         "final": {}, "extras": {}, "issues": [], "knockout_orig": {"R32-01": [2, 1]}},
    ])
    passado = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
    (data_dir / "knockout_forms.json").write_text(json.dumps(
        {"rounds": [{"round": "R32", "deadline": passado, "csv": ""}]}), encoding="utf-8")
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    k = next(p for p in d["participants"] if p["alias"] == "Fulano")["picks"]["knockout"]["R32-01"]
    assert k["used"] == [2, 1] and k["orig"] == [2, 1]
    assert k["hidden_reason"] is None


def test_mata_mata_sem_prazo_cadastrado_fica_oculto_por_padrao(tmp_path, monkeypatch):
    # fail-closed: rodada ainda sem Form/prazo cadastrado (ex.: Semis antes do organizador criar
    # o Form) -> continua oculto, nunca revela "por acidente" na ausência de configuração.
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[
        {"alias": "Fulano", "file": "f.xlsx", "group_preds": {},
         "final": {}, "extras": {}, "issues": [], "knockout_orig": {"R32-01": [2, 1]}},
    ])
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    k = next(p for p in d["participants"] if p["alias"] == "Fulano")["picks"]["knockout"]["R32-01"]
    assert k["used"] is None
    assert k["hidden_reason"] == "unconfigured"


def test_mata_mata_jogo_ja_encerrado_revela_mesmo_sem_prazo_configurado(tmp_path, monkeypatch):
    # fail-safe complementar: se o organizador esqueceu de cadastrar o prazo mas o jogo JÁ TEM
    # resultado real, esconder não protege mais nada -- revela de qualquer forma.
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[
        {"alias": "Fulano", "file": "f.xlsx", "group_preds": {},
         "final": {}, "extras": {}, "issues": [], "knockout_orig": {"R32-01": [2, 1]}},
    ])
    (data_dir / "knockout_results.csv").write_text(
        "slot,home_score,away_score,status,special,lock\nR32-01,2,1,finished,,\n", encoding="utf-8")
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    k = next(p for p in d["participants"] if p["alias"] == "Fulano")["picks"]["knockout"]["R32-01"]
    assert k["used"] == [2, 1]
    assert k["hidden_reason"] is None


def test_mata_mata_changed_sempre_visivel_mesmo_oculto(tmp_path, monkeypatch):
    # o selo "mudou/manteve" NUNCA fica oculto (só o placar) -- é o único sinal permitido antes
    # do prazo, por pedido explícito do dono do bolão.
    data_dir, out = _setup(tmp_path, monkeypatch, bets=[
        {"alias": "Fulano", "file": "f.xlsx", "group_preds": {},
         "final": {}, "extras": {}, "issues": [], "knockout_orig": {"R32-01": [2, 1]}},
    ])
    BD.main()
    d = json.loads(out.read_text(encoding="utf-8"))
    k = next(p for p in d["participants"] if p["alias"] == "Fulano")["picks"]["knockout"]["R32-01"]
    assert "changed" in k and k["changed"] is False   # não mudou (sem Form configurado) mas o campo existe


def test_grava_history_e_matches_reference_no_diretorio_certo(tmp_path, monkeypatch):
    data_dir, out = _setup(tmp_path, monkeypatch)
    BD.main()
    assert (data_dir / "matches_reference.csv").exists()
    assert (data_dir / "history.json").exists()
    hist = json.loads((data_dir / "history.json").read_text(encoding="utf-8"))
    assert len(hist) == 1 and set(hist[0]["ranks"].keys()) == {"Fulano", "Ciclano"}
