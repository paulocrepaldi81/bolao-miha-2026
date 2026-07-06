"""
Estatísticas "divertidas/curiosas" do bolão (não afetam pontuação — são só para a landing page).
Puro e sem I/O: recebe os dados já carregados por build_data.py e devolve dicts prontos pra
JSON. Fail-safe: entrada insuficiente devolve None/vazio, nunca lança exceção que derrube o robô.
"""
import statistics

MIN_COMMON_GAMES = 20    # jogos em comum mínimos p/ considerar um par no "gêmeo de aposta"
MIN_FILLED_GAMES = 10    # jogos preenchidos mínimos p/ entrar no "time-quente/cabeça-fria"


def compute_twins(bets):
    """Para cada apostador, acha o(s) 'gêmeo' (MENOR distância) e o(s) 'rival' (MAIOR distância)
    entre todos os outros, comparando o placar apostado nos jogos de GRUPO. Distância(A,B) = soma,
    em cada jogo que ambos preencheram, de |casaA-casaB| + |foraA-foraB| (0 = apostas idênticas).
    Empates: lista TODOS os nomes empatados (nunca escolhe 1 arbitrariamente). Retorna
    {alias: {"twin": {"aliases":[...], "distance":int}, "rival": {...}} | {"twin":None,"rival":None}}.
    """
    aliases = [b["alias"] for b in bets]
    preds = {b["alias"]: b.get("group_preds", {}) for b in bets}
    out = {a: {"twin": None, "rival": None} for a in aliases}
    for ai in aliases:
        gi = preds[ai]
        dists = []
        for aj in aliases:
            if aj == ai:
                continue
            gj = preds[aj]
            common = gi.keys() & gj.keys()
            if len(common) < MIN_COMMON_GAMES:
                continue
            d = sum(abs(gi[m][0] - gj[m][0]) + abs(gi[m][1] - gj[m][1]) for m in common)
            dists.append((d, aj))
        if not dists:
            continue
        mind = min(d for d, _ in dists)
        maxd = max(d for d, _ in dists)
        out[ai]["twin"] = {"aliases": sorted(a for d, a in dists if d == mind), "distance": mind}
        out[ai]["rival"] = {"aliases": sorted(a for d, a in dists if d == maxd), "distance": maxd}
    return out


def compute_wisdom(bets, results, catalog):
    """'Sabedoria das multidões': compara o erro do PLACAR-CONSENSO (mediana do placar apostado
    pelo bolão inteiro) contra o erro MÉDIO INDIVIDUAL, nos jogos de GRUPO já encerrados. Se o
    consenso erra menos, é o efeito clássico de wisdom-of-the-crowd. Retorna None se não houver
    jogo encerrado (fail-safe — categoria só aparece quando há dado real).
    """
    cat_by_id = {m["match_id"]: m for m in catalog}
    consensus_errs, individual_errs, deltas = [], [], []
    for mid, m in cat_by_id.items():
        r = results.get(mid, {})
        if r.get("status") != "finished" or r.get("home_score") is None:
            continue
        rh, ra = r["home_score"], r["away_score"]
        homes, aways = [], []
        for b in bets:
            gp = b.get("group_preds", {}).get(mid)
            if gp:
                homes.append(gp[0])
                aways.append(gp[1])
        if not homes:
            continue
        ch, ca = statistics.median(homes), statistics.median(aways)
        c_err = abs(rh - ch) + abs(ra - ca)
        i_err = statistics.mean(abs(rh - h) + abs(ra - a) for h, a in zip(homes, aways))
        consensus_errs.append(c_err)
        individual_errs.append(i_err)
        deltas.append((i_err - c_err, mid, rh, ra, ch, ca, m.get("home"), m.get("away")))
    if not consensus_errs:
        return None
    mc, mi = statistics.mean(consensus_errs), statistics.mean(individual_errs)
    pct_better = (1 - mc / mi) * 100 if mi else 0.0

    def _entry(e):
        _, mid, rh, ra, ch, ca, home, away = e
        return {"match_id": mid, "home": home, "away": away,
                "real": [rh, ra], "consensus": [round(ch, 1), round(ca, 1)]}
    deltas.sort(reverse=True)   # maior delta primeiro = onde o consenso mais "ganhou"
    return {
        "games_evaluated": len(consensus_errs),
        "consensus_avg_error": round(mc, 3),
        "individual_avg_error": round(mi, 3),
        "pct_better": round(pct_better, 1),
        "best_call": _entry(deltas[0]),
        "worst_call": _entry(deltas[-1]),
    }


def compute_goal_profile(bets):
    """Perfil de apostador pela média de gols apostados por jogo de GRUPO (casa+fora, dividido
    pelo nº de jogos preenchidos — não a soma bruta, pra não penalizar aposta incompleta). Exige
    MIN_FILLED_GAMES pra entrar (amostra pequena distorce a média). z-score vs a média do bolão:
    z>1 = 'quente' (aposta gols pra caramba), z<-1 = 'frio' (aposta cauteloso), senão 'equilibrado'.
    Retorna {alias: {"avg_goals","z","label","bolao_avg"} | None (poucos jogos/sem dado)}.
    """
    raw = {}
    for b in bets:
        gp = b.get("group_preds", {})
        n = len(gp)
        if n < MIN_FILLED_GAMES:
            raw[b["alias"]] = None
            continue
        raw[b["alias"]] = sum(h + a for h, a in gp.values()) / n
    valid = [v for v in raw.values() if v is not None]
    if len(valid) < 2:
        return {a: None for a in raw}
    mu = statistics.mean(valid)
    sigma = statistics.pstdev(valid) or 1e-9
    out = {}
    for alias, avg in raw.items():
        if avg is None:
            out[alias] = None
            continue
        z = (avg - mu) / sigma
        label = "quente" if z > 1 else ("frio" if z < -1 else "equilibrado")
        out[alias] = {"avg_goals": round(avg, 2), "z": round(z, 2), "label": label, "bolao_avg": round(mu, 2)}
    return out


def compute_rank_history(history, aliases):
    """Reduz o history.json (um snapshot a cada MUDANÇA de classificação, não por tempo fixo)
    a 1 PONTO POR DIA CORRIDO (o último snapshot de cada dia — 'ts' já vem no fuso de SP) —
    mantém o data.json leve mesmo com a Copa inteira de histórico. Ignora aliases que ainda não
    existiam num dia (entram como None; snapshots de teste/antigos sem o alias atual já ficam
    fora naturalmente, sem filtro especial). Retorna (dates, series) — dates=['YYYY-MM-DD',...],
    series={alias: [[rank,total]|None, ...]} alinhado a dates. Fail-safe: history vazio -> ([], {}).
    """
    if not history:
        return [], {a: [] for a in aliases}
    by_day = {}
    for snap in history:   # history já vem em ordem cronológica -> o último grava por cima
        day = (snap.get("ts") or "")[:10]
        if day:
            by_day[day] = snap
    dates = sorted(by_day)
    series = {a: [] for a in aliases}
    for day in dates:
        ranks = by_day[day].get("ranks", {})
        for a in aliases:
            r = ranks.get(a)
            series[a].append([r["rank"], r["total"]] if r else None)
    return dates, series
