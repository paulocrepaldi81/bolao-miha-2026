"""
"A RODADA" — gera o PNG diário do Bolão Miha 2026 (TAREFA SEPARADA da landing page).

Pega da própria Copa (ESPN, API pública) a ÚLTIMA rodada encerrada (resultados +
curiosidades) e os PRÓXIMOS jogos (com horário de São Paulo), monta um pôster estilo
futebol/cartoon com a caricatura do Ricardo e exporta a-rodada/hoje.png.

Independe do relógio do runner: usa o estado real do torneio (jogos post/pre), não a
data "de hoje". O rótulo de data vem da data do próximo jogo (string do evento).

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


def _artil_row(medal, nome, team, gols, gmax):
    pct = int(gols / gmax * 100) if gmax else 0
    bar = (f'<span style="flex:0 0 64px;height:8px;border-radius:5px;background:rgba(244,196,48,.18);'
           f'overflow:hidden;display:inline-block"><span style="display:block;height:100%;width:{pct}%;'
           f'background:#f4c430;border-radius:5px"></span></span>')
    return (f'<div style="display:flex;align-items:center;gap:9px;background:rgba(255,255,255,.06);'
            f'border-radius:10px;padding:6px 12px">'
            f'<span style="font-size:15px;flex:0 0 auto">{medal}</span>'
            f'<span style="flex:0 0 22px;text-align:center">{flag(team) if team else ""}</span>'
            f'<span style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
            f'font-size:14px;font-weight:600">{_short_name(nome)}</span>{bar}'
            f'<span style="font-family:Anton,sans-serif;font-size:18px;min-width:20px;text-align:right;'
            f'color:#f4c430">{gols}</span></div>')


def _subsec(txt):
    return (f'<div style="font-family:Anton,sans-serif;font-size:13px;color:#f4c430;letter-spacing:.4px;'
            f'margin:12px 0 6px;display:flex;align-items:center;gap:7px">{txt}'
            f'<span style="flex:1;height:1px;background:rgba(244,196,48,.20)"></span></div>')


def _card_curiosidade(txt):
    return (f'<div style="background:rgba(244,196,48,.10);border-left:3px solid #f4c430;border-radius:8px;'
            f'padding:9px 13px;margin-top:12px"><div style="font-family:Anton,sans-serif;font-size:12px;'
            f'color:#f4c430;letter-spacing:.5px;margin-bottom:3px">💡 VOCÊ SABIA?</div>'
            f'<div style="font-size:13px;color:#e9f5ef;line-height:1.45">{txt}</div></div>')


def _artilharia_top3():
    fl = _load_json(os.path.join(ENG_DATA, "facts_live.json"), {})
    return ((fl.get("partials") or {}).get("scorers_top") or [])[:3]


def _proxima_fase(next_round, pairs):
    """'Quem vencer A×B pega o vencedor de C×D nas oitavas' — do slot-irmão no chaveamento."""
    bracket = _load_json(os.path.join(ENG_DATA, "knockout_bracket.json"), {})
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
        nxt = _PHASE_NEXT.get(rnd, "próxima fase")
        return (f"Quem vencer {flag(j['home'])} {j['home']} × {j['away']} {flag(j['away'])} pega o "
                f"vencedor de {flag(s['home'])} {s['home']} × {s['away']} {flag(s['away'])} nas <b>{nxt}</b>.")
    return None


def _curiosidade_dia(next_round, up_day):
    cur = _load_json(os.path.join(HERE, "curiosidades_selecoes.json"), {})
    times = [t for j in next_round for t in (j["home"], j["away"]) if t in cur and not t.startswith("_")]
    if not times:
        return None
    seed = int(hashlib.md5(str(up_day).encode()).hexdigest(), 16)   # escolha estável por dia
    team = sorted(set(times))[seed % len(set(times))]
    fatos = cur[team]
    fato = fatos[seed % len(fatos)]
    return f"{flag(team)} <b>{team}:</b> {fato}"


def curiosidades_html(last_round, next_round, up_day):
    """HTML da seção CURIOSIDADES. No mata-mata: 3 blocos (artilharia/próxima fase/você sabia).
    Em grupos OU se tudo falhar: os bullets clássicos (gols/goleada/empate)."""
    pairs = _bracket_pairs()
    if next_round and is_knockout(next_round, pairs):
        blocks = []
        try:
            top = _artilharia_top3()
            if top:
                gmax = top[0].get("gols") or 1
                medals = ["🥇", "🥈", "🥉"]
                rows = "".join(_artil_row(medals[i], t.get("nome"), t.get("equipe"), t.get("gols", 0), gmax)
                               for i, t in enumerate(top[:3]))
                blocks.append(_subsec("ARTILHARIA") + f'<div style="display:grid;gap:5px">{rows}</div>')
        except Exception:
            pass
        try:
            pf = _proxima_fase(next_round, pairs)
            if pf:
                blocks.append(_subsec("🔜 PRÓXIMA FASE") +
                              f'<div style="font-size:13px;color:#e9f5ef;line-height:1.5">{pf}</div>')
        except Exception:
            pass
        try:
            cd = _curiosidade_dia(next_round, up_day)
            if cd:
                blocks.append(_card_curiosidade(cd))
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


def build_html(last_round, next_round, res_day, up_day):
    lbl_jogos = label_day(up_day)
    lbl_res = label_day(res_day)
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
    jogos_extra = f'<span style="{small}">{lbl_jogos} · horário de Brasília</span>'
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
      <div style="font-size:12.5px;color:#bfe3d2;margin-top:4px">{('Hoje · ' + lbl_jogos) if lbl_jogos else lbl_res} · por Ricardo Mihalik</div>
    </div>
    {ball_header}
  </div>
  <div style="position:relative;z-index:1;padding:6px 20px 20px">
    {sec("📋 RESULTADOS", res_extra)}
    <div style="display:grid;gap:7px">{resultados}</div>
    {sec("🔥 CURIOSIDADES")}
    {curis_html}
    {sec("📅 JOGOS DE HOJE", jogos_extra)}
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
            if (dt.date.today() - dt.date.fromisoformat(res_day)).days > 3:
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
