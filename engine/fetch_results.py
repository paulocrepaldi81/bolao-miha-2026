"""
Busca os placares oficiais da Copa 2026 e atualiza data/results.csv.

FONTE PRIMÁRIA: ESPN (API JSON pública `site.api.espn.com`, sem chave). É a mais
RÁPIDA e a que a própria ESPN usa no site — atualiza segundos após o fim do jogo,
exatamente o que o bolão precisa ("o apostador quer saber assim que acaba"). O plano
grátis da football-data.org é mais lento; por isso ela virou a 2ª fonte (cross_check.py).

Por que API e não raspar HTML do Globo/ESPN: a página de notícia muda de layout sem
aviso e quebra o robô em silêncio. A API JSON é estruturada e estável.

Uso:
  python3 fetch_results.py            # atualiza data/results.csv
  python3 fetch_results.py --dry-run  # só mostra o que faria

Segurança:
  - Linha com lock=sim em results.csv NUNCA é sobrescrita (correção manual vence).
  - Jogo sem casamento de nomes vai para o relatório, nunca é chutado.
"""
import argparse, csv, json, os, sys, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "data", "results.csv")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={a}-{b}"
# ESPN devolve ~100 eventos por chamada → varremos a Copa em janelas.
WINDOWS = [("20260611", "20260625"), ("20260626", "20260710"), ("20260711", "20260719")]

# Cache compartilhado dos eventos crus da ESPN — DENTRO DE UMA MESMA RODADA do robô, os 3 scripts
# que precisam da ESPN (fetch_results, fetch_knockout, fetch_facts + resolve_bracket) rodam em
# sequência, em segundos, e batiam na API 3-4x pro MESMO instante (mesmas janelas de data). Além
# de desperdício, isso arrisca INCONSISTÊNCIA: se um placar mudar no meio da rodada, cada script
# veria um "agora" diferente. Consolidado aqui: o 1º a rodar (fetch_results, sempre primeiro no
# workflow) busca e grava o cache; os outros reusam se ainda fresco, senão buscam ao vivo também
# (fail-safe — nunca depende de rodar em uma ordem específica).
ESPN_CACHE = os.path.join(HERE, "data", "espn_events_cache.json")
ESPN_CACHE_MAX_AGE = 180   # segundos — folga generosa (a rodada inteira do robô dura ~1 min)


def fetch_espn_raw(windows=None):
    """Busca os eventos crus da ESPN (todas as janelas) e grava no cache da rodada."""
    events = []
    for a, b in (windows or WINDOWS):
        req = urllib.request.Request(ESPN.format(a=a, b=b), headers={"User-Agent": "bolao-miha-bot"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        events.extend(data.get("events", []))
    try:
        with open(ESPN_CACHE, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": datetime.now(timezone.utc).isoformat(), "events": events}, f)
    except Exception:
        pass   # cache é só otimização — falha ao gravar não pode derrubar o script chamador
    return events


def load_espn_events(max_age=ESPN_CACHE_MAX_AGE):
    """Eventos crus da ESPN desta rodada do robô: usa o cache se ainda fresco (evita bater 3-4x
    na API pro mesmo instante); senão busca ao vivo e grava o cache pros próximos scripts."""
    try:
        with open(ESPN_CACHE, encoding="utf-8") as f:
            c = json.load(f)
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(c["fetched_at"])).total_seconds()
        if 0 <= age <= max_age:
            return c["events"]
    except Exception:
        pass   # cache ausente/corrompido/velho -> busca ao vivo, igual sempre foi
    return fetch_espn_raw()

# PT (planilha) → nomes possíveis nas APIs (inglês). Vale p/ ESPN e football-data:
# os nomes em inglês das duas são praticamente idênticos (validado: 48/48 mapeiam).
TEAM_EN = {
    "México": ["Mexico"], "África do Sul": ["South Africa"],
    "Coreia do Sul": ["South Korea", "Korea Republic"], "Rep Tcheca": ["Czechia", "Czech Republic"],
    "Canadá": ["Canada"], "Bósnia": ["Bosnia and Herzegovina", "Bosnia-Herzegovina", "Bosnia"],
    "Catar": ["Qatar"], "Suíça": ["Switzerland"],
    "Brasil": ["Brazil"], "Marrocos": ["Morocco"], "Haiti": ["Haiti"], "Escócia": ["Scotland"],
    "EUA": ["United States", "USA", "United States of America"], "Paraguai": ["Paraguay"],
    "Austrália": ["Australia"], "Turquia": ["Türkiye", "Turkey"],
    "Alemanha": ["Germany"], "Curaçao": ["Curaçao", "Curacao"],
    "Costa do Marfim": ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire"], "Equador": ["Ecuador"],
    "Holanda": ["Netherlands"], "Japão": ["Japan"], "Suécia": ["Sweden"], "Tunísia": ["Tunisia"],
    "Bélgica": ["Belgium"], "Egito": ["Egypt"], "Irã": ["Iran", "IR Iran"], "Nova Zelândia": ["New Zealand"],
    "Espanha": ["Spain"], "Cabo Verde": ["Cape Verde", "Cabo Verde", "Cape Verde Islands"],
    "Arábia Saudita": ["Saudi Arabia"], "Uruguai": ["Uruguay"],
    "França": ["France"], "Senegal": ["Senegal"], "Iraque": ["Iraq"], "Noruega": ["Norway"],
    "Argentina": ["Argentina"], "Argélia": ["Algeria"], "Áustria": ["Austria"], "Jordânia": ["Jordan"],
    "Portugal": ["Portugal"], "RD Congo": ["DR Congo", "Congo DR", "Democratic Republic of the Congo"],
    "Uzbequistão": ["Uzbekistan"], "Colômbia": ["Colombia"],
    "Inglaterra": ["England"], "Gana": ["Ghana"], "Croácia": ["Croatia"], "Panamá": ["Panama"],
}
EN_PT = {en.lower(): pt for pt, ens in TEAM_EN.items() for en in ens}


def load_catalog_pairs():
    """par de seleções (sem ordem) → jogo do catálogo."""
    from catalog import get_catalog
    return {frozenset((m["home"], m["away"])): m for m in get_catalog()}


def load_results():
    rows, order = {}, []
    if os.path.exists(RESULTS):
        with open(RESULTS, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("match_id"):
                    rows[r["match_id"]] = r
                    order.append(r["match_id"])
    return rows, order


def save_results(rows, order):
    field_order = ["match_id", "status", "home_score", "away_score", "verified", "lock"]
    seen = set(order)
    all_ids = order + [k for k in rows if k not in seen]
    with open(RESULTS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=field_order, extrasaction="ignore")
        w.writeheader()
        for mid in all_ids:
            w.writerow({k: rows[mid].get(k, "") for k in field_order})


def fetch_espn():
    """Eventos da Copa em todas as janelas → {match_id: {status, score_by_pt}}."""
    pairs = load_catalog_pairs()
    out, unmatched = {}, []
    for ev in load_espn_events():
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors", [])
        if len(cs) != 2:
            continue
        score, names, roles = {}, [], {}
        ok = True
        for c in cs:
            raw = (c.get("team", {}).get("displayName")
                   or c.get("team", {}).get("name") or "")
            pt = EN_PT.get(raw.strip().lower())
            if not pt:
                ok = False
                break
            names.append(pt)
            roles[c.get("homeAway")] = pt          # mando REAL da ESPN (home/away)
            try:
                score[pt] = int(c.get("score"))
            except (TypeError, ValueError):
                score[pt] = None
        if not ok:
            continue   # placeholders de chave ("Group A Winner") — ignora
        m = pairs.get(frozenset(names))
        if not m:
            unmatched.append(" x ".join(names))
            continue
        t = ev.get("status", {}).get("type", {})
        state, completed = t.get("state"), bool(t.get("completed"))
        status = "finished" if completed else ("live" if state == "in" else "scheduled")
        out[m["match_id"]] = {"status": status, "score": score,
                              "home": m["home"], "away": m["away"],
                              "real_home": roles.get("home"), "real_away": roles.get("away"),
                              "real_kickoff": ev.get("date") or ""}
    return out, unmatched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows, order = load_results()
    try:
        espn, unmatched = fetch_espn()
    except Exception as e:
        print(f"⚠ ESPN indisponível: {e} — results.csv mantido como está.")
        sys.exit(0)   # não derruba o pipeline; segue com o results.csv atual

    updated, locked = [], []
    for mid, e in espn.items():
        cur = rows.get(mid, {"match_id": mid})
        if str(cur.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes"):
            locked.append(mid)
            continue
        new = dict(cur)
        new["status"] = e["status"]
        hs, as_ = e["score"].get(e["home"]), e["score"].get(e["away"])
        if hs is not None and as_ is not None and e["status"] in ("finished", "live"):
            new["home_score"], new["away_score"] = str(hs), str(as_)
            new["verified"] = "sim" if e["status"] == "finished" else ""
        else:
            # jogo não disputado: limpa qualquer placar residual
            new["home_score"], new["away_score"], new["verified"] = "", "", ""
        if new != cur:
            rows[mid] = new
            if mid not in order:
                order.append(mid)
            updated.append(f"{mid}: {e['home']} {new.get('home_score','—')} x "
                           f"{new.get('away_score','—')} {e['away']} [{e['status']}]")

    if args.dry_run:
        print("DRY-RUN — mudanças que seriam aplicadas:")
    else:
        save_results(rows, order)
        # Agenda REAL da ESPN (data + mando) por match_id. A planilha pode ter a agenda errada
        # (ex.: Grupo L). O build_data usa isto SÓ p/ EXIBIÇÃO (datas/mando/orientação do palpite).
        # A PONTUAÇÃO não lê este arquivo — continua casando pelo par de times da planilha.
        real = {mid: {"home": e.get("real_home"), "away": e.get("real_away"),
                      "kickoff": e.get("real_kickoff")}
                for mid, e in espn.items() if e.get("real_home") and e.get("real_away")}
        with open(os.path.join(HERE, "data", "fixtures_real.json"), "w", encoding="utf-8") as f:
            json.dump(real, f, ensure_ascii=False, indent=1)

    print(f"[ESPN] Atualizados: {len(updated)} | travados (lock): {len(locked)} | "
          f"sem casamento: {len(unmatched)}")
    for u in updated:
        print("  ✓", u)
    for u in unmatched[:8]:
        print("  ⚠ sem casamento de nome:", u)


if __name__ == "__main__":
    main()
