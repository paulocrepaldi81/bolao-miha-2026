"""
Mata-mata (v2) — leitura dos palpites de placar enviados pelo Google Form.

Cada rodada tem UM Google Form; as respostas viram uma planilha publicada como CSV. Aqui a
gente lê esse CSV e produz, por apelido, o placar atualizado de cada slot do chaveamento.

Regras (decididas com o dono):
  • trava por PRAZO: só vale envio com carimbo de data/hora ANTES do prazo da fase;
  • vale o ÚLTIMO envio (dentro do prazo) — o apostador pode reenviar à vontade;
  • casa o apelido com o roster (sem acento, sem caixa); apelido desconhecido = ignorado;
  • jogo em branco / "Outro placar" / placar inválido = sem override → vale a aposta ORIGINAL.

Nada aqui pontua ou toca a classificação — só monta os palpites. A pontuação fica no scoring.
"""
import csv
import io
import re
import unicodedata
from datetime import datetime


def _norm(s):
    return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().strip().lower()


def _parse_score(cell):
    """'2 × 1' / '2 x 1' / '2x1' -> (2,1).  'Outro...' / '' / lixo -> None."""
    m = re.match(r"^\s*(\d+)\s*[x×]\s*(\d+)\s*$", str(cell or ""), re.I)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _parse_ts(raw):
    """Carimbo do Google Forms (fuso de São Paulo na planilha). Formatos comuns pt-BR."""
    raw = str(raw or "").strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def parse_form_csv(text, round_id, deadline_dt, roster_aliases):
    """
    text          : conteúdo do CSV de respostas do Form.
    round_id      : 'R32' | 'R16' | 'QF' | 'SF' | 'F3' (prefixo do slot; cada 'Jogo N' vira ROUND-0N).
    deadline_dt   : datetime (naive, fuso São Paulo) — envios DEPOIS disso são descartados.
    roster_aliases: lista dos apelidos válidos (roster) — casa o apelido respondido.
    Retorna: {apelido_real: {slot: (h,a)}}  — só os jogos que a pessoa atualizou, do último envio válido.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        return {}
    header = rows[0]
    ts_i = next((i for i, h in enumerate(header) if "carimbo" in _norm(h) or "timestamp" in _norm(h)), 0)
    alias_i = next((i for i, h in enumerate(header) if _norm(h) == "seu apelido"), None)
    game_cols = {}
    for i, h in enumerate(header):
        m = re.match(r"\s*jogo\s*(\d+)", _norm(h))
        if m:
            game_cols[i] = f"{round_id}-{int(m.group(1)):02d}"
    if alias_i is None or not game_cols:
        return {}

    alias_by_norm = {_norm(a): a for a in roster_aliases}
    best = {}   # apelido_real -> (ts, {slot:(h,a)})
    for row in rows[1:]:
        if alias_i >= len(row):
            continue
        alias = alias_by_norm.get(_norm(row[alias_i]))
        if not alias:
            continue
        ts = _parse_ts(row[ts_i] if ts_i < len(row) else "")
        if ts is None or ts > deadline_dt:          # trava por prazo (e descarta sem carimbo)
            continue
        picks = {}
        for ci, slot in game_cols.items():
            if ci < len(row):
                sc = _parse_score(row[ci])
                if sc is not None:
                    picks[slot] = sc
        prev = best.get(alias)
        if prev is None or ts >= prev[0]:            # vale o ÚLTIMO envio dentro do prazo
            best[alias] = (ts, picks)
    return {alias: p for alias, (t, p) in best.items()}


def effective_picks(knockout_orig, form_picks):
    """Placar EFETIVO por slot = override do Form onde houver; senão, o da aposta ORIGINAL.
    knockout_orig: {slot: (h,a)} (da planilha) · form_picks: {slot: (h,a)} (do Form, já filtrado)."""
    eff = {s: tuple(v) for s, v in (knockout_orig or {}).items()}
    for s, v in (form_picks or {}).items():
        eff[s] = tuple(v)
    return eff
