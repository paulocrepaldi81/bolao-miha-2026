"""
Orquestra o motor: lê planilhas → pontua → monta classificação → gera data.json.

Uso:
  cd engine
  python3 build_data.py --bets ./bets --out ../landing-page/data.json

Arquivos de apoio (pasta engine/data):
  results.csv   resultados oficiais dos jogos (você preenche a cada rodada)
  facts.json    fatos das categorias extras + campeão/vice/3º reais (no fim)
  roster.csv    alias, pago (sim/não), ordem de envio (desempate)
  history.json  snapshots automáticos p/ movimentação (gerado pelo motor)
"""
import argparse, csv, glob, json, os, re
from collections import Counter
from datetime import datetime, timezone, timedelta

import config as C
from catalog import build_group_catalog
from read_bets import read_bet
from scoring import score_bet
import leaderboard as LB

SP = timezone(timedelta(hours=-3))   # America/Sao_Paulo (GMT-3)

# Pódios das edições anteriores (Hall da Fama) — dados confirmados pelo organizador
HALL_DA_FAMA = [
    {"year": 2022, "host": "Catar",         "flag": "🇶🇦", "podium": ["Alexandre Tauszig", "Charles Miller", "Guilherme Marcondes"]},
    {"year": 2018, "host": "Rússia",        "flag": "🇷🇺", "podium": ["Fabio Terzian", "Pedro Marcondes", "Ricardo Kerr"]},
    {"year": 2014, "host": "Brasil",        "flag": "🇧🇷", "podium": ["Paulo Crepaldi", "Ricardo Mihalik", "Fernando Mihalik"]},
    {"year": 2010, "host": "África do Sul", "flag": "🇿🇦", "podium": ["Marina Mihalik", "Rodrigo Duarte", "Luis Luengo"]},
    {"year": 2006, "host": "Alemanha",      "flag": "🇩🇪", "podium": ["Kat Lencina", "Pedro Mitev", "Flávia Mihalik"]},
]
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MONTHS = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
          "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12}


def parse_kickoff(text, year=2026):
    """'11/jun 16h' / '21h30' / '0h'  ->  ISO com fuso de São Paulo."""
    if not text:
        return None
    m = re.match(r"\s*(\d{1,2})/(\w{3})\s+(\d{1,2})h(\d{0,2})", str(text).strip(), re.I)
    if not m:
        return None
    d, mon, hh, mm = int(m.group(1)), m.group(2).lower(), int(m.group(3)), m.group(4)
    mm = int(mm) if mm else 0
    if mon not in MONTHS:
        return None
    return datetime(year, MONTHS[mon], d, hh, mm, tzinfo=SP).isoformat()


def load_results(path):
    res = {}
    if not os.path.exists(path):
        return res
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = (row.get("match_id") or "").strip()
            if not mid:
                continue
            hs, as_ = row.get("home_score", ""), row.get("away_score", "")
            res[mid] = {
                "home_score": int(hs) if str(hs).strip() != "" else None,
                "away_score": int(as_) if str(as_).strip() != "" else None,
                "status": (row.get("status") or "scheduled").strip() or "scheduled",
                "verified": str(row.get("verified", "")).strip().lower() in ("1", "true", "sim", "yes"),
            }
    return res


def load_facts(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        real_final = {k: d.get(k) for k in ("champion", "vice", "third")}
        return real_final, d
    return {"champion": None, "vice": None, "third": None}, {}


def load_roster(path):
    roster = {}
    if not os.path.exists(path):
        return roster
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            alias = (row.get("alias") or "").strip()
            if not alias:
                continue
            paid = str(row.get("paid", "")).strip().lower() in ("1", "true", "sim", "yes", "pago")
            order = row.get("order")
            roster[alias.lower()] = {"paid": paid, "order": int(order) if order else i}
    return roster


def load_history(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def load_cross_check(path):
    """Resumo da conferência independente (ESPN) p/ o bloco 'Auditoria' do site."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        return None
    return {
        "status": c.get("status", "ok"),
        "source_a": c.get("source_a"), "source_b": c.get("source_b"),
        "source_b_ok": c.get("source_b_ok", True),
        "compared": c.get("compared", 0), "agree": c.get("agree", 0),
        "discrepancies": c.get("discrepancies", []),
        "checked_at": c.get("checked_at"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bets", default="./bets", help="pasta com as planilhas preenchidas")
    ap.add_argument("--template", default=None, help="planilha-modelo (catálogo)")
    ap.add_argument("--out", default="../landing-page/data.json")
    ap.add_argument("--placeholder", action="store_true", help="marca is_placeholder=true")
    ap.add_argument("--from-json", action="store_true",
                    help="lê apostas de data/bets_extracted.json (p/ o robô, sem .xlsx)")
    args = ap.parse_args()

    from catalog import get_catalog
    catalog = get_catalog(args.template)   # usa data/catalog.json se não houver planilha (CI)
    results = load_results(os.path.join(DATA, "results.csv"))
    real_final, facts = load_facts(os.path.join(DATA, "facts.json"))
    roster = load_roster(os.path.join(DATA, "roster.csv"))
    history = load_history(os.path.join(DATA, "history.json"))
    audit = load_cross_check(os.path.join(DATA, "cross_check.json"))

    bets, scored, all_issues = [], [], []
    bets_json = os.path.join(DATA, "bets_extracted.json")
    if args.from_json and os.path.exists(bets_json):
        with open(bets_json, encoding="utf-8") as f:
            raw = json.load(f)["bets"]
        for bet in raw:   # JSON converte tuplas em listas — normaliza de volta
            bet["group_preds"] = {k: tuple(v) for k, v in bet["group_preds"].items()}
            bets.append(bet)
    else:
        bet_files = sorted(glob.glob(os.path.join(args.bets, "*.xlsx")))
        bet_files = [f for f in bet_files if "~$" not in os.path.basename(f)]
        for path in bet_files:
            bets.append(read_bet(path, catalog))

    for bet in bets:
        scored.append(score_bet(bet, results, catalog, real_final, facts))
        if bet["issues"]:
            all_issues.append((bet["alias"], bet["file"], bet["issues"]))

    # Baseline da MOVIMENTAÇÃO = a classificação mais recente que era DIFERENTE da atual.
    # Assim o "▲/▼ da rodada" reflete a última mudança real de pontos e continua aparecendo
    # mesmo nas execuções em que nada mudou (o robô roda de minutos em minutos).
    cur_tot = {s["alias"]: s["total"] for s in scored}
    def _totals(snap):
        return {a: v.get("total") for a, v in snap.get("ranks", {}).items()}
    prev_snapshot = {}
    for snap in reversed(history):
        if _totals(snap) != cur_tot:
            prev_snapshot = snap["ranks"]
            break

    participants = LB.build(scored, roster, catalog, results, real_final, facts, prev_snapshot)

    # ---- matches p/ a Central de Jogos ----
    matches = []
    for m in catalog:
        r = results.get(m["match_id"], {})
        matches.append({
            "match_id": m["match_id"],
            "group": m["group"], "home_team": m["home"], "away_team": m["away"], "venue": "",
            "kickoff_sao_paulo": parse_kickoff(m["date"]),
            "status": r.get("status", "scheduled"),
            "home_score": r.get("home_score"), "away_score": r.get("away_score"),
            "verified": r.get("verified", False), "is_special": m["special"],
        })

    # ---- palpites individuais por aposta (alimenta a aba "Minha Aposta") ----
    bet_by_alias = {b["alias"]: b for b in bets}
    scored_by_alias = {s["alias"]: s for s in scored}
    for p in participants:
        b = bet_by_alias.get(p["alias"]); s = scored_by_alias.get(p["alias"])
        if not b:
            continue
        groups = {}
        for mid, (ph, pa) in b["group_preds"].items():
            groups[mid] = [ph, pa, (s["by_match"].get(mid, 0) if s else 0)]
        p["picks"] = {"groups": groups, "final": b["final"], "extras": b["extras"]}

    # ---- estatísticas reais ----
    stats = build_stats(bets, scored, history)
    movement = build_movement(participants)

    paid_n = sum(1 for p in participants if p["paid"])
    now = datetime.now(SP).isoformat()
    data = {
        "meta": {
            "pool_name": "Bolão Miha 2026", "timezone": "America/Sao_Paulo",
            "is_placeholder": bool(args.placeholder), "bet_value": C.BET_VALUE,
            "total_bets": len(participants), "paid_bets": paid_n, "paid_pending": True,
            "last_data_update": now, "last_source_check": now,
            "rule_version": "v2.1", "freshness": "ok",
        },
        "latest_result": build_latest(catalog, results),
        "audit": audit,
        "final_result": real_final,
        "extras_summary": build_extras_summary(bets, facts),
        "participants": participants,
        "matches": matches,
        "movement": movement,
        "stats": stats,
        "probability": {"method": "Modelo simples: pontos máximos possíveis e 'matematicamente vivo'. "
                                  "Sem simulação de força de seleção no lançamento.", "simulations": 0},
        "history_note": "Hall da Fama vem do data.json (campo 'history').",
    }
    # Hall da Fama: preserva o existente; senão usa o histórico oficial embutido
    data["history"] = HALL_DA_FAMA
    if os.path.exists(args.out):
        try:
            with open(args.out, encoding="utf-8") as f:
                prev = json.load(f).get("history")
            if prev:
                data["history"] = prev
        except Exception:
            pass

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        # compacto (sem indent) — 88 apostas × palpites; economiza dados no mobile
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # ---- snapshot p/ movimentação: só grava quando a classificação MUDA ----
    # (evita inflar o histórico e mantém estável o baseline da "rodada" entre execuções iguais)
    if not history or _totals(history[-1]) != cur_tot:
        history.append({"ts": now, "ranks": {p["alias"]: {"rank": p["rank"], "total": p["score"]}
                                             for p in participants}})
        with open(os.path.join(DATA, "history.json"), "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    # ---- referência de jogos + relatório de validação ----
    with open(os.path.join(DATA, "matches_reference.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["match_id", "group", "home", "away", "date", "especial"])
        for m in catalog:
            w.writerow([m["match_id"], m["group"], m["home"], m["away"], m["date"], "sim" if m["special"] else ""])
    write_validation(os.path.join(DATA, "validation_report.txt"), participants, roster, all_issues)

    print(f"OK · {len(participants)} apostas · {paid_n} pagas · {sum(1 for r in results.values() if r['home_score'] is not None)} jogos com resultado")
    print(f"  → {args.out}")
    if all_issues:
        print(f"  ⚠ {len(all_issues)} planilha(s) com avisos — veja data/validation_report.txt")


EXTRA_LABELS = [
    ("artilheiro_nome",      "⚽ Artilheiro — nome",            C.PTS_ART_NOME),
    ("artilheiro_equipe",    "👕 Artilheiro — equipe",          C.PTS_ART_EQUIPE),
    ("artilheiro_gols",      "🔢 Artilheiro — nº de gols",      C.PTS_ART_GOLS),
    ("mais_goleadora",       "🎯 Equipe mais goleadora",        C.PTS_CURIOSIDADE),
    ("menos_vazada",         "🧤 Equipe menos vazada",          C.PTS_CURIOSIDADE),
    ("mais_gols_jogo",       "🔥 Maior nº de gols em um jogo",  C.PTS_CURIOSIDADE),
    ("empates_1f",           "🤝 Nº de empates na 1ª fase",     C.PTS_CURIOSIDADE),
    ("jogos_penaltis",       "🥅 Jogos decididos nos pênaltis", C.PTS_CURIOSIDADE),
    ("equipe_1o_expulso",    "🟥 Equipe do 1º expulso",         C.PTS_CURIOSIDADE),
    ("equipe_1o_gol_contra", "😅 Equipe do 1º gol contra",      C.PTS_CURIOSIDADE),
    ("azarao",               "🦓 Azarão da Copa",               C.PTS_CURIOSIDADE),
]


def build_extras_summary(bets, facts):
    """Para cada categoria extra: valor real (se definido), quem pontuou e parcial ao vivo."""
    from scoring import _match_fact
    live_path = os.path.join(DATA, "facts_live.json")
    partials = {}
    if os.path.exists(live_path):
        try:
            with open(live_path, encoding="utf-8") as f:
                partials = json.load(f).get("partials", {})
        except Exception:
            pass
    out = []
    for key, label, pts in EXTRA_LABELS:
        real = facts.get(key)
        winners = []
        if real not in (None, ""):
            winners = sorted(b["alias"] for b in bets
                             if _match_fact(b["extras"].get(key), real))
        out.append({"key": key, "label": label, "points": pts,
                    "real": real if real not in (None, "") else None,
                    "partial": partials.get(key) if real in (None, "") else None,
                    "winners": winners})
    return out


def build_latest(catalog, results):
    played = [(m, results[m["match_id"]]) for m in catalog
              if results.get(m["match_id"], {}).get("status") == "finished"
              and results.get(m["match_id"], {}).get("home_score") is not None]
    if not played:
        return None
    # o "último resultado" é o jogo encerrado mais RECENTE (por horário), não o último do catálogo
    played.sort(key=lambda x: parse_kickoff(x[0]["date"]) or "")
    m, r = played[-1]
    return {"home_team": m["home"], "away_team": m["away"],
            "home_score": r["home_score"], "away_score": r["away_score"],
            "note": "Resultado oficial computado."}


def build_movement(parts):
    if not parts:
        return {"biggest_jump": None, "biggest_drop": None, "longest_first": "—",
                "pain_of_round": "A bola ainda não rolou."}
    jump = max(parts, key=lambda p: p["rank_change"])
    drop = min(parts, key=lambda p: p["rank_change"])
    return {
        "biggest_jump": {"alias": jump["alias"], "delta": jump["rank_change"]} if jump["rank_change"] > 0 else None,
        "biggest_drop": {"alias": drop["alias"], "delta": drop["rank_change"]} if drop["rank_change"] < 0 else None,
        "longest_first": f"{parts[0]['alias']} — na ponta agora",
        "pain_of_round": (f"{drop['alias']} caiu {abs(drop['rank_change'])} posições."
                          if drop["rank_change"] < 0 else "Rodada tranquila — ninguém despencou."),
    }


def build_stats(bets, scored, history):
    if not scored:
        return {"best_exact": None, "optimistic": None, "cursed": None,
                "elimination": "—", "longest_first": None, "fav_score": "2 × 1"}
    best = max(scored, key=lambda s: s["exact_scores"])
    # mais otimista = maior média de gols nos palpites
    def avg_goals(b):
        gs = [h + a for (h, a) in b["group_preds"].values()]
        return sum(gs) / len(gs) if gs else 0
    opt = max(bets, key=avg_goals) if bets else None
    cursed = min(scored, key=lambda s: (s["correct_outcomes"], s["total"]))
    counter = Counter()
    for b in bets:
        for (h, a) in b["group_preds"].values():
            counter[f"{h} × {a}"] += 1
    fav = counter.most_common(1)[0][0] if counter else "2 × 1"
    # mais tempo em 1º = quem mais apareceu como rank 1 nos snapshots
    first_counts = Counter(s["ranks"] and next((a for a, v in s["ranks"].items() if v["rank"] == 1), None)
                           for s in history)
    longest = first_counts.most_common(1)[0][0] if first_counts and first_counts.most_common(1)[0][0] else None
    return {
        "best_exact": {"alias": best["alias"], "val": f"{best['exact_scores']} placares exatos"} if best["exact_scores"] else None,
        "optimistic": {"alias": opt["alias"], "val": f"média {avg_goals(opt):.1f} gols/palpite"} if opt else None,
        "cursed": {"alias": cursed["alias"], "val": f"{cursed['correct_outcomes']} acertos de vencedor"},
        "elimination": "ninguém eliminado (fase de grupos)",
        "longest_first": {"alias": longest, "val": "mais rodadas em 1º"} if longest else None,
        "fav_score": fav,
    }


def write_validation(path, participants, roster, issues):
    lines = ["RELATÓRIO DE VALIDAÇÃO — Bolão Miha 2026", "=" * 44, ""]
    lines.append(f"Apostas lidas: {len(participants)} | no roster: {len(roster)}")
    in_roster = {p["alias"].lower() for p in participants}
    missing = [a for a in roster if a not in in_roster]
    no_roster = [p["alias"] for p in participants if p["alias"].lower() not in roster]
    if no_roster:
        lines.append(f"\n⚠ Apostas SEM entrada no roster (tratadas como café-com-leite): {', '.join(no_roster)}")
    if missing:
        lines.append(f"\n⚠ No roster mas SEM planilha recebida: {', '.join(missing)}")
    if issues:
        lines.append("\nProblemas por planilha:")
        for alias, file, iss in issues:
            lines.append(f"\n  • {alias} ({file}) — {len(iss)} aviso(s):")
            for x in iss[:12]:
                lines.append(f"      - {x}")
            if len(iss) > 12:
                lines.append(f"      … e mais {len(iss) - 12}")
    else:
        lines.append("\n✓ Nenhum problema de leitura.")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
