"""
Captura os jogos do MATA-MATA na ESPN e gera:
  - data/knockout_results.csv   (slot,home_score,away_score,status,special,lock) p/ a PONTUAÇÃO
  - data/knockout_fixtures.json (slot -> home,away,kickoff,status,winner,decided_by,pen_*) p/ EXIBIÇÃO

Regras:
  • Placar = tempo normal + PRORROGAÇÃO (a ESPN já inclui em 'score'); pênaltis (shootoutScore) NÃO
    pontuam — entram só como info de exibição (quem avançou).
  • Orientação = a do CHAVEAMENTO (home do slot). O placar é indexado pelo NOME do time, então já
    sai na orientação certa do slot.
  • Casa o confronto real ao slot por PAR DE TIMES (knockout_bracket.json). Slot sem times reais
    ainda (placeholder de fase futura) é ignorado — nunca chuta.
  • lock=sim nunca é sobrescrito (correção manual do organizador vence).
  • FAIL-CLOSED: qualquer erro de rede não derruba o pipeline (sai 0, mantém o CSV atual).

Uso: python3 fetch_knockout.py [--dry-run]
"""
import argparse, csv, json, os
from fetch_results import EN_PT, load_espn_events

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BRACKET = os.path.join(DATA, "knockout_bracket.json")
RES = os.path.join(DATA, "knockout_results.csv")
FIX = os.path.join(DATA, "knockout_fixtures.json")

SLUG_ROUND = {"round-of-32": "R32", "round-of-16": "R16", "quarterfinals": "QF",
              "semifinals": "SF", "final": "FIN", "third-place": "TER"}


def load_bracket_pairs():
    """{frozenset(home,away): entry} — só os slots com os DOIS times reais definidos."""
    try:
        bj = json.load(open(BRACKET, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for entries in bj.values():
        if not isinstance(entries, list):
            continue
        for e in entries:
            h, a = e.get("home"), e.get("away")
            if h and a:
                out[frozenset((h, a))] = e
    return out


def load_existing():
    rows, order = {}, []
    if os.path.exists(RES):
        for r in csv.DictReader(open(RES, newline="", encoding="utf-8")):
            if r.get("slot"):
                rows[r["slot"]] = r
                order.append(r["slot"])
    return rows, order


def fetch():
    pairs = load_bracket_pairs()
    res, fix, unmatched = {}, {}, []
    for ev in load_espn_events():
        rnd = SLUG_ROUND.get(((ev.get("season") or {}).get("slug") or ""))
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors", [])
        if len(cs) != 2:
            continue
        score, names, winner, pen = {}, [], None, {}
        ok = True
        for c in cs:
            raw = (c.get("team", {}).get("displayName") or c.get("team", {}).get("name") or "")
            pt = EN_PT.get(raw.strip().lower())
            if not pt:
                ok = False
                break
            names.append(pt)
            try:
                score[pt] = int(c.get("score"))
            except (TypeError, ValueError):
                score[pt] = None
            if c.get("winner"):
                winner = pt
            ss = c.get("shootoutScore")
            if ss not in (None, ""):
                try:
                    pen[pt] = int(ss)
                except (TypeError, ValueError):
                    pass
        if not ok:
            continue
        e = pairs.get(frozenset(names))
        if not e:
            if rnd:                       # parece mata-mata mas não casou → reporta
                unmatched.append(" x ".join(names))
            continue
        slot = e["slot"]
        t = ev.get("status", {}).get("type", {})
        state, completed = t.get("state"), bool(t.get("completed"))
        status = "finished" if completed else ("live" if state == "in" else "scheduled")
        hs, as_ = score.get(e["home"]), score.get(e["away"])
        res[slot] = {"slot": slot, "home_score": hs, "away_score": as_,
                     "status": status, "special": "sim" if e.get("special") else ""}
        decided = None
        if status == "finished":
            decided = "pen" if (hs is not None and hs == as_) else "normal"
        fix[slot] = {"home": e["home"], "away": e["away"],
                     "kickoff": ev.get("date") or e.get("kickoff"),
                     "status": status, "winner": winner, "decided_by": decided,
                     "pen_home": pen.get(e["home"]), "pen_away": pen.get(e["away"])}
    return res, fix, unmatched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        res, fix, unmatched = fetch()
    except Exception as ex:
        print(f"  ⚠ ESPN (mata-mata) indisponível: {ex}")
        return 0   # fail-closed
    if not res:
        print("mata-mata: nenhum confronto resolvido ainda (sem times reais no bracket) — nada a gravar.")
        return 0
    existing, order = load_existing()
    for slot, r in res.items():
        cur = existing.get(slot, {})
        if str(cur.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes"):
            continue   # correção manual vence
        hs, as_ = r["home_score"], r["away_score"]
        if r["status"] in ("finished", "live") and hs is not None and as_ is not None:
            existing[slot] = {"slot": slot, "home_score": str(hs), "away_score": str(as_),
                              "status": r["status"], "special": r["special"], "lock": cur.get("lock", "")}
        else:   # agendado / sem placar → limpa qualquer placar residual
            existing[slot] = {"slot": slot, "home_score": "", "away_score": "",
                              "status": r["status"] or "scheduled", "special": r["special"], "lock": cur.get("lock", "")}
        if slot not in order:
            order.append(slot)

    if args.dry_run:
        for s in order:
            x = existing[s]
            print(f"  {s}: {x['home_score']}x{x['away_score']} [{x['status']}]")
        return 0

    fields = ["slot", "home_score", "away_score", "status", "special", "lock"]
    with open(RES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for s in order:
            w.writerow({k: existing[s].get(k, "") for k in fields})
    with open(FIX, "w", encoding="utf-8") as f:
        json.dump(fix, f, ensure_ascii=False, indent=1)

    fin = sum(1 for x in existing.values() if x["status"] == "finished")
    live = sum(1 for x in existing.values() if x["status"] == "live")
    print(f"OK · mata-mata: {len(existing)} slot(s) · {fin} encerrado(s) · {live} ao vivo")
    if unmatched:
        print("  ⚠ sem casamento (mata-mata):", unmatched[:8])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
