"""
Busca os placares oficiais da Copa 2026 automaticamente e atualiza data/results.csv.

Fonte: football-data.org (API estruturada e estável; espelha os dados oficiais FIFA).
Por que API e não raspar Globo/FIFA/ESPN: páginas de notícia mudam de HTML sem aviso
e quebram robôs em silêncio — uma API estruturada é a forma confiável de automatizar.
A verificação editorial (FIFA/GE/ESPN) continua sendo a checagem humana via `lock`.

Setup (uma vez):
  1. Crie uma chave grátis em https://www.football-data.org/client/register
  2. Exporte:  export FOOTBALL_DATA_TOKEN=suachave
     (no GitHub Actions: Settings → Secrets → FOOTBALL_DATA_TOKEN)

Uso:
  python3 fetch_results.py            # atualiza data/results.csv
  python3 fetch_results.py --dry-run  # só mostra o que faria

Regras de segurança:
  - Linha com lock=sim em results.csv NUNCA é sobrescrita (correção manual vence).
  - Jogo sem casamento de nomes vai para o relatório, nunca é chutado.
"""
import argparse, csv, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "data", "results.csv")
API = "https://api.football-data.org/v4/competitions/WC/matches"

# PT (planilha) → nomes possíveis na API (inglês)
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
    "Bélgica": ["Belgium"], "Egito": ["Egypt"], "Irã": ["Iran"], "Nova Zelândia": ["New Zealand"],
    "Espanha": ["Spain"], "Cabo Verde": ["Cape Verde", "Cabo Verde", "Cape Verde Islands"],
    "Arábia Saudita": ["Saudi Arabia"], "Uruguai": ["Uruguay"],
    "França": ["France"], "Senegal": ["Senegal"], "Iraque": ["Iraq"], "Noruega": ["Norway"],
    "Argentina": ["Argentina"], "Argélia": ["Algeria"], "Áustria": ["Austria"], "Jordânia": ["Jordan"],
    "Portugal": ["Portugal"], "RD Congo": ["DR Congo", "Congo DR", "Democratic Republic of the Congo"],
    "Uzbequistão": ["Uzbekistan"], "Colômbia": ["Colombia"],
    "Inglaterra": ["England"], "Gana": ["Ghana"], "Croácia": ["Croatia"], "Panamá": ["Panama"],
}
EN_PT = {en.lower(): pt for pt, ens in TEAM_EN.items() for en in ens}

STATUS_MAP = {"FINISHED": "finished", "IN_PLAY": "live", "PAUSED": "live",
              "TIMED": "scheduled", "SCHEDULED": "scheduled", "POSTPONED": "scheduled"}


def load_catalog_pairs():
    """match_id por par (home,away) em PT, nas duas ordens."""
    from catalog import get_catalog
    pairs = {}
    for m in get_catalog():
        pairs[(m["home"], m["away"])] = m["match_id"]
        pairs[(m["away"], m["home"])] = m["match_id"]   # API pode inverter mando
    return pairs


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


def fetch_api(token):
    req = urllib.request.Request(API, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        print("⚠ FOOTBALL_DATA_TOKEN não definido — nada buscado.")
        print("  Crie a chave grátis em https://www.football-data.org/client/register")
        print("  e rode:  export FOOTBALL_DATA_TOKEN=suachave")
        sys.exit(0)   # sai sem erro: o pipeline segue com o results.csv manual

    pairs = load_catalog_pairs()
    rows, order = load_results()
    data = fetch_api(token)

    updated, unmatched, locked = [], [], []
    for fx in data.get("matches", []):
        if fx.get("stage") and "GROUP" not in fx["stage"].upper():
            continue   # v1: só fase de grupos (mata-mata entra no v2)
        ht = EN_PT.get((fx.get("homeTeam", {}).get("name") or "").lower())
        at = EN_PT.get((fx.get("awayTeam", {}).get("name") or "").lower())
        if not ht or not at:
            unmatched.append(f"{fx.get('homeTeam',{}).get('name')} x {fx.get('awayTeam',{}).get('name')}")
            continue
        mid = pairs.get((ht, at))
        if not mid:
            unmatched.append(f"{ht} x {at} (sem match_id)")
            continue
        status = STATUS_MAP.get(fx.get("status", ""), "scheduled")
        ft = fx.get("score", {}).get("fullTime", {})
        hs, as_ = ft.get("home"), ft.get("away")
        cur = rows.get(mid, {"match_id": mid})
        if str(cur.get("lock", "")).strip().lower() in ("sim", "1", "true", "yes"):
            locked.append(mid)
            continue
        new = dict(cur)
        new["status"] = status
        if hs is not None and as_ is not None and status in ("finished", "live"):
            # respeita a ordem mandante/visitante da PLANILHA
            new_h, new_a = (hs, as_) if _same_order(ht, at, mid) else (as_, hs)
            new["home_score"], new["away_score"] = str(new_h), str(new_a)
            new["verified"] = "sim" if status == "finished" else ""
        if new != cur:
            rows[mid] = new
            if mid not in order:
                order.append(mid)
            updated.append(f"{mid}: {ht} {new.get('home_score','—')} x {new.get('away_score','—')} {at} [{status}]")

    if args.dry_run:
        print("DRY-RUN — mudanças que seriam aplicadas:")
    else:
        save_results(rows, order)

    print(f"Atualizados: {len(updated)} | travados (lock): {len(locked)} | sem casamento: {len(unmatched)}")
    for u in updated:
        print("  ✓", u)
    for u in unmatched[:10]:
        print("  ⚠ sem casamento de nome:", u)


_ORDER_CACHE = None
def _same_order(ht, at, mid):
    """True se (ht, at) é a ordem mandante/visitante da planilha para mid."""
    global _ORDER_CACHE
    if _ORDER_CACHE is None:
        from catalog import get_catalog
        _ORDER_CACHE = {m["match_id"]: (m["home"], m["away"]) for m in get_catalog()}
    return _ORDER_CACHE.get(mid) == (ht, at)


if __name__ == "__main__":
    main()
