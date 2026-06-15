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
import json
import os
import urllib.request

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
    "jordan": "Jordânia", "portugal": "Portugal", "dr congo": "RD Congo", "uzbekistan": "Uzbequistão",
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


def pick_rounds(events):
    finished = [e for e in events if e["state"] == "post" and e["hs"] is not None]
    scheduled = [e for e in events if e["state"] == "pre"]
    last_round = []
    if finished:
        last_day = sp_daykey(finished[-1]["date"])
        last_round = [e for e in finished if sp_daykey(e["date"]) == last_day]
    next_round = []
    if scheduled:
        next_day = sp_daykey(scheduled[0]["date"])
        next_round = [e for e in scheduled if sp_daykey(e["date"]) == next_day]
    return last_round, next_round


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


def img_b64(name):
    p = os.path.join(HERE, name)
    if os.path.exists(p):
        return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
    return None


def caricatura_html():
    src = img_b64("ricardo.png")
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


def build_html(last_round, next_round):
    label = sp_date_label(next_round[0]["date"]) if next_round else (
        sp_date_label(last_round[0]["date"]) if last_round else "")
    ball = img_b64("trionda.png")
    ball_header = (f'<img src="{ball}" alt="" style="width:62px;height:62px;flex:0 0 auto">' if ball else "")
    ball_wm = (f'<img src="{ball}" alt="" style="position:absolute;width:300px;height:300px;'
               f'right:-70px;bottom:-70px;opacity:.06;z-index:0;pointer-events:none">' if ball else "")

    def res_row(j):
        win = j["hs"] != j["as"]
        sc = (f'<span style="font-family:Anton,sans-serif;font-size:22px;'
              f'color:{"#f4c430" if win else "#fff"}">{j["hs"]} × {j["as"]}</span>')
        return (f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'background:rgba(255,255,255,.06);border-radius:10px;padding:8px 14px">'
                f'<span style="flex:1">{FLAG.get(j["home"],"")} {j["home"]}</span>{sc}'
                f'<span style="flex:1;text-align:right">{j["away"]} {FLAG.get(j["away"],"")}</span></div>')

    def jogo_row(j, first):
        bg = "rgba(244,196,48,.14)" if first else "rgba(255,255,255,.06)"
        return (f'<div style="display:flex;align-items:center;gap:12px;background:{bg};'
                f'border-radius:10px;padding:8px 14px">'
                f'<b style="font-family:Anton,sans-serif;font-size:18px;color:#f4c430;min-width:54px">{sp_time(j["date"])}</b>'
                f'<span style="font-size:15px">{FLAG.get(j["home"],"")} {j["home"]} <span style="color:#7fae98">×</span> {j["away"]} {FLAG.get(j["away"],"")}</span></div>')

    resultados = "".join(res_row(j) for j in last_round) or '<div style="color:#bfe3d2">Sem jogos na rodada anterior.</div>'
    curis = "<br>".join("● " + c for c in curiosidades(last_round))
    jogos = "".join(jogo_row(j, i == 0) for i, j in enumerate(next_round)) or '<div style="color:#bfe3d2">Sem jogos hoje.</div>'

    def sec(txt, extra=""):
        return (f'<div style="font-family:Anton,sans-serif;font-size:17px;letter-spacing:.5px;color:#f4c430;'
                f'margin:18px 0 9px;display:flex;align-items:center;gap:8px">{txt}'
                f'<span style="flex:1;height:2px;background:rgba(244,196,48,.25);border-radius:2px"></span>{extra}</div>')

    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com">
<link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">
<style>*{{margin:0;box-sizing:border-box}}body{{background:#06281c}}</style></head>
<body><div id="poster" style="position:relative;overflow:hidden;width:600px;font-family:'Segoe UI',system-ui,sans-serif;background:#0a3d2c;color:#fff">
  {ball_wm}
  <div style="position:relative;z-index:1;background:#0c4a35;padding:18px 20px;display:flex;align-items:center;gap:16px;border-bottom:4px solid #f4c430">
    {caricatura_html()}
    <div style="flex:1;min-width:0">
      <div style="font-size:12px;letter-spacing:3px;color:#f4c430;font-weight:800">BOLÃO MIHA 2026</div>
      <div style="font-family:Anton,sans-serif;font-size:42px;line-height:.95;letter-spacing:1px">A RODADA</div>
      <div style="font-size:12.5px;color:#bfe3d2;margin-top:4px">{label} · por Ricardo Mihalik</div>
    </div>
    {ball_header}
  </div>
  <div style="position:relative;z-index:1;padding:6px 20px 20px">
    {sec("📋 RESULTADOS DA RODADA")}
    <div style="display:grid;gap:7px">{resultados}</div>
    {sec("🔥 CURIOSIDADES")}
    <div style="font-size:14px;color:#e9f5ef;line-height:1.8">{curis}</div>
    {sec("📅 JOGOS DE HOJE", '<span style="font-family:Segoe UI,system-ui;font-size:11px;color:#bfe3d2;font-weight:600;letter-spacing:0">horário de Brasília</span>')}
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
        pg.locator("#poster").screenshot(path=OUT)
        b.close()


def main():
    events = fetch_events()
    last_round, next_round = pick_rounds(events)
    html = build_html(last_round, next_round)
    if os.environ.get("RODADA_HTML_ONLY"):
        with open(os.path.join(HERE, "preview.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML salvo em a-rodada/preview.html (modo sem render)")
        return
    render_png(html)
    print(f"OK · pôster gerado: {OUT} · rodada passada: {len(last_round)} jogos · hoje: {len(next_round)} jogos")


if __name__ == "__main__":
    main()
