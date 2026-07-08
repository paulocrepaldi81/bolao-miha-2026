"""
gen_rodada.py — os 3 estados do bloco "próximo(s) jogo(s)": HOJE / VÃO (sem jogo hoje, próximo
é dia futuro) / FIM DE COPA. Bug real corrigido 08/07/2026: no vão entre Oitavas (terminaram
06-07/07) e Quartas (começam 09/07) o pôster disse "JOGOS DE HOJE: França × Marrocos" com o
jogo ainda a 1-2 dias de distância. Rode: cd a-rodada && python3 -m pytest tests -q
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gen_rodada as GR


def test_vao_sem_jogo_nao_diz_hoje():
    # o cenário exato do bug: próximo jogo é 09/07, "hoje" é 08/07
    html = GR.build_html([], [], None, "2026-07-09", today_day="2026-07-08")
    assert "PRÓXIMO JOGO" in html
    assert "hoje ninguém joga" in html
    assert "JOGOS DE HOJE" not in html
    # a data real do próximo jogo continua aparecendo (não é pra esconder, só não chamar de "hoje")
    assert "julho" in html.lower() or "Julho" in html


def test_dia_normal_com_jogo_hoje_mantem_hoje():
    html = GR.build_html([], [], None, "2026-07-09", today_day="2026-07-09")
    assert "JOGOS DE HOJE" in html
    assert "Hoje ·" in html
    assert "PRÓXIMO JOGO" not in html


def test_fim_de_copa_sem_mais_jogo():
    html = GR.build_html([], [], "2026-07-19", None, today_day="2026-07-20")
    assert "ACABOU A COPA" in html
    assert "JOGOS DE HOJE" not in html and "PRÓXIMO JOGO" not in html


def test_boundary_corte_as_6h_sp_nao_confunde_com_vao():
    # jogo agendado pra hoje às 10h SP (bem depois do corte de 6h) -> agenda_day do jogo bate
    # com o dia de calendário atual, mesmo gerando o pôster de madrugada (antes das 6h SP)
    assert GR.agenda_day("2026-07-09T13:00:00+00:00") == "2026-07-09"   # 10h SP


def test_today_agenda_day_reaproveita_agenda_day():
    # today_agenda_day() não deve duplicar a regra de corte -- só delega pra agenda_day() com
    # o horário atual. Sanity check: retorna uma string de data válida no formato certo.
    import datetime as dt
    hoje = GR.today_agenda_day()
    assert dt.date.fromisoformat(hoje)   # não lança -> formato YYYY-MM-DD válido
