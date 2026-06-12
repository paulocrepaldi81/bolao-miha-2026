"""
Apura automaticamente as CATEGORIAS EXTRAS a partir dos resultados e da API.

Camadas:
  1. Derivado dos placares já buscados (results.csv): empates na 1ª fase,
     maior nº de gols num jogo, mais goleadora / menos vazada (parciais).
  2. API football-data.org: artilharia (/scorers) e varredura jogo a jogo de
     cartões vermelhos e gols contra (detalhe de cada partida encerrada).

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
SCAN_PER_RUN = 6
RED_CARDS = {"RED", "YELLOW_RED"}   # expulsão = vermelho direto ou 2º amarelo


def api_get(path, token):
    req = urllib.request.Request(API + path, headers={"X-Auth-Token": token})
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

    if not token:
        print("⚠ Sem FOOTBALL_DATA_TOKEN — só parciais derivadas dos placares.")
        save_json(LIVE, live)
        sys.exit(0)

    # ---------- 2) Artilharia (1 chamada) ----------
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

    # ---------- 3) Varredura de cartões/gols contra (detalhe por partida) ----------
    try:
        fixtures = api_get("/competitions/WC/matches", token).get("matches", [])
    except Exception as e:
        print(f"⚠ lista de partidas indisponível: {e}")
        save_json(LIVE, live)
        return
    fin = [fx for fx in fixtures if fx.get("status") == "FINISHED"]
    fin.sort(key=lambda fx: fx.get("utcDate", ""))
    scanned = set(live["scanned"])
    to_scan = [fx for fx in fin if fx["id"] not in scanned][:SCAN_PER_RUN]

    for fx in to_scan:
        try:
            time.sleep(6.5)   # respeita ~10 req/min do plano grátis
            d = api_get(f"/matches/{fx['id']}", token)
        except Exception as e:
            print(f"  (detalhe {fx['id']} indisponível: {e})")
            break
        md = d.get("match", d)
        # diagnóstico: o que a API realmente entrega neste plano
        print(f"  jogo {fx['id']} ({fx.get('homeTeam',{}).get('name','?')} x {fx.get('awayTeam',{}).get('name','?')}): "
              f"campos={sorted(k for k in md.keys() if k not in ('area','competition','season','odds'))} | "
              f"bookings={len(md.get('bookings') or [])} goals={len(md.get('goals') or [])} "
              f"substitutions={len(md.get('substitutions') or [])}")
        when = fx.get("utcDate", "")
        home_en = (md.get("homeTeam", {}).get("name") or "")
        away_en = (md.get("awayTeam", {}).get("name") or "")
        pt = {home_en: EN_PT.get(home_en.lower(), home_en),
              away_en: EN_PT.get(away_en.lower(), away_en)}

        if live["first_red"] is None:
            reds = [b for b in (md.get("bookings") or []) if b.get("card") in RED_CARDS]
            if reds:
                b = min(reds, key=lambda x: x.get("minute") or 999)
                team_en = b.get("team", {}).get("name", "")
                live["first_red"] = {"team": EN_PT.get(team_en.lower(), team_en),
                                     "player": b.get("player", {}).get("name", "?"),
                                     "minute": b.get("minute"), "utc": when}
        if live["first_own"] is None:
            owns = [g for g in (md.get("goals") or []) if g.get("type") == "OWN"]
            if owns:
                g = min(owns, key=lambda x: x.get("minute") or 999)
                credited_en = g.get("team", {}).get("name", "")
                # quem SOFRE o gol contra é a equipe do autor = a outra equipe
                suffer_en = away_en if credited_en == home_en else home_en
                live["first_own"] = {"team": EN_PT.get(suffer_en.lower(), suffer_en),
                                     "player": g.get("scorer", {}).get("name", "?"),
                                     "minute": g.get("minute"), "utc": when}
        scanned.add(fx["id"])
    live["scanned"] = sorted(scanned)

    # finaliza 1º expulso / 1º gol contra quando a cronologia está garantida
    def chronology_complete(found):
        earlier = [fx for fx in fin if fx.get("utcDate", "") < found["utc"]]
        return all(fx["id"] in scanned for fx in earlier)

    if live["first_red"]:
        fr = live["first_red"]
        partials["equipe_1o_expulso"] = f"{fr['team']} ({fr['player']}, {fr['minute']}')"
        if facts.get("equipe_1o_expulso") is None and chronology_complete(fr):
            facts["equipe_1o_expulso"] = fr["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_expulso = {fr['team']}")
    elif fin:
        partials["equipe_1o_expulso"] = f"nenhuma expulsão em {len(scanned)} jogo(s) varrido(s)"

    if live["first_own"]:
        fo = live["first_own"]
        partials["equipe_1o_gol_contra"] = f"{fo['team']} ({fo['player']}, {fo['minute']}')"
        if facts.get("equipe_1o_gol_contra") is None and chronology_complete(fo):
            facts["equipe_1o_gol_contra"] = fo["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_gol_contra = {fo['team']}")
    elif fin:
        partials["equipe_1o_gol_contra"] = f"nenhum gol contra em {len(scanned)} jogo(s) varrido(s)"

    save_json(LIVE, live)
    if changed_facts:
        save_json(FACTS, facts)
    print(f"OK · varridos {len(to_scan)} jogo(s) nesta execução ({len(scanned)}/{len(fin)} encerrados) "
          f"· parciais: {len(partials)}")


if __name__ == "__main__":
    main()
