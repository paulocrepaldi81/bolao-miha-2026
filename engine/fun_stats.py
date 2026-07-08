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


def compute_classico_vizinhos(participants):
    """Acha o par de apostadores mais 'colados' na tabela: ordena por pontuação e procura o
    MENOR GAP POSITIVO entre dois vizinhos consecutivos (gap=0 = empate, que não é disputa —
    já é decidido; por isso é ignorado, senão o resultado seria quase sempre um empate trivial
    em 88 apostas). Em caso de empate no menor gap, fica com o par mais alto na tabela (mais
    dramático). Retorna {"a","a_rank","b","b_rank","gap"} ou None (<2 apostadores ou só empates).
    """
    if len(participants) < 2:
        return None
    ranked = sorted(participants, key=lambda p: -p["score"])
    best = None
    for i in range(len(ranked) - 1):
        a, b = ranked[i], ranked[i + 1]
        gap = a["score"] - b["score"]
        if gap <= 0:
            continue
        if best is None or gap < best["gap"]:
            best = {"a": a["alias"], "a_rank": a["rank"], "b": b["alias"], "b_rank": b["rank"], "gap": gap}
    return best


def compute_novela_ultrapassagens(history, aliases):
    """Para cada par de apostadores, conta quantas vezes a ordem relativa entre os dois se
    inverteu ao longo dos snapshots do history.json (ex.: A passou de na-frente pra atrás de B).
    Ignora transições que passam por empate exato (rank igual não conta como 'na frente'), só
    soma quando o sinal realmente inverte de um lado pro outro. Retorna o par com MAIS trocas:
    {"a","b","count"} (ordenado alfabeticamente) ou None (histórico insuficiente / nunca houve
    troca — não distingue os dois casos, a landing trata como 'a novela ainda não tem elenco').
    """
    if len(history) < 2:
        return None
    last_sign, flips = {}, {}
    for snap in history:
        ranks = snap.get("ranks", {})
        present = [a for a in aliases if a in ranks]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                a, b = present[i], present[j]
                ra, rb = ranks[a].get("rank"), ranks[b].get("rank")
                if ra is None or rb is None or ra == rb:
                    continue
                key = (a, b) if a < b else (b, a)
                rank0 = ra if key[0] == a else rb
                rank1 = rb if key[0] == a else ra
                sign = 1 if rank0 < rank1 else -1   # +1 = key[0] na frente de key[1] agora
                prev = last_sign.get(key)
                if prev is not None and prev != sign:
                    flips[key] = flips.get(key, 0) + 1
                last_sign[key] = sign
    if not flips:
        return None
    (a, b), count = min(flips.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"a": a, "b": b, "count": count}


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
