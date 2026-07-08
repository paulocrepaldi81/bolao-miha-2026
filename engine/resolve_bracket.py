"""
Auto-resolução do chaveamento do MATA-MATA. A partir dos VENCEDORES de uma fase (em
knockout_fixtures.json), gera os confrontos da fase SEGUINTE em knockout_bracket.json, usando a
topologia FIXA confirmada nas fórmulas da planilha v2.1:
    R16-k = venc(R32-(2k-1)) × venc(R32-(2k))   ·  QF-k = venc(R16-(2k-1)) × venc(R16-(2k))
    SF-k  = venc(QF-(2k-1))  × venc(QF-(2k))     ·  FIN  = venc(SF-01) × venc(SF-02)
    TER (3º lugar) = PERDEDOR(SF-01) × PERDEDOR(SF-02)
Mandante do novo slot = vencedor do slot ÍMPAR (mesma orientação do palpite original).

Roda no robô DEPOIS do fetch_knockout. Idempotente e FAIL-CLOSED:
  • só gera um slot quando os DOIS alimentadores já têm vencedor definido;
  • NUNCA sobrescreve um slot já preenchido (permite correção/lock manual);
  • sem vencedores suficientes, não faz nada.
Puxa o horário (kickoff) da ESPN para o novo confronto, quando já publicado.
Uso: python3 resolve_bracket.py [--dry-run]
"""
import argparse, json, os
from fetch_results import EN_PT, load_espn_events
from config import SPECIAL_SLOTS   # fonte única (leaderboard.py também usa pra pontos restantes)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BRACKET = os.path.join(DATA, "knockout_bracket.json")
FIX = os.path.join(DATA, "knockout_fixtures.json")

NEXT = {"R32": "R16", "R16": "QF", "QF": "SF", "SF": "FIN"}
N_SLOTS = {"R16": 8, "QF": 4, "SF": 2, "FIN": 1}


def _load(path, d):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return d


def _espn_kickoffs():
    """{frozenset(home,away): kickoff_iso} dos jogos de mata-mata na ESPN (p/ os novos confrontos).
    Usa o cache compartilhado da rodada (load_espn_events) em vez de bater na API de novo —
    fetch_results.py já buscou os mesmos eventos poucos segundos antes, nesta mesma rodada do robô."""
    out = {}
    try:
        for ev in load_espn_events():
            cs = (ev.get("competitions") or [{}])[0].get("competitors", [])
            if len(cs) != 2:
                continue
            names = [EN_PT.get((c.get("team", {}).get("displayName") or "").strip().lower()) for c in cs]
            if all(names):
                out[frozenset(names)] = ev.get("date")
    except Exception as e:
        print(f"  ⚠ ESPN (kickoffs) indisponível: {e}")
    return out


def resolve():
    bracket = _load(BRACKET, {})
    fix = _load(FIX, {})
    winner = {s: e["winner"] for s, e in fix.items() if e.get("winner")}
    loser = {s: (e["away"] if e["winner"] == e["home"] else e["home"])
             for s, e in fix.items() if e.get("winner") and e.get("home") and e.get("away")}
    have = {e["slot"] for ents in bracket.values() if isinstance(ents, list) for e in ents if e.get("home")}

    new = []   # (fase, slot, home, away)
    for phase, nxt in NEXT.items():
        for k in range(1, N_SLOTS[nxt] + 1):
            slot = "FIN" if nxt == "FIN" else f"{nxt}-{k:02d}"
            if slot in have:
                continue
            f1, f2 = f"{phase}-{2 * k - 1:02d}", f"{phase}-{2 * k:02d}"
            if f1 in winner and f2 in winner:
                new.append((nxt, slot, winner[f1], winner[f2]))   # mandante = vencedor do ímpar
    if "TER" not in have and "SF-01" in loser and "SF-02" in loser:
        new.append(("TER", "TER", loser["SF-01"], loser["SF-02"]))   # 3º lugar = perdedores das SFs

    if not new:
        return bracket, []
    kicks = _espn_kickoffs()
    for nxt, slot, home, away in new:
        bracket.setdefault(nxt, []).append(
            {"slot": slot, "home": home, "away": away,
             "kickoff": kicks.get(frozenset((home, away))), "special": slot in SPECIAL_SLOTS})
    return bracket, new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    bracket, new = resolve()
    if not new:
        print("chaveamento: nada novo a resolver (sem vencedores suficientes ainda).")
        return 0
    for nxt, slot, home, away in new:
        print(f"  ➜ {slot}: {home} × {away}")
    # bloco pronto pra colar no MATCHES do Form da nova fase (o organizador só ajusta o 'quando')
    by_phase = {}
    for nxt, slot, home, away in new:
        by_phase.setdefault(nxt, []).append((int(slot.split("-")[1]) if "-" in slot else 1, home, away))
    for phase, lst in by_phase.items():
        print(f"\n=== COLE no MATCHES do Form da fase {phase} (ajuste 'quando' com a data/hora) ===")
        for n, home, away in sorted(lst):
            print(f"  {{ n: {n}, home: '{home}', away: '{away}', quando: '??/?? · ??h' }},")
    if not args.dry_run:
        with open(BRACKET, "w", encoding="utf-8") as f:
            json.dump(bracket, f, ensure_ascii=False, indent=2)
        print(f"OK · {len(new)} confronto(s) novo(s) gravado(s) no chaveamento.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
