"""
CONFERÊNCIA INDEPENDENTE (backup de checagem) — Bolão Miha 2026.

O robô usa a football-data.org como fonte oficial dos placares (results.csv).
Este módulo cruza ESSES placares com uma SEGUNDA fonte independente — a ESPN
(API JSON pública, sem chave) — e aponta qualquer divergência em jogo ENCERRADO.
É a rede de segurança: se as duas fontes discordarem num placar já finalizado,
gravamos um alerta e o workflow nos avisa por e-mail.

Por que ESPN por API e não raspar HTML do Globo/ESPN: a página de notícia muda de
layout sem aviso e quebra o robô em silêncio. A API JSON da ESPN é estruturada e
estável (mesma que alimenta o placar do site deles) — confiável para automação.

Saída: data/cross_check.json
  status: "ok" | "divergencia" | "fonte_indisponivel"
  compared / agree / discrepancies / espn_ahead / unmapped

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
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={a}-{b}"

# ESPN devolve no máx. ~100 eventos por chamada → varremos em janelas para cobrir
# a Copa inteira (11/jun–19/jul) sem perder jogos.
WINDOWS = [("20260611", "20260625"), ("20260626", "20260710"), ("20260711", "20260719")]

SP = timezone(timedelta(hours=-3))

# Nomes "de chaveamento" (ex.: "Group A Winner", "Round of 32 1 Winner") aparecem
# nos jogos de mata-mata ainda sem seleção definida. Não são erro de mapeamento.
_PLACEHOLDER = ("winner", "loser", "place", "group ", "round of",
                "quarterfinal", "semifinal", "final", "tbd")


def _is_placeholder(name):
    n = (name or "").strip().lower()
    return any(p in n for p in _PLACEHOLDER)


def fetch_window(a, b):
    url = ESPN.format(a=a, b=b)
    req = urllib.request.Request(url, headers={"User-Agent": "bolao-miha-crosscheck"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    from catalog import get_catalog
    from fetch_results import EN_PT, load_results

    catalog = get_catalog()
    # par de seleções (sem ordem) → jogo do catálogo
    by_pair = {frozenset((m["home"], m["away"])): m for m in catalog}
    results, _ = load_results()   # match_id → linha (strings)

    espn_by_mid = {}   # match_id → {"score": {time_pt: gols}, "completed": bool}
    unmapped = []
    source_ok = True

    for a, b in WINDOWS:
        try:
            data = fetch_window(a, b)
        except Exception as e:
            source_ok = False
            print(f"  ⚠ ESPN indisponível ({a}-{b}): {e}")
            continue
        for ev in data.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            cs = comp.get("competitors", [])
            if len(cs) != 2:
                continue
            names_pt, score = [], {}
            ok = True
            for c in cs:
                team = c.get("team", {})
                raw = team.get("displayName") or team.get("name") or team.get("shortDisplayName") or ""
                pt = EN_PT.get(raw.strip().lower())
                if not pt:
                    if not _is_placeholder(raw):   # placeholder de chaveamento = ignora em silêncio
                        unmapped.append(raw)
                    ok = False
                    break
                names_pt.append(pt)
                try:
                    score[pt] = int(c.get("score"))
                except (TypeError, ValueError):
                    score[pt] = None
            if not ok:
                continue
            m = by_pair.get(frozenset(names_pt))
            if not m:
                continue   # não é jogo da fase de grupos que mapeamos
            completed = bool(ev.get("status", {}).get("type", {}).get("completed"))
            espn_by_mid[m["match_id"]] = {"score": score, "completed": completed,
                                          "home": m["home"], "away": m["away"]}

    # ---- comparação ----
    discrepancies, espn_ahead, espn_behind, compared, agree = [], [], [], 0, 0
    for mid, e in espn_by_mid.items():
        row = results.get(mid, {})
        our_status = (row.get("status") or "scheduled").strip()
        hs, as_ = row.get("home_score", ""), row.get("away_score", "")
        our_finished = our_status == "finished" and str(hs).strip() != "" and str(as_).strip() != ""

        if our_finished and e["completed"]:
            compared += 1
            our_score = {e["home"]: int(hs), e["away"]: int(as_)}
            if all(our_score.get(t) == e["score"].get(t) for t in our_score):
                agree += 1
            else:
                discrepancies.append({
                    "match_id": mid,
                    "teams": f"{e['home']} x {e['away']}",
                    "oficial": f"{hs}x{as_}  (football-data)",
                    "espn": f"{e['score'].get(e['home'])}x{e['score'].get(e['away'])}  (ESPN)",
                    "lock": str(row.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes"),
                })
        elif e["completed"] and not our_finished:
            espn_ahead.append(mid)   # ESPN já encerrou; robô ainda não atualizou (a próxima busca pega)
        elif our_finished and not e["completed"]:
            espn_behind.append(mid)  # robô já tem; ESPN ainda não fechou (raro; informativo)

    if discrepancies:
        status = "divergencia"
    elif not source_ok and compared == 0:
        status = "fonte_indisponivel"
    else:
        status = "ok"

    report = {
        "checked_at": datetime.now(SP).isoformat(),
        "source_a": "football-data.org",
        "source_b": "ESPN",
        "source_b_ok": source_ok,
        "status": status,
        "compared": compared,
        "agree": agree,
        "discrepancies": discrepancies,
        "espn_ahead": sorted(espn_ahead),
        "espn_behind": sorted(espn_behind),
        "unmapped": sorted(set(unmapped)),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Conferência 2 fontes · {agree}/{compared} batem · "
          f"ESPN à frente: {len(espn_ahead)} · status: {status}")
    for d in discrepancies:
        print(f"  ⛔ DIVERGÊNCIA {d['match_id']} {d['teams']}: {d['oficial']} ≠ {d['espn']}"
              + ("  [lock manual ativo]" if d["lock"] else ""))
    if report["unmapped"]:
        print(f"  (nomes não mapeados, ignorados: {report['unmapped']})")
    # nunca derruba o pipeline — o alerta é um passo separado do workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
