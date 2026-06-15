"""
CONFERÊNCIA INDEPENDENTE (backup de checagem) — Bolão Miha 2026.

A fonte PRIMÁRIA é a ESPN (results.csv, via fetch_results.py). Este módulo cruza
ESSES placares com uma SEGUNDA fonte independente — a football-data.org — e aponta
qualquer divergência em jogo ENCERRADO. É a rede de segurança: se as duas fontes
discordarem num placar já finalizado, gravamos um alerta e o workflow nos avisa.

Saída: data/cross_check.json
  status: "ok" | "divergencia" | "fonte_indisponivel"
  compared / agree / discrepancies / pendente_2a_fonte

NUNCA derruba o pipeline: sempre sai com código 0 e grava o relatório. Quem dispara
o e-mail de alerta é um passo final do workflow que lê este JSON.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "cross_check.json")
FD_API = "https://api.football-data.org/v4/competitions/WC/matches"

SP = timezone(timedelta(hours=-3))


def fetch_football_data(token):
    req = urllib.request.Request(FD_API, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    from catalog import get_catalog
    from fetch_results import EN_PT, load_results

    catalog = get_catalog()
    by_pair = {frozenset((m["home"], m["away"])): m for m in catalog}
    results, _ = load_results()   # match_id → linha (ESPN é quem preenche)

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    fd_by_mid = {}
    source_ok = bool(token)
    if token:
        try:
            data = fetch_football_data(token)
            for fx in data.get("matches", []):
                if fx.get("stage") and "GROUP" not in fx["stage"].upper():
                    continue
                h = EN_PT.get((fx.get("homeTeam", {}).get("name") or "").lower())
                a = EN_PT.get((fx.get("awayTeam", {}).get("name") or "").lower())
                if not h or not a:
                    continue
                m = by_pair.get(frozenset((h, a)))
                if not m:
                    continue
                ft = fx.get("score", {}).get("fullTime", {})
                finished = fx.get("status") == "FINISHED"
                fd_by_mid[m["match_id"]] = {
                    "finished": finished,
                    "score": {h: ft.get("home"), a: ft.get("away")},
                    "home": m["home"], "away": m["away"],
                }
        except Exception as e:
            source_ok = False
            print(f"  ⚠ football-data indisponível: {e}")

    discrepancies, pendente, compared, agree = [], [], 0, 0
    for mid, fd in fd_by_mid.items():
        row = results.get(mid, {})
        our_status = (row.get("status") or "scheduled").strip()
        hs, as_ = row.get("home_score", ""), row.get("away_score", "")
        our_finished = our_status == "finished" and str(hs).strip() != "" and str(as_).strip() != ""
        if our_finished and fd["finished"]:
            compared += 1
            our = {fd["home"]: int(hs), fd["away"]: int(as_)}
            if all(our.get(t) == fd["score"].get(t) for t in our):
                agree += 1
            else:
                discrepancies.append({
                    "match_id": mid,
                    "teams": f"{fd['home']} x {fd['away']}",
                    "primaria": f"{hs}x{as_}  (ESPN)",
                    "secundaria": f"{fd['score'].get(fd['home'])}x{fd['score'].get(fd['away'])}  (football-data)",
                    "lock": str(row.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes"),
                })
        elif our_finished and not fd["finished"]:
            pendente.append(mid)   # ESPN já fechou; football-data (mais lenta) ainda não

    if discrepancies:
        status = "divergencia"
    elif not source_ok and compared == 0:
        status = "fonte_indisponivel"
    else:
        status = "ok"

    report = {
        "checked_at": datetime.now(SP).isoformat(),
        "source_a": "ESPN", "source_b": "football-data.org",
        "source_b_ok": source_ok,
        "status": status, "compared": compared, "agree": agree,
        "discrepancies": discrepancies,
        "pendente_2a_fonte": sorted(pendente),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Conferência 2 fontes (ESPN × football-data) · {agree}/{compared} batem · "
          f"2ª fonte ainda apurando: {len(pendente)} · status: {status}")
    for d in discrepancies:
        print(f"  ⛔ DIVERGÊNCIA {d['match_id']} {d['teams']}: {d['primaria']} ≠ {d['secundaria']}"
              + ("  [lock manual ativo]" if d["lock"] else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
