"""
"A RODADA" — gera o PNG diário do Bolão Miha 2026 (TAREFA SEPARADA da landing page).

Pega da própria Copa (ESPN, API pública) a ÚLTIMA rodada encerrada (resultados +
curiosidades) e os PRÓXIMOS jogos (com horário de São Paulo), monta um pôster estilo
futebol/cartoon com a caricatura do Ricardo e exporta a-rodada/hoje.png.

Usa o estado real do torneio (jogos post/pre) pra achar QUAL é o próximo jogo — mas o
relógio real (UTC, comparado via agenda_day) decide COMO chamar isso: só diz "HOJE" se o
próximo jogo for de fato hoje. Bug real corrigido em 08/07: entre Oitavas (terminaram
06-07/07) e Quartas (começam 09/07) existe um vão de dias sem jogo nenhum — nesse vão o
pôster dizia "JOGOS DE HOJE: França × Marrocos" quando esse jogo só ia acontecer 1-2 dias
depois. Agora tem 3 estados: HOJE (jogo é hoje mesmo) / VÃO (próximo jogo é dia futuro,
mostra a data e deixa claro que hoje não tem jogo) / FIM DE COPA (sem mais jogo nenhum).

Caricatura: usa a-rodada/ricardo.png se existir; senão, um mascote vetorial (SVG).

Render: HTML → PNG via Playwright (chromium headless). Roda no workflow a-rodada.yml.
"""
import base64
import datetime as dt
import hashlib
import io
import json
import os
import urllib.request
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hoje.png")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={a}-{b}"
WINDOWS = [("20260611", "20260625"), ("20260626", "20260710"), ("20260711", "20260719")]

EN_PT = {
    "mexico": "México", "south africa": "África do Sul", "south korea": "Coreia do Sul",
    "korea republic": "Coreia do Sul", "czechia": "Rep Tcheca", "canada": "Canadá",
    "bosnia and herzegovina": "Bósnia", "bosnia-herzegovina": "Bósnia", "qatar": "Catar",
    "switzerland": "Suíça", "brazil": "Brasil", "morocco": "Marrocos", "haiti": "Haiti",
    "scotland": "Escócia", "united states": "EUA", "paraguay": "Paraguai", "australia": "Austrália",
    "türkiye": "Turquia", "turkey": "Turquia", "germany": "Alemanha", "curaçao": "Curaçao",
    "curacao": "Curaçao", "ivory coast": "Costa do Marfim", "ecuador": "Equador",
    "netherlands": "Holanda", "japan": "Japão", "sweden": "Suécia", "tunisia": "Tunísia",
    "belgium": "Bélgica", "egypt": "Egito", "iran": "Irã", "new zealand": "Nova Zelândia",
    "spain": "Espanha", "cape verde": "Cabo Verde", "saudi arabia": "Arábia Saudita",
    "uruguay": "Uruguai", "france": "França", "senegal": "Senegal", "iraq": "Iraque",
    "norway": "Noruega", "argentina": "Argentina", "algeria": "Argélia", "austria": "Áustria",
    "jordan": "Jordânia", "portugal": "Portugal", "dr congo": "RD Congo", "congo dr": "RD Congo", "uzbekistan": "Uzbequistão",
    "colombia": "Colômbia", "england": "Inglaterra", "ghana": "Gana", "croatia": "Croácia", "panama": "Panamá",
}
FLAG = {
    "México": "🇲🇽", "África do Sul": "🇿🇦", "Canadá": "🇨🇦", "Bósnia": "🇧🇦", "Brasil": "🇧🇷",
    "Marrocos": "🇲🇦", "Haiti": "🇭🇹", "Escócia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "EUA": "🇺🇸", "Paraguai": "🇵🇾", "Austrália": "🇦🇺",
    "Turquia": "🇹🇷", "Alemanha": "🇩🇪", "Curaçao": "🇨🇼", "Costa do Marfim": "🇨🇮", "Equador": "🇪🇨",
    "Holanda": "🇳🇱", "Japão": "🇯🇵", "Suécia": "🇸🇪", "Tunísia": "🇹🇳", "Bélgica": "🇧🇪", "Egito": "🇪🇬",
    "Irã": "🇮🇷", "Nova Zelândia": "🇳🇿", "Espanha": "🇪🇸", "Cabo Verde": "🇨🇻", "Arábia Saudita": "🇸🇦",
    "Uruguai": "🇺🇾", "França": "🇫🇷", "Senegal": "🇸🇳", "Iraque": "🇮🇶", "Noruega": "🇳🇴", "Argentina": "🇦🇷",
    "Argélia": "🇩🇿", "Áustria": "🇦🇹", "Jordânia": "🇯🇴", "Portugal": "🇵🇹", "RD Congo": "🇨🇩",
    "Uzbequistão": "🇺🇿", "Colômbia": "🇨🇴", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Gana": "🇬🇭", "Croácia": "🇭🇷",
    "Panamá": "🇵🇦", "Catar": "🇶🇦", "Suíça": "🇨🇭", "Coreia do Sul": "🇰🇷", "Rep Tcheca": "🇨🇿",
}
# Escócia/Inglaterra: emoji de SUBDIVISÃO o Noto do CI não renderiza (vira tofu/bandeira preta).
# Pra essas, bandeira SVG inline (cruz de São Jorge / saltire) — idêntica à da landing, renderiza
# em qualquer sistema. As demais seleções usam o emoji normal.
SUBDIV_SVG = {
    "Inglaterra": '<svg viewBox="0 0 30 20" width="19" height="13" style="vertical-align:-2px;border-radius:2px"><rect width="30" height="20" fill="#fff"/><rect x="12" width="6" height="20" fill="#ce1124"/><rect y="7" width="30" height="6" fill="#ce1124"/></svg>',
    "Escócia":    '<svg viewBox="0 0 30 20" width="19" height="13" style="vertical-align:-2px;border-radius:2px"><rect width="30" height="20" fill="#0065bf"/><path d="M0 0L30 20M30 0L0 20" stroke="#fff" stroke-width="4.5"/></svg>',
}


def flag(team):
    return SUBDIV_SVG.get(team) or FLAG.get(team, "")


TEAM_GROUP = {
    "Coreia do Sul": "A", "México": "A", "Rep Tcheca": "A", "África do Sul": "A",
    "Bósnia": "B", "Canadá": "B", "Catar": "B", "Suíça": "B", "Brasil": "C",
    "Escócia": "C", "Haiti": "C", "Marrocos": "C", "Austrália": "D", "EUA": "D",
    "Paraguai": "D", "Turquia": "D", "Alemanha": "E", "Costa do Marfim": "E",
    "Curaçao": "E", "Equador": "E", "Holanda": "F", "Japão": "F", "Suécia": "F",
    "Tunísia": "F", "Bélgica": "G", "Egito": "G", "Irã": "G", "Nova Zelândia": "G",
    "Arábia Saudita": "H", "Cabo Verde": "H", "Espanha": "H", "Uruguai": "H",
    "França": "I", "Iraque": "I", "Noruega": "I", "Senegal": "I", "Argentina": "J",
    "Argélia": "J", "Jordânia": "J", "Áustria": "J", "Colômbia": "K", "Portugal": "K",
    "RD Congo": "K", "Uzbequistão": "K", "Croácia": "L", "Gana": "L", "Inglaterra": "L",
    "Panamá": "L",
}
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def fetch_events():
    evs = []
    for a, b in WINDOWS:
        req = urllib.request.Request(ESPN.format(a=a, b=b), headers={"User-Agent": "rodada-bot"})
        with urllib.request.urlopen(req, timeout=30) as r:
            evs += json.load(r).get("events", [])
    out = []
    for e in evs:
        comp = (e.get("competitions") or [{}])[0]
        cs = comp.get("competitors", [])
        if len(cs) != 2:
            continue
        try:
            home = next(c for c in cs if c.get("homeAway") == "home")
            away = next(c for c in cs if c.get("homeAway") == "away")
        except StopIteration:
            continue
        pt = lambda c: EN_PT.get((c.get("team", {}).get("displayName") or "").strip().lower())
        h, a = pt(home), pt(away)
        if not h or not a:
            # Descarte NÃO-silencioso: se a ESPN renomear um time (acento/abreviação), o log do
            # CI mostra o nome cru pra gente mapear — foi assim que o "Congo DR" passou batido.
            print(f"  (sem tradução p/ pôster, jogo ignorado: "
                  f"{home.get('team', {}).get('displayName')!r} x {away.get('team', {}).get('displayName')!r})")
            continue
        t = e.get("status", {}).get("type", {})
        out.append({
            "date": e.get("date", ""), "state": t.get("state"),
            "home": h, "away": a,
            "hs": _int(home.get("score")), "as": _int(away.get("score")),
        })
    out.sort(key=lambda x: x["date"])
    return out


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def sp_time(iso):
    """ISO UTC → 'HH:MM' em São Paulo (UTC-3)."""
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) - dt.timedelta(hours=3)
        return d.strftime("%Hh%M").replace("h00", "h")
    except Exception:
        return "—"


def sp_date_label(iso):
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) - dt.timedelta(hours=3)
        return f"{DIAS[d.weekday()].capitalize()}, {d.day} de {MESES[d.month - 1]}"
    except Exception:
        return ""


def sp_daykey(iso):
    """Dia em São Paulo (UTC-3) no formato AAAA-MM-DD — agrupa jogos da noite que viram
    o dia seguinte em UTC (ex.: 01h UTC = 22h SP do dia anterior)."""
    try:
        return (dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) - dt.timedelta(hours=3)).strftime("%Y-%m-%d")
    except Exception:
        return iso[:10]


def agenda_day(iso):
    """'Dia da agenda' em SP, mas com o corte às 06h (não à meia-noite): jogos de madrugada
    (00h/01h SP) contam para o dia ANTERIOR — é o que rolou 'enquanto você dormia'. Existem
    jogos às 00h e 01h SP na Copa; sem isso eles cairiam no dia errado."""
    try:
        sp = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) - dt.timedelta(hours=3)
        return (sp - dt.timedelta(hours=6)).strftime("%Y-%m-%d")
    except Exception:
        return iso[:10]


def today_agenda_day():
    """'Hoje' pela MESMA regra de corte de agenda_day (6h SP) — reaproveita a função em vez de
    duplicar a lógica, pra nunca divergir se o corte mudar. SEMPRE explícito em UTC
    (datetime.now(timezone.utc)): datetime.now() sem argumento pega o fuso do RELÓGIO LOCAL de
    quem roda o script — no GitHub Actions (UTC) "funciona por acidente", mas rodando local em
    horário de Brasília deslocaria o corte em 3h por engano."""
    return agenda_day(dt.datetime.now(dt.timezone.utc).isoformat())


def label_day(daykey):
    try:
        d = dt.date.fromisoformat(daykey)
        return f"{DIAS[d.weekday()].capitalize()}, {d.day} de {MESES[d.month - 1]}"
    except Exception:
        return ""


def pick_rounds(events):
    """Retorna (resultados, jogos_da_rodada, dia_resultados, dia_rodada).
    - jogos_da_rodada = TODOS os jogos do próximo dia de SP com jogo (agendado, AO VIVO e
      já encerrado nesse dia) — assim nada cai no vão (era o bug do jogo ao vivo sumindo).
    - resultados = jogos encerrados do último dia de SP ANTERIOR ao dia da rodada."""
    finished = [e for e in events if e["state"] == "post" and e["hs"] is not None and e["as"] is not None]
    upcoming = [e for e in events if e["state"] in ("pre", "in")]
    up_day = agenda_day(min(upcoming, key=lambda e: e["date"])["date"]) if upcoming else None
    next_round = sorted([e for e in events if agenda_day(e["date"]) == up_day],
                        key=lambda e: e["date"]) if up_day else []
    fin_days = sorted({agenda_day(e["date"]) for e in finished})
    if up_day:
        fin_days = [d for d in fin_days if d < up_day]
    res_day = fin_days[-1] if fin_days else None
    last_round = sorted([e for e in finished if agenda_day(e["date"]) == res_day],
                        key=lambda e: e["date"]) if res_day else []
    return last_round, next_round, res_day, up_day


def curiosidades(jogos):
    if not jogos:
        return ["A bola ainda vai rolar — primeira rodada chegando!"]
    tot = sum(j["hs"] + j["as"] for j in jogos)
    cur = [f"<b>{tot} gols</b> em {len(jogos)} jogo{'s' if len(jogos) != 1 else ''} na rodada."]
    goleada = max(jogos, key=lambda j: abs(j["hs"] - j["as"]))
    if abs(goleada["hs"] - goleada["as"]) >= 3:
        vencedor = goleada["home"] if goleada["hs"] > goleada["as"] else goleada["away"]
        cur.append(f"<b>{vencedor}</b> atropelou: {goleada['home']} {goleada['hs']}×{goleada['as']} {goleada['away']}.")
    empates = [j for j in jogos if j["hs"] == j["as"]]
    if empates:
        e = empates[0]
        cur.append(f"<b>Empate da rodada:</b> {e['home']} {e['hs']}×{e['as']} {e['away']}.")
    return cur[:3]


# ───────────────── CURIOSIDADES turbinadas do MATA-MATA (3 blocos) ─────────────────
# Lê arquivos do engine (../engine/data) e a curadoria local. TUDO fail-closed: se faltar
# qualquer dado, o bloco some; se TODOS falharem, cai nas curiosidades de grupo (acima).
ENG_DATA = os.path.join(HERE, "..", "engine", "data")
_PHASE_NEXT = {"R32": "oitavas", "R16": "quartas", "QF": "semifinais", "SF": "final"}


def _load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _bracket_pairs():
    """{frozenset(home,away): slot_entry} dos slots com os dois times reais já definidos."""
    bj = _load_json(os.path.join(ENG_DATA, "knockout_bracket.json"), {})
    out = {}
    for entries in (bj.values() if isinstance(bj, dict) else []):
        if isinstance(entries, list):
            for e in entries:
                if e.get("home") and e.get("away"):
                    out[frozenset((e["home"], e["away"]))] = e
    return out


def is_knockout(next_round, pairs):
    return any(frozenset((j["home"], j["away"])) in pairs for j in next_round)


def _short_name(nome):
    parts = (nome or "").split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) >= 2 else (nome or "?")


def _artil_chip(medal, nome, team, gols):
    # chip vertical compacto: medalha em cima, bandeira + nº de gols (herói) no meio, nome embaixo.
    return (f'<div style="flex:1 1 0;min-width:0;background:rgba(255,255,255,.06);border-radius:11px;'
            f'padding:9px 8px 8px;text-align:center;border-top:2px solid rgba(244,196,48,.35)">'
            f'<div style="font-size:14px;line-height:1;margin-bottom:4px">{medal}</div>'
            f'<div style="display:flex;align-items:baseline;justify-content:center;gap:5px;margin-bottom:3px">'
            f'<span style="font-size:16px">{flag(team) if team else ""}</span>'
            f'<span style="font-family:Anton,sans-serif;font-size:24px;color:#f4c430;line-height:1">{gols}</span></div>'
            f'<div style="font-size:11px;font-weight:600;color:#e9f5ef;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis">{_short_name(nome)}</div></div>')


def _pf_linha(j, adv, nxt):
    # AGENDA da próxima fase: "jogo do dia → adversário", seta dourada; ellipsis blinda nomes longos.
    return (f'<div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.05);'
            f'border-radius:9px;padding:6px 11px">'
            f'<span style="flex:1;min-width:0;font-size:12.5px;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis">{flag(j["home"])} {j["home"]} <span style="color:#7fae98">×</span> '
            f'{j["away"]} {flag(j["away"])}</span>'
            f'<span style="color:#f4c430;font-size:14px;flex:0 0 auto">→</span>'
            f'<span style="flex:0 0 auto;font-size:11.5px;color:#bfe3d2;max-width:215px;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis">{adv} <span style="color:#f4c430;font-weight:600">'
            f'{nxt}</span></span></div>')


def _mini_cur(icon, titulo, body):
    # card compacto p/ curiosidades lado a lado (mata-mata).
    return (f'<div style="flex:1 1 0;min-width:0;background:rgba(244,196,48,.09);border-left:3px solid #f4c430;'
            f'border-radius:8px;padding:8px 11px"><div style="font-family:Anton,sans-serif;font-size:10.5px;'
            f'color:#f4c430;letter-spacing:.4px;margin-bottom:3px">{icon} {titulo}</div>'
            f'<div style="font-size:12px;color:#e9f5ef;line-height:1.4">{body}</div></div>')


def _subsec(txt):
    return (f'<div style="font-family:Anton,sans-serif;font-size:12px;color:#f4c430;letter-spacing:.5px;'
            f'margin:13px 0 6px;display:flex;align-items:center;gap:7px;text-transform:uppercase">{txt}'
            f'<span style="flex:1;height:1px;background:rgba(244,196,48,.20)"></span></div>')


def _card_curiosidade(txt):
    return (f'<div style="background:rgba(244,196,48,.10);border-left:3px solid #f4c430;border-radius:8px;'
            f'padding:9px 13px;margin-top:12px"><div style="font-family:Anton,sans-serif;font-size:12px;'
            f'color:#f4c430;letter-spacing:.5px;margin-bottom:3px">💡 VOCÊ SABIA?</div>'
            f'<div style="font-size:13px;color:#e9f5ef;line-height:1.45">{txt}</div></div>')


def _artilharia_top(n=4):
    fl = _load_json(os.path.join(ENG_DATA, "facts_live.json"), {})
    return ((fl.get("partials") or {}).get("scorers_top") or [])[:n]


def _proxima_fase(next_round, pairs, last_round=None):
    """Para CADA jogo do dia devolve (jogo, adversário na próxima fase, rótulo). RESOLUÇÃO PARCIAL:
    se o jogo-IRMÃO já foi decidido, mostra o time que passou (bandeira); senão 'venc. C × D'.
    Devolve lista (uma linha por jogo) ou None. Reaproveita a topologia de slot-irmão + winner."""
    bracket = _load_json(os.path.join(ENG_DATA, "knockout_bracket.json"), {})
    fixtures = _load_json(os.path.join(ENG_DATA, "knockout_fixtures.json"), {})
    # Vencedores AO VIVO dos jogos JÁ ENCERRADOS (o pôster tem o resultado real via ESPN): cobre o
    # caso das fixtures defasadas (ex.: México já ganhou mas o resolver ainda não rodou). Empate =
    # pênaltis → não dá pra saber o vencedor daqui, cai no fixtures.
    live_win = {}
    for r in (last_round or []):
        hs, as_ = r.get("hs"), r.get("as")
        if hs is not None and as_ is not None and hs != as_:
            live_win[frozenset((r["home"], r["away"]))] = r["home"] if hs > as_ else r["away"]
    out = []
    for j in next_round:
        e = pairs.get(frozenset((j["home"], j["away"])))
        if not e or "-" not in str(e.get("slot", "")):
            continue
        rnd, num = e["slot"].split("-")[0], int(e["slot"].split("-")[1])
        k = (num + 1) // 2                       # par que alimenta o slot da próxima fase
        sib = f"{rnd}-{(2 * k if num == 2 * k - 1 else 2 * k - 1):02d}"
        s = next((x for x in bracket.get(rnd, []) if x.get("slot") == sib and x.get("home")), None)
        if not s:
            continue
        nxt = _PHASE_NEXT.get(rnd, "próx. fase")
        # irmão já decidido? mostra o time que passou — resultado AO VIVO na frente, fixtures atrás
        win = live_win.get(frozenset((s["home"], s["away"]))) or fixtures.get(sib, {}).get("winner")
        adv = (f"{flag(win)} {win}" if win
               else f"venc. {flag(s['home'])} {s['home']} × {s['away']} {flag(s['away'])}")
        out.append((j, adv, nxt))
    return out or None


def _curiosidades_dia(next_round, up_day, n=2, exclude=()):
    """Até N curiosidades de seleções DISTINTAS entre os jogos do dia (escolha estável por dia)."""
    cur = _load_json(os.path.join(HERE, "curiosidades_selecoes.json"), {})
    times = sorted({t for j in next_round for t in (j["home"], j["away"])
                    if t in cur and not t.startswith("_") and t not in exclude})
    if not times:
        return []
    seed = int(hashlib.md5(str(up_day).encode()).hexdigest(), 16)
    off = seed % len(times)
    rot = times[off:] + times[:off]                       # rotação estável por dia
    out = []
    for team in rot[:n]:
        fatos = cur[team]
        out.append(f"{flag(team)} <b>{team}:</b> {fatos[seed % len(fatos)]}")
    return out


_STAGE_RANK = {"final": 5, "semi-finals": 4, "third-place match": 4, "quarter-finals": 3,
               "round of 16": 2}
_STAGE_PT = {"final": "final", "semi-finals": "semi", "third-place match": "3º lugar",
             "quarter-finals": "quartas", "round of 16": "oitavas"}


def _card_h2h(titulo, body):
    return (f'<div style="background:rgba(244,196,48,.10);border-left:3px solid #f4c430;border-radius:8px;'
            f'padding:9px 13px;margin-top:12px"><div style="font-family:Anton,sans-serif;font-size:12px;'
            f'color:#f4c430;letter-spacing:.5px;margin-bottom:3px">{titulo}</div>'
            f'<div style="font-size:13px;color:#e9f5ef;line-height:1.45">{body}</div></div>')


def _h2h_dia_body(next_round):
    """(título, linha) do confronto-direto de Copa MAIS MARCANTE entre os jogos de hoje
    (final>semi>recente), ou None se nenhum par tiver histórico. O ícone ⚔️ é posto pelo card."""
    h2h = _load_json(os.path.join(HERE, "h2h_copa.json"), {})
    best = None
    for j in next_round:
        for e in h2h.get("|".join(sorted([j["home"], j["away"]])), []) or []:
            cand = (_STAGE_RANK.get(e.get("stage"), 1), e.get("ano", 0), e, j)
            if best is None or cand[:2] > best[:2]:
                best = cand
    if not best:
        return None
    rank, ano, e, j = best
    hs, as_ = (e["hs"], e["as"]) if e["home"] == j["home"] else (e["as"], e["hs"])
    stage = _STAGE_PT.get(e.get("stage"), "")
    quando = f"{stage} de {ano}" if (rank >= 4 and stage) else str(ano)
    titulo = "CLÁSSICO DE COPA" if rank >= 4 else "JÁ SE ENFRENTARAM"
    linha = f"{flag(j['home'])} {j['home']} <b>{hs}×{as_}</b> {j['away']} {flag(j['away'])} · {quando}"
    return (titulo, linha)


def curiosidades_html(last_round, next_round, up_day):
    """HTML da seção CURIOSIDADES. No mata-mata: 3 blocos (artilharia/próxima fase/você sabia).
    Em grupos OU se tudo falhar: os bullets clássicos (gols/goleada/empate)."""
    pairs = _bracket_pairs()
    if next_round and is_knockout(next_round, pairs):
        blocks = []
        # ARTILHARIA — faixa de chips compactos (top-4); medalha por RANK (empate divide: 6/6 = 🥇🥇)
        try:
            top = _artilharia_top(4)
            if top:
                def _medal(i):
                    g = top[i].get("gols", 0) or 0
                    r = 1 + sum(1 for t in top if (t.get("gols", 0) or 0) > g)
                    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(r, "4º")
                chips = "".join(_artil_chip(_medal(i), top[i].get("nome"), top[i].get("equipe"),
                                            top[i].get("gols", 0)) for i in range(len(top)))
                blocks.append(_subsec("⚽ Artilharia") +
                              f'<div style="display:flex;gap:7px;align-items:stretch">{chips}</div>')
        except Exception:
            pass
        # QUEM PEGA QUEM — grade cobrindo TODOS os jogos do dia (não só o 1º)
        try:
            pf = _proxima_fase(next_round, pairs, last_round)
            if pf:
                linhas = "".join(_pf_linha(j, adv, nxt) for j, adv, nxt in pf)
                blocks.append(_subsec("🔜 Quem pega quem") +
                              f'<div style="display:grid;gap:5px">{linhas}</div>')
        except Exception:
            pass
        # DESTAQUES — 2 curiosidades: h2h de Copa (se houver) + você-sabia, ou 2 seleções distintas
        try:
            cards = []
            hb = _h2h_dia_body(next_round)
            if hb:
                cards.append(_mini_cur("⚔️", hb[0], hb[1]))
                cards += [_mini_cur("💡", "VOCÊ SABIA?", c) for c in _curiosidades_dia(next_round, up_day, 1)]
            else:
                cards += [_mini_cur("💡", "VOCÊ SABIA?", c) for c in _curiosidades_dia(next_round, up_day, 2)]
            if cards:
                blocks.append(f'<div style="display:flex;gap:8px;align-items:stretch;margin-top:11px">'
                              f'{"".join(cards)}</div>')
        except Exception:
            pass
        if blocks:
            return "".join(blocks)
    # fallback (fase de grupos ou tudo indisponível)
    return ('<div style="font-size:14px;color:#e9f5ef;line-height:1.6">'
            + "<br>".join("● " + c for c in curiosidades(last_round)) + '</div>')


def img_b64(name):
    p = os.path.join(HERE, name)
    if os.path.exists(p):
        return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
    return None


def caricatura_b64():
    """Lê a-rodada/ricardo.png e LIMPA automaticamente um fundo claro 'queimado' (o xadrez
    de transparência que o Nano Banana às vezes exporta como pixels). Assim você só troca a
    imagem na pasta e o pôster sai certo. Já-transparente ou fundo sólido escuro = mantém."""
    p = os.path.join(HERE, "ricardo.png")
    if not os.path.exists(p):
        return None
    try:
        from PIL import Image
        im = Image.open(p).convert("RGBA")
        px = im.load(); w, h = im.size
        corners = [px[1, 1], px[w - 2, 1], px[1, h - 2], px[w - 2, h - 2]]
        light = lambda c: (max(c[:3]) - min(c[:3])) <= 24 and sum(c[:3]) / 3 >= 190
        # já tem transparência nas bordas, ou fundo sólido NÃO-claro (ex.: verde) → usa como está
        if any(c[3] < 250 for c in corners) or not all(light(c) for c in corners):
            return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
        # fundo claro opaco (xadrez/branco): flood-fill das bordas até o contorno do desenho
        seen = bytearray(w * h)
        dq = deque()
        for x in range(w):
            dq.append((x, 0)); dq.append((x, h - 1))
        for y in range(h):
            dq.append((0, y)); dq.append((w - 1, y))
        while dq:
            x, y = dq.pop()
            if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]:
                continue
            seen[y * w + x] = 1
            c = px[x, y]
            if not light(c):
                continue
            px[x, y] = (c[0], c[1], c[2], 0)
            dq.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
        buf = io.BytesIO(); im.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print(f"  (limpeza da caricatura pulada: {e})")
        return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()


def caricatura_html():
    src = caricatura_b64()
    if src:
        return (f'<img src="{src}" alt="Ricardo" style="width:88px;height:88px;border-radius:50%;'
                f'object-fit:cover;border:3px solid #f4c430;flex:0 0 auto;background:#114a37"/>')
    # mascote vetorial (placeholder até a caricatura oficial do Ricardo chegar)
    return ('<svg width="88" height="88" viewBox="0 0 74 74" style="flex:0 0 auto;border-radius:50%;'
            'border:3px solid #f4c430;background:#114a37">'
            '<ellipse cx="37" cy="42" rx="17" ry="18" fill="#e8b48c"/>'
            '<path d="M20 36 Q37 14 54 36 Q50 26 37 24 Q24 26 20 36Z" fill="#d9a07a"/>'
            '<rect x="25" y="39" width="11" height="8" rx="2" fill="none" stroke="#222" stroke-width="2"/>'
            '<rect x="38" y="39" width="11" height="8" rx="2" fill="none" stroke="#222" stroke-width="2"/>'
            '<line x1="36" y1="42" x2="38" y2="42" stroke="#222" stroke-width="2"/>'
            '<path d="M31 52 Q37 56 43 52 L43 57 Q37 62 31 57Z" fill="#cfcfcf"/></svg>')


def grp_chip(j):
    # Selo de GRUPO só quando os DOIS times são do mesmo grupo (fase de grupos). No mata-mata
    # os times são de grupos diferentes, e marcar o grupo do mandante seria informação errada —
    # então o selo é omitido (até virar rótulo de fase numa v2, se quisermos).
    gh, ga = TEAM_GROUP.get(j["home"]), TEAM_GROUP.get(j["away"])
    if not gh or gh != ga:
        return ""
    return (f'<span style="font-family:Anton,sans-serif;font-size:11px;color:#0a3d2c;background:#f4c430;'
            f'border-radius:5px;padding:2px 7px;flex:0 0 auto;letter-spacing:.3px">GRUPO {gh}</span>')


def build_html(last_round, next_round, res_day, up_day, today_day=None):
    # today_day como parâmetro (default = today_agenda_day() real) — permite testar os 3 estados
    # abaixo com datas fixas, sem precisar mockar o relógio.
    today_day = today_day or today_agenda_day()
    lbl_jogos = label_day(up_day)
    lbl_res = label_day(res_day)
    # 3 estados do bloco "próximo(s) jogo(s)" — NUNCA diga "hoje" quando o próximo jogo é dia
    # futuro (bug real de 08/07: disse "JOGOS DE HOJE: França × Marrocos" com o jogo 2 dias à
    # frente, no vão entre Oitavas e Quartas). HOJE = o próximo jogo é hoje mesmo. VÃO = existe
    # próximo jogo, mas não é hoje (mostra a data real + deixa explícito que hoje não tem jogo).
    # FIM DE COPA = não há mais nenhum jogo futuro.
    if up_day is None:
        jogos_titulo = "🏆 ACABOU A COPA"
        jogos_sub = "Sem mais jogos até 2030 — hora de cobrar o campeão do bolão"
        header_sub = lbl_res
    elif up_day == today_day:
        jogos_titulo = "📅 JOGOS DE HOJE"
        jogos_sub = f"{lbl_jogos} · horário de Brasília"
        header_sub = f"Hoje · {lbl_jogos}"
    else:
        jogos_titulo = "⏳ PRÓXIMO JOGO"
        jogos_sub = f"{lbl_jogos} · horário de Brasília — hoje ninguém joga"
        header_sub = lbl_jogos
    small = "font-family:Segoe UI,system-ui;font-size:11px;color:#bfe3d2;font-weight:600;letter-spacing:0"
    ball = img_b64("trionda.png")
    ball_header = (f'<img src="{ball}" alt="" style="width:62px;height:62px;flex:0 0 auto">' if ball else "")
    ball_wm = (f'<img src="{ball}" alt="" style="position:absolute;width:300px;height:300px;'
               f'right:-70px;bottom:-70px;opacity:.06;z-index:0;pointer-events:none">' if ball else "")

    # bandeira com largura fixa → nomes alinhados em coluna (régua vertical) nas duas seções
    flg = lambda t: f'<span style="display:inline-block;min-width:22px;text-align:center">{flag(t)}</span>'

    def res_row(j):
        win = j["hs"] != j["as"]
        sc = (f'<span style="font-family:Anton,sans-serif;font-size:22px;min-width:64px;text-align:center;'
              f'white-space:nowrap;color:{"#f4c430" if win else "#fff"}">{j["hs"]} × {j["as"]}</span>')
        nm = "flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"
        return (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;'
                f'background:rgba(255,255,255,.06);border-radius:10px;padding:8px 14px">'
                f'{grp_chip(j)}'
                f'<span style="{nm}">{flg(j["home"])} {j["home"]}</span>{sc}'
                f'<span style="{nm};text-align:right">{j["away"]} {flg(j["away"])}</span></div>')

    def jogo_row(j):
        # AGENDA: só o horário (sem placar), mesmo que o jogo já tenha começado/encerrado.
        tag = (f'<b style="font-family:Anton,sans-serif;font-size:18px;color:#f4c430;min-width:54px">'
               f'{sp_time(j["date"])}</b>')
        return (f'<div style="display:flex;align-items:center;gap:11px;background:rgba(255,255,255,.06);'
                f'border-radius:10px;padding:8px 14px">{grp_chip(j)}{tag}'
                f'<span style="font-size:15px">{flg(j["home"])} {j["home"]} '
                f'<span style="color:#7fae98">×</span> {j["away"]} {flg(j["away"])}</span></div>')

    resultados = "".join(res_row(j) for j in last_round) or '<div style="color:#bfe3d2">Sem jogos na rodada anterior.</div>'
    curis_html = curiosidades_html(last_round, next_round, up_day)
    jogos = "".join(jogo_row(j) for j in next_round) or '<div style="color:#bfe3d2">Sem jogos nesta rodada.</div>'

    def sec(txt, extra=""):
        return (f'<div style="font-family:Anton,sans-serif;font-size:17px;letter-spacing:.5px;color:#f4c430;'
                f'margin:14px 0 8px;display:flex;align-items:center;gap:8px">{txt}'
                f'<span style="flex:1;height:2px;background:rgba(244,196,48,.25);border-radius:2px"></span>{extra}</div>')

    res_extra = f'<span style="{small}">{lbl_res}</span>' if lbl_res else ""
    jogos_extra = f'<span style="{small}">{jogos_sub}</span>'
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">
<style>*{{margin:0;box-sizing:border-box}}body{{background:#06281c}}</style></head>
<body><div id="poster" style="position:relative;overflow:hidden;width:600px;font-family:'Segoe UI',system-ui,sans-serif;background:#0a3d2c;color:#fff">
  {ball_wm}
  <div style="position:relative;z-index:1;height:5px;background:linear-gradient(90deg,#E61D25 0%,#F4C430 38%,#27B14B 68%,#3D6BFF 100%)"></div>
  <div style="position:relative;z-index:1;background:#0c4a35;padding:18px 20px;display:flex;align-items:center;gap:16px;border-bottom:4px solid #f4c430">
    {caricatura_html()}
    <div style="flex:1;min-width:0">
      <div style="font-size:12px;letter-spacing:3px;color:#f4c430;font-weight:800">BOLÃO MIHA 2026</div>
      <div style="font-family:Anton,sans-serif;font-size:42px;line-height:.95;letter-spacing:1px">A RODADA</div>
      <div style="font-size:12.5px;color:#bfe3d2;margin-top:4px">{header_sub} · por Ricardo Mihalik</div>
    </div>
    {ball_header}
  </div>
  <div style="position:relative;z-index:1;padding:6px 20px 20px">
    {sec("📋 RESULTADOS", res_extra)}
    <div style="display:grid;gap:7px">{resultados}</div>
    {sec("🔥 CURIOSIDADES")}
    {curis_html}
    {sec(jogos_titulo, jogos_extra)}
    <div style="display:grid;gap:7px">{jogos}</div>
  </div>
  <div style="position:relative;z-index:1;background:#0c4a35;padding:12px 20px;font-size:12px;color:#bfe3d2;text-align:center;border-top:1px solid rgba(255,255,255,.1)">⚽ Classificação ao vivo no site do bolão · boa sorte! 🏆</div>
</div></body></html>"""


def render_png(html):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=2)
        pg.set_content(html, wait_until="networkidle")
        pg.evaluate("async () => { try { await document.fonts.ready; } catch (e) {} }")  # garante a fonte Anton aplicada antes do print
        pg.locator("#poster").screenshot(path=OUT)
        b.close()


def main():
    events = fetch_events()
    last_round, next_round, res_day, up_day = pick_rounds(events)
    # Pós-Copa: sem jogos futuros E último resultado já antigo → não republica o pôster "morto"
    # todos os dias. (O workflow só publica se hoje.png existir.)
    if up_day is None and res_day:
        try:
            # dt.date.today() é NAIVE (pega o fuso do relógio local de quem roda) — troca por
            # today_agenda_day() (sempre UTC explícito) pra não divergir da mesma noção de "hoje"
            # usada em build_html() logo abaixo.
            if (dt.date.fromisoformat(today_agenda_day()) - dt.date.fromisoformat(res_day)).days > 3:
                print(f"Torneio encerrado (último dia com jogo: {res_day}) — sem pôster novo.")
                return
        except Exception:
            pass
    html = build_html(last_round, next_round, res_day, up_day)
    if os.environ.get("RODADA_HTML_ONLY"):
        with open(os.path.join(HERE, "preview.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML salvo em a-rodada/preview.html (modo sem render)")
        return
    render_png(html)
    print(f"OK · pôster gerado: {OUT} · rodada passada: {len(last_round)} jogos · hoje: {len(next_round)} jogos")


if __name__ == "__main__":
    main()
