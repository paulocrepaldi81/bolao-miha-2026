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
from scoring import score_bet, score_knockout
import knockout as KO
import leaderboard as LB

SP = timezone(timedelta(hours=-3))   # America/Sao_Paulo (GMT-3)

# Pódios das edições anteriores (Hall da Fama) — dados confirmados pelo organizador
HALL_DA_FAMA = [
    {"year": 2022, "host": "Catar",         "flag": "🇶🇦", "podium": ["Alexandre Tauszig", "Charles Miller", "Guilherme Marcondes"]},
    {"year": 2018, "host": "Rússia",        "flag": "🇷🇺", "podium": ["Fabio Terzian", "Pedro Marcondes", "Ricardo Kerr"]},
    {"year": 2014, "host": "Brasil",        "flag": "🇧🇷", "podium": ["Paulo Crepaldi", "Ricardo Mihalik", "Fernando Mihalik"]},
    {"year": 2010, "host": "África do Sul", "flag": "🇿🇦", "podium": ["Marina Mihalik", "Rodrigo Duarte", "Luis Luengo"]},
    {"year": 2006, "host": "Alemanha",      "flag": "🇩🇪", "podium": ["Kat Lencina", "Pedro Mitev", "Flávia Mihalik"]},
    {"year": 2002, "host": "Coreia/Japão",  "flag": "🇰🇷🇯🇵", "podium": ["Rafael Liberman", "Wagner Jacot", "Roberto Mihalik"]},
]
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
HISTORY_MAX = 250   # máx. de snapshots guardados em history.json (baseline usa só os recentes)
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


def espn_kickoff_sp(iso):
    """ISO UTC da ESPN (ex.: '2026-06-17T20:00Z') -> ISO no fuso de São Paulo."""
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(SP).isoformat()
    except Exception:
        return None


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


def load_knockout_results(path):
    """knockout_results.csv: slot,home_score,away_score,status,special (orientação do CHAVEAMENTO,
    placar do tempo normal+prorrogação — pênaltis não entram). Ausente → {} (sem mata-mata ainda)."""
    res = {}
    if not os.path.exists(path):
        return res
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            slot = (row.get("slot") or "").strip()
            if not slot:
                continue
            hs, as_ = row.get("home_score", ""), row.get("away_score", "")
            res[slot] = {
                "home_score": int(hs) if str(hs).strip() != "" else None,
                "away_score": int(as_) if str(as_).strip() != "" else None,
                "status": (row.get("status") or "scheduled").strip() or "scheduled",
                "special": str(row.get("special", "")).strip().lower() in ("1", "true", "sim", "yes"),
            }
    return res


def _read_form_source(src):
    """Lê o CSV do Form: URL (Drive/Sheets publicado) ou arquivo local. FALHA-FECHADA: qualquer
    erro retorna None → aquela rodada é ignorada e vale o fallback (nunca derruba o pipeline)."""
    try:
        if str(src).startswith("http"):
            import urllib.request
            with urllib.request.urlopen(src, timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"  ⚠ fonte do form indisponível ({src}): {e}")
    return None


def load_knockout_form(path, roster_aliases):
    """knockout_forms.json: {"rounds":[{"round":"R32","deadline":"YYYY-MM-DD HH:MM","csv":"<url|arquivo>"}]}.
    Mescla os palpites de todas as rodadas por apelido (trava por prazo + vale o último, no módulo
    knockout). Falha-fechada por rodada. Retorna {alias: {slot: (h,a)}}."""
    merged = {}
    if not os.path.exists(path):
        return merged
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception:
        return merged
    for rd in cfg.get("rounds", []):
        rid, src, dl = rd.get("round"), rd.get("csv"), rd.get("deadline")
        if not (rid and src and dl):
            continue
        try:
            deadline = datetime.strptime(dl, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        # prazo POR JOGO (opcional): {slot: "YYYY-MM-DD HH:MM"} — ex.: travar o jogo de hoje mais cedo.
        slot_deadlines = {}
        for slot, sdl in (rd.get("slot_deadlines") or {}).items():
            try:
                slot_deadlines[slot] = datetime.strptime(sdl, "%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                continue
        text = _read_form_source(src)
        if text is None:
            continue
        try:
            picks = KO.parse_form_csv(text, rid, deadline, roster_aliases, slot_deadlines)
        except Exception as e:
            print(f"  ⚠ CSV do form {rid} ilegível: {e}")
            continue
        for alias, sl in picks.items():
            merged.setdefault(alias, {}).update(sl)
    return merged


def _divergence_persisted(c, persist=3):
    """True se a MESMA divergência já apareceu em >= `persist` checagens seguidas. Lê o `streak`
    que o passo 'Avaliar divergência' grava em alert_state.json (o mesmo que o e-mail usa) — assim
    banner e e-mail disparam JUNTOS. build_data roda ANTES desse passo, então o streak lido é o do
    run ANTERIOR; por isso o +1 (este run). NÃO escreve nada aqui (sem corrida com o passo)."""
    sig = json.dumps(sorted((d.get("match_id"), d.get("primaria"), d.get("secundaria"))
                            for d in c.get("discrepancias", c.get("discrepancies", []))), ensure_ascii=False)
    try:
        st = json.load(open(os.path.join(DATA, "alert_state.json"), encoding="utf-8"))
    except Exception:
        st = {}
    return sig != "" and sig == st.get("last_sig", "") and st.get("streak", 0) + 1 >= persist


def load_cross_check(path):
    """Resumo da conferência independente (ESPN) p/ o bloco 'Auditoria' do site.
    DEBOUNCE DO BANNER: uma divergência só "acende" o banner vermelho depois de PERSISTIR algumas
    checagens (igual ao e-mail) — glitch transitório da 2ª fonte, que se acerta sozinho em minutos,
    nem aparece (fica "ok"/verde). Divergência REAL persiste e aí sim aparece."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        return None
    status = c.get("status", "ok")
    discrepancies = c.get("discrepancies", [])
    if status == "divergencia" and not _divergence_persisted(c):
        status, discrepancies = "ok", []   # ainda não persistiu → não acende o banner
    return {
        "status": status,
        "source_a": c.get("source_a"), "source_b": c.get("source_b"),
        "source_b_ok": c.get("source_b_ok", True),
        "compared": c.get("compared", 0), "agree": c.get("agree", 0),
        "discrepancies": discrepancies,
        "resolvidas": c.get("resolvidas", []),   # divergências decididas a favor da ESPN
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
    # Agenda REAL (data + mando) da ESPN por match_id — usada SÓ p/ EXIBIÇÃO (datas/mando/
    # orientação do palpite). A PONTUAÇÃO não lê isto: casa pelo par de times da planilha.
    real_fix = {}
    _fp = os.path.join(DATA, "fixtures_real.json")
    if os.path.exists(_fp):
        try:
            with open(_fp, encoding="utf-8") as f:
                real_fix = json.load(f)
        except Exception:
            real_fix = {}

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

    # ---- MATA-MATA (v2): soma os pontos do chaveamento ao total ----
    # Placar EFETIVO por slot = override do Google Form (dentro do prazo) ou a aposta ORIGINAL.
    # Inerte enquanto não há resultados de mata-mata (ko_results vazio → 0 pra todos → 0-diff).
    # Falha-fechada: CSV do form indisponível/quebrado → ninguém recebe override → vale o original.
    ko_results = load_knockout_results(os.path.join(DATA, "knockout_results.csv"))
    ko_form = load_knockout_form(os.path.join(DATA, "knockout_forms.json"), [s["alias"] for s in scored])
    ko_fix = {}
    try:
        with open(os.path.join(DATA, "knockout_fixtures.json"), encoding="utf-8") as f:
            ko_fix = json.load(f)
    except Exception:
        ko_fix = {}
    bet_by_alias = {b["alias"]: b for b in bets}
    for s in scored:
        b = bet_by_alias.get(s["alias"], {})
        eff = KO.effective_picks(b.get("knockout_orig", {}), ko_form.get(s["alias"], {}))
        ko_pts, ko_by, ko_exact = score_knockout(eff, ko_results)
        s["knockout_pts"] = ko_pts
        s["knockout_by"] = ko_by
        s["total"] += ko_pts
        s["exact_scores"] += ko_exact     # placares exatos do mata-mata entram no contador
        s["correct_outcomes"] += sum(1 for v in ko_by.values() if v > 0)   # acertos de resultado do KO
        s["by_match"].update(ko_by)       # e os pontos do KO entram em "pontos na rodada" (day_points)

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

    # ---- RODADA (janela 05:00 → 04:59 SP do dia seguinte) ----
    # Cada jogo pertence à rodada da data de (kickoff_SP − 5h): assim um jogo de madrugada
    # (ex.: 2h) ainda conta na rodada do dia anterior, e a rodada nova só começa às 5h.
    # "Rodada corrente" = a rodada mais recente que JÁ tem jogo encerrado (sticky: entre
    # rodadas segue mostrando a última com jogos; zera só quando o 1º jogo da nova encerra).
    # 'now' não entra aqui de propósito — o sticky depende só de quais jogos já terminaram.
    def _rodada_date(iso_sp):
        return (datetime.fromisoformat(iso_sp) - timedelta(hours=5)).date().isoformat()
    kickoff_by_mid = {}
    for m in catalog:
        k = espn_kickoff_sp((real_fix.get(m["match_id"]) or {}).get("kickoff")) or parse_kickoff(m["date"])
        if k:
            kickoff_by_mid[m["match_id"]] = k
    finished_round = {mid: _rodada_date(k) for mid, k in kickoff_by_mid.items()
                      if results.get(mid, {}).get("status") == "finished"
                      and results.get(mid, {}).get("home_score") is not None}
    # o MATA-MATA também conta na rodada: cada slot ENCERRADO entra pela data do seu kickoff (SP)
    for slot, fx in ko_fix.items():
        k = espn_kickoff_sp(fx.get("kickoff"))
        rr = ko_results.get(slot, {})
        if k and rr.get("status") == "finished" and rr.get("home_score") is not None:
            finished_round[slot] = _rodada_date(k)
    cur_round = max(finished_round.values()) if finished_round else None
    round_mids = frozenset(mid for mid, d in finished_round.items() if d == cur_round)

    participants = LB.build(scored, roster, catalog, results, real_final, facts, prev_snapshot, round_mids)

    # ---- matches p/ a Central de Jogos ----
    matches = []
    for m in catalog:
        r = results.get(m["match_id"], {})
        rf = real_fix.get(m["match_id"]) or {}
        # ESPN manda na AGENDA (data + mando); a planilha manda no confronto. Exibe o mando/data
        # reais da ESPN quando houver — corrige erro de agenda da planilha (ex.: Grupo L).
        home = rf.get("home") or m["home"]
        away = rf.get("away") or m["away"]
        hs, as_ = r.get("home_score"), r.get("away_score")
        # o results.csv guarda o PLACAR na orientação da PLANILHA; se o mando inverteu vs a
        # planilha, troca o placar JUNTO com os times (senão o placar sai do lado errado).
        if rf.get("home") and rf["home"] != m["home"]:
            hs, as_ = as_, hs
        matches.append({
            "match_id": m["match_id"],
            "group": m["group"], "home_team": home, "away_team": away, "venue": "",
            "kickoff_sao_paulo": espn_kickoff_sp(rf.get("kickoff")) or parse_kickoff(m["date"]),
            "status": r.get("status", "scheduled"),
            "home_score": hs, "away_score": as_,
            "verified": r.get("verified", False), "is_special": m["special"],
        })

    # ---- jogos do MATA-MATA na Central de Jogos (ADITIVO: reusa todo o front da fase 1) ----
    # Só entram slots com os DOIS times reais já definidos (R32 agora; R16+ quando classificarem).
    # Campos extra (phase/slot/winner/decided_by/pen_*) são ignorados pelo front atual — não quebram.
    PHASE_LABEL = {"R32": "16 avos", "R16": "Oitavas", "QF": "Quartas",
                   "SF": "Semifinal", "FIN": "Final", "TER": "3º lugar"}
    for slot, fx in ko_fix.items():
        home, away = fx.get("home"), fx.get("away")
        if not (home and away):
            continue
        rr = ko_results.get(slot, {})
        phase = slot.split("-")[0]
        matches.append({
            "match_id": slot,
            "group": PHASE_LABEL.get(phase, phase),
            "home_team": home, "away_team": away, "venue": "",
            "kickoff_sao_paulo": espn_kickoff_sp(fx.get("kickoff")) or fx.get("kickoff"),
            "status": rr.get("status") or fx.get("status") or "scheduled",
            "home_score": rr.get("home_score"), "away_score": rr.get("away_score"),
            "verified": rr.get("status") == "finished", "is_special": bool(rr.get("special")),
            "phase": phase, "slot": slot, "winner": fx.get("winner"),
            "decided_by": fx.get("decided_by"), "pen_home": fx.get("pen_home"), "pen_away": fx.get("pen_away"),
        })

    # ---- palpites individuais por aposta (alimenta a aba "Minha Aposta") ----
    bet_by_alias = {b["alias"]: b for b in bets}
    scored_by_alias = {s["alias"]: s for s in scored}
    cat_home = {m["match_id"]: m["home"] for m in catalog}   # mando da planilha por jogo
    for p in participants:
        b = bet_by_alias.get(p["alias"]); s = scored_by_alias.get(p["alias"])
        if not b:
            continue
        groups = {}
        for mid, (ph, pa) in b["group_preds"].items():
            pts = (s["by_match"].get(mid, 0) if s else 0)
            rf = real_fix.get(mid) or {}
            # se a ESPN inverteu o mando vs a planilha, troca [casa,fora] só p/ EXIBIR o palpite
            # alinhado ao confronto mostrado. Os PONTOS (pts) não mudam (são por jogo).
            if rf.get("home") and cat_home.get(mid) and rf["home"] != cat_home[mid]:
                groups[mid] = [pa, ph, pts]
            else:
                groups[mid] = [ph, pa, pts]
        # palpites do MATA-MATA por slot: o que VALEU (override do Form ou original) + pontos
        ko_orig = b.get("knockout_orig", {})
        form_a = ko_form.get(p["alias"], {})
        eff = KO.effective_picks(ko_orig, form_a)
        ko_by = (s.get("knockout_by", {}) if s else {})
        knockout = {}
        for slot, (h, a) in eff.items():
            o = ko_orig.get(slot)
            knockout[slot] = {"orig": list(o) if o else [h, a], "used": [h, a],
                              "changed": slot in form_a, "pts": ko_by.get(slot)}
        p["picks"] = {"groups": groups, "final": b["final"], "extras": b["extras"], "knockout": knockout}

    # ---- estatísticas reais ----
    stats = build_stats(bets, scored, history)
    movement = build_movement(participants)

    paid_n = sum(1 for p in participants if p["paid"])
    now = datetime.now(SP).isoformat()
    # link do Form da FASE ATUAL do mata-mata (p/ o botão "Atualizar meus palpites" na landing).
    # Vem do 'form_url' da ÚLTIMA rodada do knockout_forms.json — MAS só se o PRAZO dela ainda não
    # passou. Senão o botão apontaria pro Form de uma fase JÁ ENCERRADA (ex.: o R32 durante as
    # oitavas, enquanto a rodada R16 não é cadastrada). Prazo vencido → botão SOME (melhor que
    # mandar pro formulário errado).
    ko_form_url = None
    try:
        _rounds = (json.load(open(os.path.join(DATA, "knockout_forms.json"), encoding="utf-8")).get("rounds") or [])
        if _rounds:
            _last = _rounds[-1]
            _aberta = True
            if _last.get("deadline"):
                try:
                    _aberta = datetime.strptime(_last["deadline"], "%Y-%m-%d %H:%M") > datetime.now(SP).replace(tzinfo=None)
                except Exception:
                    _aberta = True
            ko_form_url = _last.get("form_url") if _aberta else None
    except Exception:
        ko_form_url = None
    data = {
        "meta": {
            "pool_name": "Bolão Miha 2026", "timezone": "America/Sao_Paulo",
            "is_placeholder": bool(args.placeholder), "bet_value": C.BET_VALUE,
            "total_bets": len(participants), "paid_bets": paid_n, "paid_pending": True,
            "last_data_update": now, "last_source_check": now,
            "rule_version": "v2.1", "freshness": "ok",
        },
        "latest_result": build_latest(matches),
        "audit": audit,
        "final_result": real_final,
        "extras_summary": build_extras_summary(bets, facts),
        "participants": participants,
        "matches": matches,
        "knockout_form_url": ko_form_url,
        "movement": movement,
        "stats": stats,
        "probability": {"method": "Modelo simples: pontos máximos possíveis e 'matematicamente vivo'. "
                                  "Sem simulação de força de seleção no lançamento.", "simulations": 0},
        "history_note": "Hall da Fama vem do data.json (campo 'history').",
    }
    # Hall da Fama: HALL_DA_FAMA é a FONTE ÚNICA (constante versionada). Para editar o
    # Hall da Fama, basta mudar HALL_DA_FAMA acima — o robô republica sozinho.
    data["history"] = HALL_DA_FAMA

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        # compacto (sem indent) — 88 apostas × palpites; economiza dados no mobile
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    # ---- snapshot p/ movimentação: só grava quando a classificação MUDA ----
    # (evita inflar o histórico e mantém estável o baseline da "rodada" entre execuções iguais)
    if not history or _totals(history[-1]) != cur_tot:
        history.append({"ts": now, "ranks": {p["alias"]: {"rank": p["rank"], "total": p["score"]}
                                             for p in participants}})
        # cap defensivo: o baseline da movimentação só usa o snapshot recente, então manter os
        # últimos N basta — limita o tamanho do arquivo/commit ao longo de toda a Copa.
        history = history[-HISTORY_MAX:]
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
            # _match_fact é lista-aware: empate (real = lista) → quem cravou qualquer um pontua.
            winners = sorted(b["alias"] for b in bets
                             if _match_fact(b["extras"].get(key), real))
        # exibição do "real": empate vira "Empate: A, B, C"
        if isinstance(real, (list, tuple, set)):
            rl = [str(x) for x in real]
            real_disp = rl[0] if len(rl) == 1 else "Empate: " + ", ".join(rl)
        else:
            real_disp = real if real not in (None, "") else None
        out.append({"key": key, "label": label, "points": pts,
                    "real": real_disp,
                    "partial": partials.get(key) if real in (None, "") else None,
                    "winners": winners})
    return out


def build_latest(matches):
    # "último resultado" = o jogo ENCERRADO mais recente (por horário real), de GRUPO OU MATA-MATA.
    # Usa a lista `matches` (que já inclui os jogos do KO, com placar na orientação certa). ANTES
    # só olhava o catálogo de GRUPOS e ficava travado no último jogo de grupo durante o mata-mata.
    played = [m for m in matches
              if m.get("status") == "finished" and m.get("home_score") is not None]
    if not played:
        return None
    played.sort(key=lambda m: m.get("kickoff_sao_paulo") or "")
    m = played[-1]
    return {"home_team": m["home_team"], "away_team": m["away_team"],
            "home_score": m["home_score"], "away_score": m["away_score"],
            "note": "Resultado oficial computado."}


def build_movement(parts):
    if not parts:
        return {"biggest_jump": None, "biggest_drop": None, "longest_first": "—",
                "pain_of_round": "A bola ainda não rolou."}
    # superlativos com EMPATE EXPLÍCITO (holders = todos; nada de max/min escondendo gente).
    def holders_at(key, pick):
        vals = [p[key] for p in parts]
        v = max(vals) if pick == "max" else min(vals)
        return v, sorted(p["alias"] for p in parts if p[key] == v)
    # mais pontos NA RODADA (day_points) — o destaque do bloco
    pv, ph = holders_at("day_points", "max")
    round_points = {"value": pv, "holders": ph, "count": len(ph)} if pv > 0 else None
    # maior salto (subiu) e maior tombo (caiu): base = rank_change (desde a última mudança)
    jv, jh = holders_at("rank_change", "max")
    biggest_jump = {"value": jv, "holders": jh, "count": len(jh)} if jv > 0 else None
    dv, dh = holders_at("rank_change", "min")          # tombo: sempre mostra (decisão do dono), todos juntos
    biggest_drop = {"value": dv, "holders": dh, "count": len(dh)} if dv < 0 else None
    return {
        "round_points": round_points,
        "biggest_jump": biggest_jump,
        "biggest_drop": biggest_drop,
        "longest_first": f"{parts[0]['alias']} — na ponta agora",
        "pain_of_round": "",
    }


def build_stats(bets, scored, history):
    if not scored:
        return {"best_exact": None, "optimistic": None, "cursed": None,
                "elimination": "—", "longest_first": None, "fav_score": "2 × 1"}
    # superlativos com EMPATE EXPLÍCITO: holders = TODOS que alcançaram o valor (nada de
    # max()/min() escondendo co-líderes). O front trunca para exibir; o motor manda a lista cheia.
    n_part = len(scored)
    mx_exact = max(s["exact_scores"] for s in scored)
    exact_holders = sorted((s["alias"] for s in scored if s["exact_scores"] == mx_exact)) if mx_exact else []
    # pé-frio do BOLÃO = quem cravou MENOS placares exatos no torneio (mirror do "mais exatos";
    # métrica acumulada, por isso o rótulo é "do bolão", não "da rodada").
    mn_exact = min(s["exact_scores"] for s in scored)
    cursed_holders = sorted(s["alias"] for s in scored if s["exact_scores"] == mn_exact)
    # some SÓ no caso degenerado: mais da metade do bolão empatada no piso (sem outlier real)
    cursed_suppress = len(cursed_holders) > n_part / 2
    # mais otimista = maior média de gols nos palpites
    def avg_goals(b):
        gs = [h + a for (h, a) in b["group_preds"].values()]
        return sum(gs) / len(gs) if gs else 0
    opt = max(bets, key=avg_goals) if bets else None
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
        "best_exact": {"value": mx_exact, "unit": "placares exatos",
                       "holders": exact_holders, "count": len(exact_holders),
                       "alias": exact_holders[0], "val": f"{mx_exact} placares exatos"} if exact_holders else None,
        "optimistic": {"alias": opt["alias"], "val": f"média {avg_goals(opt):.1f} gols/palpite"} if opt else None,
        "cursed": ({"value": mn_exact, "unit": ("placar exato" if mn_exact == 1 else "placares exatos"),
                    "holders": cursed_holders, "count": len(cursed_holders),
                    "alias": cursed_holders[0], "val": f"{mn_exact} placares exatos"}
                   if not cursed_suppress else None),
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
