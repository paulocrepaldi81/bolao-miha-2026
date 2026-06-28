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
import csv
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

    # 2ª fonte TAMBÉM confere o MATA-MATA (antes ficava cega no KO): junta os pares do
    # chaveamento + os resultados do KO. A football-data põe a PRORROGAÇÃO no fullTime e os
    # pênaltis à parte — mesma base do nosso placar (ESPN). Comparação é por time (orientação
    # não importa). Fail-closed: arquivo ausente/ilegível só não adiciona nada.
    try:
        kb = json.load(open(os.path.join(HERE, "data", "knockout_bracket.json"), encoding="utf-8"))
        for ents in (kb.values() if isinstance(kb, dict) else []):
            if isinstance(ents, list):
                for e in ents:
                    if e.get("home") and e.get("away"):
                        by_pair[frozenset((e["home"], e["away"]))] = {
                            "match_id": e["slot"], "home": e["home"], "away": e["away"]}
    except Exception:
        pass
    try:
        for r in csv.DictReader(open(os.path.join(HERE, "data", "knockout_results.csv"),
                                     newline="", encoding="utf-8")):
            if r.get("slot"):
                results[r["slot"]] = {"status": r.get("status"), "home_score": r.get("home_score"),
                                      "away_score": r.get("away_score"), "lock": r.get("lock", "")}
    except Exception:
        pass

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    fd_by_mid = {}
    source_ok = bool(token)
    if token:
        try:
            data = fetch_football_data(token)
            for fx in data.get("matches", []):
                # confere grupos E mata-mata: casa por par de times (group ou KO) com o by_pair
                h = EN_PT.get((fx.get("homeTeam", {}).get("name") or "").lower())
                a = EN_PT.get((fx.get("awayTeam", {}).get("name") or "").lower())
                if not h or not a:
                    continue
                m = by_pair.get(frozenset((h, a)))
                if not m:
                    continue
                ft = fx.get("score", {}).get("fullTime", {})
                hs_fd, as_fd = ft.get("home"), ft.get("away")
                fd_by_mid[m["match_id"]] = {
                    "finished": fx.get("status") == "FINISHED",
                    # a football-data às vezes marca FINISHED mas ainda não preencheu o
                    # placar (None) — isso é ATRASO da 2ª fonte, NÃO divergência.
                    "has_score": hs_fd is not None and as_fd is not None,
                    "score": {h: hs_fd, a: as_fd},
                    "home": m["home"], "away": m["away"],
                }
        except Exception as e:
            source_ok = False
            print(f"  ⚠ football-data indisponível: {e}")

    discrepancies, resolvidas, pendente, compared, agree = [], [], [], 0, 0
    for mid, fd in fd_by_mid.items():
        row = results.get(mid, {})
        our_status = (row.get("status") or "scheduled").strip()
        hs, as_ = row.get("home_score", ""), row.get("away_score", "")
        # exige placar NUMÉRICO (não só não-vazio): um valor estranho no results.csv não pode
        # derrubar a conferência (int() abaixo) — o módulo promete nunca derrubar o pipeline.
        our_finished = (our_status == "finished"
                        and str(hs).strip().isdigit() and str(as_).strip().isdigit())
        # só compara quando AS DUAS fontes têm placar real; senão a 2ª ainda está apurando
        if our_finished and fd["finished"] and fd["has_score"]:
            compared += 1
            our = {fd["home"]: int(hs), fd["away"]: int(as_)}
            if all(our.get(t) == fd["score"].get(t) for t in our):
                agree += 1
            else:
                locked = str(row.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes")
                entry = {
                    "match_id": mid,
                    "teams": f"{fd['home']} x {fd['away']}",
                    "primaria": f"{hs}x{as_}  (ESPN)",
                    "secundaria": f"{fd['score'].get(fd['home'])}x{fd['score'].get(fd['away'])}  (football-data)",
                    "lock": locked,
                }
                if locked:
                    # Organizador JÁ DECIDIU (lock=sim em results.csv): vale o placar da fonte
                    # PRIMÁRIA (ESPN). A 2ª fonte ainda discorda, mas a divergência está
                    # RESOLVIDA — conta como conferida e NÃO dispara alerta/banner vermelho.
                    agree += 1
                    resolvidas.append(entry)
                else:
                    discrepancies.append(entry)
        elif our_finished and not (fd["finished"] and fd["has_score"]):
            pendente.append(mid)   # ESPN já fechou; football-data (mais lenta) ainda sem placar

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
        "resolvidas": resolvidas,   # divergências decididas pelo organizador (vale a ESPN)
        "pendente_2a_fonte": sorted(pendente),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Conferência 2 fontes (ESPN × football-data) · {agree}/{compared} batem · "
          f"resolvidas (vale ESPN): {len(resolvidas)} · 2ª fonte ainda apurando: {len(pendente)} · status: {status}")
    for d in discrepancies:
        print(f"  ⛔ DIVERGÊNCIA {d['match_id']} {d['teams']}: {d['primaria']} ≠ {d['secundaria']}"
              + ("  [lock manual ativo]" if d["lock"] else ""))
    for d in resolvidas:
        print(f"  ✓ RESOLVIDA {d['match_id']} {d['teams']}: vale {d['primaria']} (ESPN); "
              f"football-data marcou {d['secundaria']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
