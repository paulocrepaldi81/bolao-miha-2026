"""
Apura automaticamente as CATEGORIAS EXTRAS a partir dos resultados e da API.

Camadas:
  1. Derivado dos placares já buscados (results.csv): empates na 1ª fase,
     maior nº de gols num jogo, mais goleadora / menos vazada (parciais).
  2. API football-data.org (FOOTBALL_DATA_TOKEN): artilharia (/scorers).
  3. API-Football (APIFOOTBALL_KEY, api-football.com): LANCES — cartões
     vermelhos e gols contra. (O plano grátis da football-data.org NÃO entrega
     lances — diagnóstico de 12/jun: bookings/goals sempre vazios.)

Saídas:
  - data/facts_live.json  → parciais "ao vivo" exibidos no site + memória da varredura
  - data/facts.json       → SÓ preenche campo ainda null quando o fato é DEFINITIVO:
      · equipe_1o_expulso / equipe_1o_gol_contra: 1ª ocorrência, com todos os jogos
        anteriores já varridos (garantia de ordem cronológica)
      · empates_1f: quando os 72 jogos da fase de grupos encerrarem
    O organizador continua mandando: valor não-null em facts.json NUNCA é alterado.

Limite da API (plano grátis ~10 req/min): varre até 6 partidas por execução,
com pausa entre chamadas; o robô roda a cada 20 min e alcança o ritmo da Copa.
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FACTS = os.path.join(DATA, "facts.json")
LIVE = os.path.join(DATA, "facts_live.json")
API = "https://api.football-data.org/v4"
AF = "https://v3.football.api-sports.io"      # API-Football (lances)
AF_LEAGUE, AF_SEASON = 1, 2026                # FIFA World Cup
SCAN_PER_RUN = 6


def api_get(path, token):
    req = urllib.request.Request(API + path, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def af_get(path, key):
    req = urllib.request.Request(AF + path, headers={"x-apisports-key": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    from catalog import get_catalog
    from fetch_results import EN_PT, load_results

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    facts = load_json(FACTS, {})
    live = load_json(LIVE, {"partials": {}, "scanned": [], "first_red": None, "first_own": None})
    partials = live["partials"]
    catalog = get_catalog()
    results, _ = load_results()
    changed_facts = False

    # ---------- 1) Derivados dos placares (sem custo de API) ----------
    finished = [(m, results[m["match_id"]]) for m in catalog
                if results.get(m["match_id"], {}).get("status") == "finished"
                and results[m["match_id"]].get("home_score") is not None]
    if finished:
        draws = sum(1 for _, r in finished if int(r["home_score"]) == int(r["away_score"]))
        partials["empates_1f"] = f"{draws} até agora ({len(finished)}/72 jogos da 1ª fase)"
        if len(finished) == len(catalog) and facts.get("empates_1f") is None:
            facts["empates_1f"] = draws
            changed_facts = True
            print(f"✔ DEFINIDO empates_1f = {draws} (72/72 jogos encerrados)")

        top_match = max(finished, key=lambda x: int(x[1]["home_score"]) + int(x[1]["away_score"]))
        m, r = top_match
        tot = int(r["home_score"]) + int(r["away_score"])
        partials["mais_gols_jogo"] = f"{tot} gols ({m['home']} {r['home_score']}×{r['away_score']} {m['away']})"

        gp, gc = {}, {}
        for m, r in finished:
            h, a = int(r["home_score"]), int(r["away_score"])
            gp[m["home"]] = gp.get(m["home"], 0) + h
            gp[m["away"]] = gp.get(m["away"], 0) + a
            gc[m["home"]] = gc.get(m["home"], 0) + a
            gc[m["away"]] = gc.get(m["away"], 0) + h
        best_attack = max(gp.items(), key=lambda x: x[1])
        best_def = min(gc.items(), key=lambda x: x[1])
        partials["mais_goleadora"] = f"{best_attack[0]} ({best_attack[1]} gols)"
        partials["menos_vazada"] = f"{best_def[0]} ({best_def[1]} sofrido(s))"

    # ---------- 2) Artilharia via football-data (funciona no plano grátis) ----------
    if token:
        try:
            sc = api_get("/competitions/WC/scorers?limit=3", token)
            scorers = sc.get("scorers", [])
            if scorers:
                s = scorers[0]
                nome = s.get("player", {}).get("name", "?")
                equipe = EN_PT.get((s.get("team", {}).get("name") or "").lower(),
                                   s.get("team", {}).get("name", "?"))
                gols = s.get("goals", "?")
                partials["artilheiro_nome"] = f"{nome} ({equipe}) — {gols} gol(s)"
                partials["artilheiro_equipe"] = equipe
                partials["artilheiro_gols"] = f"{gols} (parcial)"
        except Exception as e:
            print(f"  (artilharia indisponível: {e})")

    # ---------- 3) Lances (expulsões / gols contra) via API-Football ----------
    # O plano grátis da football-data NÃO entrega lances (diagnóstico 12/jun).
    # API-Football grátis = 100 chamadas/dia; só consultamos quando há jogo
    # encerrado ainda não varrido (~2 chamadas por jogo novo).
    af_key = os.environ.get("APIFOOTBALL_KEY", "").strip()
    af_scanned = set(live.get("af_scanned", []))
    iso_by_mid, kick_of = {}, {}
    for m in catalog:
        from build_data import parse_kickoff
        iso = parse_kickoff(m["date"]) or ""
        iso_by_mid[m["match_id"]] = iso
        kick_of[m["match_id"]] = m
    fin_mids = sorted((mid for mid, r in results.items()
                       if r.get("status") == "finished" and mid in iso_by_mid),
                      key=lambda mid: iso_by_mid[mid])
    pending = [mid for mid in fin_mids if mid not in af_scanned][:SCAN_PER_RUN]

    if not af_key:
        if pending:
            print("ℹ Lances (1º expulso/1º gol contra): preencher manualmente em data/facts.json. "
                  "(API-Football só cobre a temporada 2026 em plano PAGO; o código está pronto "
                  "se um dia houver APIFOOTBALL_KEY paga.)")
    elif pending:
        # 1 chamada por DATA com jogo pendente → mapa de fixtures por par de times
        dates = sorted({iso_by_mid[mid][:10] for mid in pending})
        fx_by_pair = {}
        for dt in dates[:3]:
            try:
                resp = af_get(f"/fixtures?league={AF_LEAGUE}&season={AF_SEASON}&date={dt}", af_key)
                if resp.get("errors"):
                    print(f"  ⚠ API-Football errors ({dt}): {resp['errors']}")
                print(f"  fixtures {dt}: {resp.get('results', 0)} resultado(s)")
                for fx in resp.get("response", []):
                    h = EN_PT.get((fx["teams"]["home"]["name"] or "").lower(), fx["teams"]["home"]["name"])
                    a = EN_PT.get((fx["teams"]["away"]["name"] or "").lower(), fx["teams"]["away"]["name"])
                    fx_by_pair[frozenset((h, a))] = fx["fixture"]["id"]
            except Exception as e:
                print(f"⚠ API-Football fixtures {dt}: {e}")
        for mid in pending:
            m = kick_of[mid]
            fxid = fx_by_pair.get(frozenset((m["home"], m["away"])))
            if not fxid:
                print(f"  ⚠ {mid} ({m['home']} x {m['away']}): fixture não encontrada — tentará de novo")
                continue
            try:
                time.sleep(1.5)
                ev = af_get(f"/fixtures/events?fixture={fxid}", af_key).get("response", [])
            except Exception as e:
                print(f"  ⚠ eventos de {mid}: {e}")
                continue
            when = iso_by_mid[mid]
            reds = [e for e in ev if e.get("type") == "Card" and "Red" in (e.get("detail") or "")]
            if reds and live["first_red"] is None:
                e0 = min(reds, key=lambda e: (e.get("time", {}).get("elapsed") or 999))
                t_en = e0.get("team", {}).get("name", "")
                live["first_red"] = {"team": EN_PT.get(t_en.lower(), t_en),
                                     "player": (e0.get("player") or {}).get("name", "?"),
                                     "minute": e0.get("time", {}).get("elapsed"), "utc": when}
                print(f"  🟥 expulsão encontrada: {live['first_red']}")
            owns = [e for e in ev if e.get("type") == "Goal" and "Own" in (e.get("detail") or "")]
            if owns and live["first_own"] is None:
                e0 = min(owns, key=lambda e: (e.get("time", {}).get("elapsed") or 999))
                credited = EN_PT.get((e0.get("team", {}).get("name") or "").lower(),
                                     e0.get("team", {}).get("name", ""))
                suffer = m["away"] if credited == m["home"] else m["home"]   # quem fez o gol contra
                live["first_own"] = {"team": suffer,
                                     "player": (e0.get("player") or {}).get("name", "?"),
                                     "minute": e0.get("time", {}).get("elapsed"), "utc": when}
                print(f"  😅 gol contra encontrado: {live['first_own']}")
            af_scanned.add(mid)
        live["af_scanned"] = sorted(af_scanned)

    # finaliza quando a cronologia está garantida (todos os jogos anteriores varridos)
    def chronology_complete(found):
        earlier = [mid for mid in fin_mids if iso_by_mid[mid] < found["utc"]]
        return all(mid in af_scanned for mid in earlier)

    if live["first_red"]:
        fr = live["first_red"]
        partials["equipe_1o_expulso"] = f"{fr['team']} ({fr['player']}, {fr['minute']}')"
        if facts.get("equipe_1o_expulso") is None and chronology_complete(fr):
            facts["equipe_1o_expulso"] = fr["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_expulso = {fr['team']}")
    elif fin_mids:
        partials["equipe_1o_expulso"] = f"nenhuma expulsão em {len(af_scanned)} jogo(s) varrido(s)"

    if live["first_own"]:
        fo = live["first_own"]
        partials["equipe_1o_gol_contra"] = f"{fo['team']} ({fo['player']}, {fo['minute']}')"
        if facts.get("equipe_1o_gol_contra") is None and chronology_complete(fo):
            facts["equipe_1o_gol_contra"] = fo["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_gol_contra = {fo['team']}")
    elif fin_mids:
        partials["equipe_1o_gol_contra"] = f"nenhum gol contra em {len(af_scanned)} jogo(s) varrido(s)"

    save_json(LIVE, live)
    if changed_facts:
        save_json(FACTS, facts)
    print(f"OK · lances: {len(af_scanned)}/{len(fin_mids)} jogo(s) varrido(s) · parciais: {len(partials)}")


if __name__ == "__main__":
    main()
