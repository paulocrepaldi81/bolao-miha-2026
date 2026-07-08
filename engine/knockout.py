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


def parse_form_csv(text, round_id, deadline, roster_aliases, slot_deadlines=None):
    """
    text          : conteúdo do CSV de respostas do Form.
    round_id      : 'R32' | 'R16' | 'QF' | 'SF' | 'FIN' (prefixo do slot; cada 'Jogo N' vira ROUND-0N).
    deadline      : datetime (naive, fuso SP) — prazo PADRÃO da rodada (envios depois disso, descartados).
    roster_aliases: lista dos apelidos válidos (roster) — casa o apelido respondido.
    slot_deadlines: {slot: datetime} OPCIONAL — prazo POR JOGO; sobrepõe o da rodada só p/ aquele slot
                    (ex.: travar o jogo de hoje mais cedo). Slot sem entrada usa `deadline`.
    Retorna: {apelido_real: {slot: (h,a)}}. Por SLOT, vale o ÚLTIMO envio cujo carimbo respeita o
    prazo DAQUELE jogo; em branco no envio vencedor = sem override (vale a aposta ORIGINAL).
    """
    slot_deadlines = slot_deadlines or {}
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2:
        return {}
    header = rows[0]
    ts_i = next((i for i, h in enumerate(header) if "carimbo" in _norm(h) or "timestamp" in _norm(h)), 0)
    alias_i = next((i for i, h in enumerate(header) if "apelido" in _norm(h)), None)
    game_cols = {}
    for i, h in enumerate(header):
        m = re.match(r"\s*jogo\s*(\d+)", _norm(h))
        if m:
            n = int(m.group(1))
            # FIN é caso especial: Final + 3º lugar vêm no MESMO Form/rodada (mesmo prazo) —
            # "Jogo 1" = a Final (slot "FIN") e "Jogo 2" = o 3º lugar (slot "TER"), não
            # "FIN-01"/"FIN-02" (que não existem em config.KNOCKOUT_CELLS/knockout_bracket.json
            # e faziam os palpites da Final serem ignorados em silêncio).
            if round_id == "FIN":
                game_cols[i] = "FIN" if n == 1 else "TER"
            else:
                game_cols[i] = f"{round_id}-{n:02d}"
    if alias_i is None or not game_cols:
        return {}

    alias_by_norm = {_norm(a): a for a in roster_aliases}
    # junta TODOS os envios válidos por apelido: lista de (ts, {slot: (h,a)|None})
    subs = {}
    for row in rows[1:]:
        if alias_i >= len(row):
            continue
        alias = alias_by_norm.get(_norm(row[alias_i]))
        if not alias:
            continue
        ts = _parse_ts(row[ts_i] if ts_i < len(row) else "")
        if ts is None:                               # sem carimbo legível = descartado (fail-closed)
            continue
        vals = {slot: (_parse_score(row[ci]) if ci < len(row) else None)
                for ci, slot in game_cols.items()}
        subs.setdefault(alias, []).append((ts, vals))

    out = {}
    for alias, lst in subs.items():
        picks = {}
        for slot in game_cols.values():
            dl = slot_deadlines.get(slot, deadline)
            best = None                              # (ts, valor) do ÚLTIMO envio dentro do prazo do slot
            for ts, vals in lst:
                if dl is not None and ts > dl:       # envio depois do prazo DESTE jogo → ignora p/ este slot
                    continue
                if best is None or ts >= best[0]:
                    best = (ts, vals.get(slot))
            if best is not None and best[1] is not None:   # em branco no envio vencedor = sem override
                picks[slot] = best[1]
        if picks:
            out[alias] = picks
    return out


def effective_picks(knockout_orig, form_picks):
    """Placar EFETIVO por slot = override do Form onde houver; senão, o da aposta ORIGINAL.
    knockout_orig: {slot: (h,a)} (da planilha) · form_picks: {slot: (h,a)} (do Form, já filtrado)."""
    eff = {s: tuple(v) for s, v in (knockout_orig or {}).items()}
    for s, v in (form_picks or {}).items():
        eff[s] = tuple(v)
    return eff
