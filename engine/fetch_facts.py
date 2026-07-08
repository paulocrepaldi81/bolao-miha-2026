"""
Apura automaticamente as CATEGORIAS EXTRAS a partir dos resultados e da API.

Camadas:
  1. Derivado dos placares (results.csv): empates na 1ª fase, maior nº de gols num
     jogo, mais goleadora / menos vazada (parciais).
  2. football-data.org (FOOTBALL_DATA_TOKEN): artilharia (/scorers).
  3. ESPN (API JSON pública, sem chave): LANCES — 1º cartão vermelho e 1º gol contra,
     lidos do array de eventos (details[]) do placar. Uma única chamada por janela já
     traz os eventos de todos os jogos → detecção cronológica simples e confiável.
     (Substitui a API-Football, cujo plano grátis não cobre a temporada 2026.)

Saídas:
  - data/facts_live.json  → parciais "ao vivo" + memória da varredura
  - data/facts.json       → SÓ preenche campo ainda null quando o fato é DEFINITIVO:
      · equipe_1o_expulso / equipe_1o_gol_contra: 1ª ocorrência, com todos os jogos
        ANTERIORES já encerrados (garante a ordem cronológica)
      · empates_1f: quando os 72 jogos da fase de grupos encerrarem
    Valor não-null em facts.json NUNCA é alterado (o organizador manda).
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FACTS = os.path.join(DATA, "facts.json")
LIVE = os.path.join(DATA, "facts_live.json")
FD = "https://api.football-data.org/v4"
# ESPN: eventos vêm de fetch_results.load_espn_events() (cache compartilhado da rodada do robô).


def fd_get(path, token):
    req = urllib.request.Request(FD + path, headers={"X-Auth-Token": token})
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


def fetch_espn_events():
    """{match_id: {date, completed, events:[{kind,team,player,minute,order}]}} para todos os jogos."""
    from fetch_results import EN_PT, load_espn_events
    from catalog import get_catalog
    # TODO (mesma classe do bug corrigido em mais_goleadora/menos_vazada, 07/jul): `pairs` só
    # cobre os 72 jogos de grupo -> 1º expulso/1º gol contra de mata-mata nunca entrariam no
    # cálculo. INERTE hoje só porque os dois fatos já travaram em facts.json durante a fase de
    # grupos (antes de existir jogo de mata-mata) — se precisar recalcular do zero um dia, ou
    # numa próxima edição do bolão, precisa somar os confrontos de knockout_fixtures.json aqui.
    pairs = {frozenset((m["home"], m["away"])): m for m in get_catalog()}
    out = {}
    scorers = {}   # artilharia (ESPN, completa): {nome: {"goals": n, "team": pt}} acumulada
    for ev in load_espn_events():
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors", [])
        if len(cs) != 2:
            continue
        id2pt, names, ok = {}, [], True
        for c in cs:
            raw = (c.get("team", {}).get("displayName") or c.get("team", {}).get("name") or "")
            pt = EN_PT.get(raw.strip().lower())
            if not pt:
                ok = False
                break
            names.append(pt)
            id2pt[str(c.get("team", {}).get("id"))] = pt
        if not ok:
            continue
        t = ev.get("status", {}).get("type", {})
        state = t.get("state")
        # ARTILHARIA (ESPN = fonte completa): conta gols de QUALQUER jogo da Copa — grupo OU
        # MATA-MATA — sem depender do catálogo de grupos (era aqui o bug: o mata-mata caía no
        # 'continue' e os gols do KO nunca entravam). `scoringPlay` = gol de PARTIDA (pênalti no
        # tempo conta; disputa por pênaltis não tem scoringPlay); gol contra NÃO conta.
        for det in comp.get("details", []):
            if state in ("post", "in") and det.get("scoringPlay") and not det.get("ownGoal"):
                a0 = (det.get("athletesInvolved") or [{}])[0]
                gnm = a0.get("displayName") or a0.get("shortName")
                if gnm:
                    gtid = str((a0.get("team") or {}).get("id") or det.get("team", {}).get("id") or "")
                    rec = scorers.setdefault(gnm, {"goals": 0, "team": None})
                    rec["goals"] += 1
                    rec["team"] = rec["team"] or id2pt.get(gtid)
        # LANCES (1º expulso / 1º gol contra) dependem do catálogo p/ mapear o match_id:
        m = pairs.get(frozenset(names))
        if not m:
            continue
        events = []
        for det in comp.get("details", []):
            if not (det.get("redCard") or det.get("ownGoal")):
                continue
            ath = (det.get("athletesInvolved") or [{}])[0]
            # time que cometeu: o do JOGADOR (expulso / autor do gol contra)
            tid = str((ath.get("team") or {}).get("id") or det.get("team", {}).get("id") or "")
            events.append({
                "kind": "red" if det.get("redCard") else "own",
                "team": id2pt.get(tid),
                "player": ath.get("displayName") or ath.get("shortName") or "?",
                "minute": (det.get("clock", {}).get("displayValue") or "").replace("'", ""),
                "order": det.get("clock", {}).get("value") or 0,
            })
        out[m["match_id"]] = {"date": ev.get("date") or "", "completed": bool(t.get("completed")),
                              "events": events}
    return out, scorers


def compute_tournament_extras(all_finished):
    """Curiosidades de TORNEIO INTEIRO (grupo + mata-mata encerrado, sem pênaltis): maior nº de
    gols num jogo, equipe mais goleadora, equipe menos vazada — todas com EMPATE EXPLÍCITO (lista
    TODOS os empatados, nunca escolhe 1 arbitrariamente). Puro, sem I/O — recebe `all_finished` já
    montada: lista de (m, r) com m={"home","away"}, r={"home_score","away_score"}. Fail-safe:
    lista vazia -> {} (nenhuma chave setada, main() não sobrescreve com vazio)."""
    if not all_finished:
        return {}

    def _join(items, cap=6):
        return ", ".join(items[:cap]) + (f" +{len(items) - cap}" if len(items) > cap else "")

    gols_jogo = lambda r: int(r["home_score"]) + int(r["away_score"])
    mxg = max(gols_jogo(r) for _, r in all_finished)
    jogos_mxg = [f"{m['home']} {r['home_score']}×{r['away_score']} {m['away']}"
                 for m, r in all_finished if gols_jogo(r) == mxg]
    out = {"mais_gols_jogo": (f"{mxg} gols ({jogos_mxg[0]})" if len(jogos_mxg) == 1
                              else f"{mxg} gols — {len(jogos_mxg)} jogos: " + "; ".join(jogos_mxg[:4])
                                   + (f" +{len(jogos_mxg) - 4}" if len(jogos_mxg) > 4 else ""))}

    gp, gc = {}, {}
    for m, r in all_finished:
        h, a = int(r["home_score"]), int(r["away_score"])
        gp[m["home"]] = gp.get(m["home"], 0) + h
        gp[m["away"]] = gp.get(m["away"], 0) + a
        gc[m["home"]] = gc.get(m["home"], 0) + a
        gc[m["away"]] = gc.get(m["away"], 0) + h

    mxsco = max(gp.values())
    tops = sorted([t for t, g in gp.items() if g == mxsco])
    out["mais_goleadora"] = (f"{tops[0]} ({mxsco} gols)" if len(tops) == 1
                             else f"{len(tops)} seleções com {mxsco} gols: " + _join(tops))

    mnc = min(gc.values())
    least = sorted([t for t, c in gc.items() if c == mnc])
    if len(least) == 1:
        out["menos_vazada"] = f"{least[0]} ({mnc} sofrido(s))"
    elif mnc == 0:
        out["menos_vazada"] = f"{len(least)} seleções ainda sem sofrer gol: " + _join(least)
    else:
        out["menos_vazada"] = f"{len(least)} seleções com {mnc} sofrido(s): " + _join(least)
    return out


def compute_penalty_partial(ko_fix, total_slots):
    """Contagem parcial de jogos de MATA-MATA decididos nos pênaltis (conta o torneio inteiro —
    16avos até a Final/3º, mesma regra de torneio-inteiro de compute_tournament_extras; só fecha
    quando o organizador travar o valor definitivo em facts.json no fim da Copa). `ko_fix` =
    knockout_fixtures.json achatado {slot:{...,"decided_by","status"}}; `total_slots` = nº fixo de
    confrontos do chaveamento (32 = len(config.KNOCKOUT_CELLS): R32+R16+QF+SF+FIN+TER). Puro, sem
    I/O. Fail-safe: nenhum jogo de mata-mata encerrado ainda -> None."""
    finished = [v for v in ko_fix.values() if v.get("status") == "finished"]
    if not finished:
        return None
    pens = sum(1 for v in finished if v.get("decided_by") == "pen")
    return f"{pens} até agora ({len(finished)}/{total_slots} jogos de mata-mata encerrados)"


def main():
    from catalog import get_catalog
    from fetch_results import EN_PT, load_results
    from build_data import load_knockout_results   # reusa o loader do motor principal (sem pênaltis)
    import config as C

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    facts = load_json(FACTS, {})
    live = load_json(LIVE, {})
    partials = live.get("partials", {})
    catalog = get_catalog()
    results, _ = load_results()
    changed_facts = False

    # jogos de MATA-MATA já encerrados (placar até a prorrogação, sem pênaltis — ver
    # load_knockout_results) entram nas 3 curiosidades de TORNEIO INTEIRO abaixo (mais_gols_jogo/
    # mais_goleadora/menos_vazada). ACHADO REAL (07/jul): sem isso, o parcial ficava PARADO nos
    # 72 jogos de grupo mesmo com 24 jogos de mata-mata já encerrados — chegou a exibir um time
    # já eliminado ("México") como líder de "sem sofrer gol" depois dele já ter perdido de virada
    # no mata-mata. `m` aqui é só {"home","away"} (o bloco abaixo não usa mais nada de `m`).
    ko_results = load_knockout_results(os.path.join(DATA, "knockout_results.csv"))
    ko_fix = load_json(os.path.join(DATA, "knockout_fixtures.json"), {})

    # AVISO ALTO (não bloqueia): knockout_fixtures.json é reescrito por completo a cada rodada,
    # sem merge (diferente do CSV, que preserva slots ausentes na resposta da ESPN) — se um slot
    # já encerrado sumir numa falha passageira de nome, o parcial de jogos_penaltis regrediria em
    # silêncio. Compara contra o pico já visto (guardado em facts_live.json) e avisa se cair.
    ko_finished_now = sum(1 for v in ko_fix.values() if v.get("status") == "finished")
    ko_finished_peak = live.get("_ko_finished_peak", 0)
    if ko_finished_now < ko_finished_peak:
        print(f"  ⚠⚠ knockout_fixtures.json regrediu: {ko_finished_peak} jogo(s) de mata-mata "
              f"encerrado(s) no pico visto antes, {ko_finished_now} agora — possível falha de nome "
              f"da ESPN sumindo com um slot já resolvido. Parciais de mata-mata (jogos_penaltis "
              f"incluído) podem estar incompletos nesta rodada.")
    live["_ko_finished_peak"] = max(ko_finished_now, ko_finished_peak)

    pen_partial = compute_penalty_partial(ko_fix, len(C.KNOCKOUT_CELLS))
    if pen_partial:
        partials["jogos_penaltis"] = pen_partial

    ko_finished = []
    for slot, r in ko_results.items():
        if r.get("status") != "finished" or r.get("home_score") is None:
            continue
        fx = ko_fix.get(slot) or {}
        home, away = fx.get("home"), fx.get("away")
        if home and away:
            ko_finished.append(({"home": home, "away": away}, r))

    # ---------- 1) Derivados dos placares ----------
    finished = [(m, results[m["match_id"]]) for m in catalog
                if results.get(m["match_id"], {}).get("status") == "finished"
                and results[m["match_id"]].get("home_score") not in (None, "")]
    # empates_1f é EXPLICITAMENTE só da 1ª fase -> continua usando só "finished" (grupos).
    # As 3 curiosidades de torneio inteiro usam "all_finished" (grupos + mata-mata encerrado).
    # Sem risco de duplicata: as duas listas vêm de namespaces de id disjuntos por construção
    # (match_id de grupo tipo "A1" vs. slot de mata-mata tipo "R32-01" nunca colidem).
    all_finished = finished + ko_finished
    if finished:
        draws = sum(1 for _, r in finished if int(r["home_score"]) == int(r["away_score"]))
        partials["empates_1f"] = f"{draws} até agora ({len(finished)}/72 jogos da 1ª fase)"
        if len(finished) == len(catalog) and facts.get("empates_1f") is None:
            facts["empates_1f"] = draws
            changed_facts = True
            print(f"✔ DEFINIDO empates_1f = {draws} (72/72 jogos encerrados)")

    partials.update(compute_tournament_extras(all_finished))

    # GUARDRAIL (C4): mesmo com grupo+mata-mata combinados acima, NÃO cravamos mais_goleadora/
    # menos_vazada/mais_gols_jogo em facts.json — pela regra oficial elas só fecham de vez ao fim
    # da Copa (resolução manual do organizador). empates_1f é "1ª fase" e já foi cravado acima.
    if finished and len(finished) == len(catalog):
        pendentes = [k for k in ("mais_goleadora", "menos_vazada", "mais_gols_jogo",
                                 "jogos_penaltis", "azarao") if facts.get(k) in (None, "")]
        if pendentes:
            print("ℹ 1ª fase encerrada. Curiosidades de torneio inteiro/mata-mata pendentes de "
                  "resolução MANUAL ao fim da Copa (contam prorrogação): " + ", ".join(pendentes))

    # ---------- 2) Artilharia: calculada via ESPN logo após buscar os lances (seção 3). ----------

    # ---------- 3) Lances (1º expulso / 1º gol contra) via ESPN ----------
    try:
        espn, scorers_espn = fetch_espn_events()
    except Exception as e:
        espn, scorers_espn = {}, {}
        print(f"  ⚠ ESPN (lances) indisponível: {e}")

    # ---------- Artilharia (ESPN = completa, detecta empate na liderança) ----------
    if scorers_espn:
        mx = max(v["goals"] for v in scorers_espn.values())
        leaders = sorted([(n, v["team"]) for n, v in scorers_espn.items() if v["goals"] == mx],
                         key=lambda x: x[0])
        if len(leaders) == 1:
            nm, eq = leaders[0]
            partials["artilheiro_nome"] = f"{nm} ({eq or '?'}) — {mx} gol(s)"
            partials["artilheiro_equipe"] = eq or "?"
            partials["artilheiro_gols"] = f"{mx} (parcial)"
        else:
            nomes = ", ".join(f"{n} ({eq or '?'})" for n, eq in leaders[:5])
            extra = f" +{len(leaders) - 5}" if len(leaders) > 5 else ""
            eqs = sorted({eq for _, eq in leaders if eq})
            partials["artilheiro_nome"] = f"Empatados em 1º: {len(leaders)} com {mx} gols — {nomes}{extra}"
            # NOMEAR as seleções (nunca "vários (N)"): o apostador precisa ver se a dele está na lista
            partials["artilheiro_equipe"] = (eqs[0] if len(eqs) == 1
                else "empate: " + ", ".join(eqs[:5]) + (f" +{len(eqs) - 5}" if len(eqs) > 5 else "") + f" ({mx} gols cada)")
            partials["artilheiro_gols"] = f"{mx} (parcial · {len(leaders)} empatados)"
        # ranking completo (TOP 15) p/ o pôster "A Rodada" (artilharia TOP 3) — o dict já existe.
        partials["scorers_top"] = sorted(
            ({"nome": n, "gols": v["goals"], "equipe": v["team"]} for n, v in scorers_espn.items()),
            key=lambda x: (-x["gols"], x["nome"]))[:15]
        print(f"✔ artilharia ESPN: {mx} gol(s) · {len(leaders)} líder(es) na ponta")
    elif token:
        # fallback raro (ESPN sem gols): football-data, agora também agrupando empates
        try:
            fds = fd_get("/competitions/WC/scorers?limit=15", token).get("scorers", [])
            if fds:
                mxg = fds[0].get("goals")
                tied = [s for s in fds if s.get("goals") == mxg]
                if len(tied) == 1:
                    s = tied[0]
                    eq = EN_PT.get((s.get("team", {}).get("name") or "").lower(), s.get("team", {}).get("name", "?"))
                    partials["artilheiro_nome"] = f"{s.get('player', {}).get('name', '?')} ({eq}) — {mxg} gol(s)"
                    partials["artilheiro_equipe"] = eq
                    partials["artilheiro_gols"] = f"{mxg} (parcial)"
                else:
                    nomes = ", ".join(s.get("player", {}).get("name", "?") for s in tied[:5])
                    partials["artilheiro_nome"] = f"Empatados em 1º: {len(tied)} com {mxg} gols — {nomes}"
                    partials["artilheiro_gols"] = f"{mxg} (parcial · {len(tied)} empatados)"
        except Exception as e:
            print(f"  (artilharia football-data indisponível: {e})")

    n_finished = sum(1 for v in espn.values() if v["completed"])
    # todos os eventos de jogos ENCERRADOS, em ordem cronológica (data do jogo, minuto)
    flat = []
    for mid, v in espn.items():
        if not v["completed"]:
            continue
        for ev in v["events"]:
            flat.append((v["date"], ev["order"], mid, ev))
    flat.sort(key=lambda x: (x[0], x[1]))

    def first(kind):
        for date, _o, mid, ev in flat:
            if ev["kind"] == kind and ev["team"]:
                return {"match_date": date, **ev}
        return None

    def chronology_locked(found):
        """Definitivo se TODO jogo que começou antes já encerrou (ninguém pode 'furar' a ordem)."""
        return all(v["completed"] for v in espn.values() if v["date"] and v["date"] < found["match_date"])

    fr, fo = first("red"), first("own")
    live["first_red"], live["first_own"] = fr, fo

    if fr:
        partials["equipe_1o_expulso"] = f"{fr['team']} ({fr['player']}, {fr['minute']}')"
        if facts.get("equipe_1o_expulso") is None and chronology_locked(fr):
            facts["equipe_1o_expulso"] = fr["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_expulso = {fr['team']}")
    elif n_finished:
        partials["equipe_1o_expulso"] = f"ainda não houve expulsão ({n_finished} jogo(s) conferido(s))"

    if fo:
        partials["equipe_1o_gol_contra"] = f"{fo['team']} ({fo['player']}, {fo['minute']}')"
        if facts.get("equipe_1o_gol_contra") is None and chronology_locked(fo):
            facts["equipe_1o_gol_contra"] = fo["team"]
            changed_facts = True
            print(f"✔ DEFINIDO equipe_1o_gol_contra = {fo['team']}")
    elif n_finished:
        partials["equipe_1o_gol_contra"] = f"ainda não houve gol contra ({n_finished} jogo(s) conferido(s))"

    live["partials"] = partials
    save_json(LIVE, live)
    if changed_facts:
        save_json(FACTS, facts)
    print(f"OK · lances ESPN: {n_finished} jogo(s) encerrado(s) conferido(s) · "
          f"1º expulso: {fr['team'] if fr else '—'} · 1º gol contra: {fo['team'] if fo else '—'}")


if __name__ == "__main__":
    main()
