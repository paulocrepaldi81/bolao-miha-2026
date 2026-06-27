"""
Debounce do banner de divergência: uma divergência só "acende" o banner (status=divergencia
chegando ao front) depois de persistir >= 3 checagens — igual ao e-mail. Glitch transitório da
2ª fonte (que se acerta sozinho) não aparece. Rode: cd engine && python3 -m pytest tests -q
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import build_data as BD

DISCREP = [{"match_id": "G6", "teams": "Egito x Irã", "primaria": "1x1  (ESPN)",
            "secundaria": "1x2  (football-data)"}]
CC = {"status": "divergencia", "compared": 66, "agree": 65, "discrepancies": DISCREP,
      "resolvidas": [], "checked_at": "2026-06-27T20:15:00-03:00"}


def _sig(disc):
    return json.dumps(sorted((d["match_id"], d["primaria"], d["secundaria"]) for d in disc),
                      ensure_ascii=False)


def _run(cc, alert_state):
    """Roda load_cross_check com DATA apontando pra um tmp contendo o alert_state dado."""
    with tempfile.TemporaryDirectory() as d:
        json.dump(alert_state, open(os.path.join(d, "alert_state.json"), "w"))
        ccp = os.path.join(d, "cross_check.json")
        json.dump(cc, open(ccp, "w"))
        old = BD.DATA
        BD.DATA = d
        try:
            return BD.load_cross_check(ccp)
        finally:
            BD.DATA = old


def test_divergencia_nova_nao_acende_banner():
    # 1ª aparição: alert_state ainda zerado -> esconde (vira "ok")
    out = _run(CC, {"last_sig": "", "streak": 0})
    assert out["status"] == "ok" and out["discrepancies"] == []


def test_divergencia_so_uma_checagem_ainda_esconde():
    out = _run(CC, {"last_sig": _sig(DISCREP), "streak": 1})   # 1+1=2 < 3
    assert out["status"] == "ok" and out["discrepancies"] == []


def test_divergencia_persistente_acende_banner():
    out = _run(CC, {"last_sig": _sig(DISCREP), "streak": 2})   # 2+1=3 >= 3
    assert out["status"] == "divergencia" and len(out["discrepancies"]) == 1


def test_sig_diferente_reinicia_e_esconde():
    out = _run(CC, {"last_sig": "outra-divergencia-qualquer", "streak": 9})
    assert out["status"] == "ok" and out["discrepancies"] == []


def test_status_ok_passa_direto():
    out = _run({"status": "ok", "compared": 66, "agree": 66, "discrepancies": [], "resolvidas": []},
               {"last_sig": "", "streak": 0})
    assert out["status"] == "ok"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
