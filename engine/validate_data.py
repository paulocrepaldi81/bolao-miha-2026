"""
Validação automática do data.json gerado — roda no robô a CADA execução, logo após
o build_data e ANTES do commit/deploy. Se algo ESTRUTURAL vier quebrado, o passo
falha (→ e-mail do GitHub) e o site NÃO publica dado ruim: a última versão boa
continua no ar.

CRÍTICO (falha o passo, bloqueia o publish):
  contagem de apostas/jogos errada · ranks não-únicos · aposta sem palpites ·
  jogo encerrado sem placar · nº de categorias extras errado · campos faltando ·
  estatística apontando apelido inexistente · modo protótipo ligado por engano.

AVISO (não bloqueia — pode estar legitimamente vazio):
  movimentação vazia (início) · sem jogo ao vivo · 2ª fonte indisponível ·
  extras ainda não definidas.

Saída: data/audit_report.txt (sempre) + código !=0 só em caso CRÍTICO.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as CFG   # nº de categorias extras vem da fonte única (EXTRA_CELLS), não hardcoded

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "..", "landing-page", "data.json")
REPORT = os.path.join(DATA, "audit_report.txt")

REQUIRED_FIELDS = ("score", "rank", "phase1_points", "exact_scores",
                   "correct_outcomes", "max_possible", "points_available")


def main():
    crit, warn = [], []

    try:
        with open(OUT, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        write_report([f"data.json não pôde ser lido/parseado: {e}"], [])
        print(f"⛔ CRÍTICO: data.json ilegível: {e}")
        sys.exit(1)

    # contagens esperadas (derivadas, não hardcoded)
    try:
        from catalog import get_catalog
        ncat = len(get_catalog())
    except Exception:
        ncat = None
    nbets = None
    bets_json = os.path.join(DATA, "bets_extracted.json")
    if os.path.exists(bets_json):
        try:
            nbets = len(json.load(open(bets_json, encoding="utf-8"))["bets"])
        except Exception:
            nbets = None

    P = d.get("participants", [])
    M = d.get("matches", [])
    ex = d.get("extras_summary", [])
    aliases = {p.get("alias") for p in P}

    def C(cond, msg):
        if not cond:
            crit.append(msg)

    def W(cond, msg):
        if not cond:
            warn.append(msg)

    # ---- META ----
    C(d.get("meta", {}).get("is_placeholder") is False,
      f"meta.is_placeholder não é False (modo protótipo?): {d.get('meta', {}).get('is_placeholder')}")

    # ---- PARTICIPANTES ----
    C(len(P) > 0, "data.json sem participantes")
    if nbets is not None:
        C(len(P) == nbets, f"nº de apostas no site ({len(P)}) != apostas extraídas ({nbets})")
    # Ranking de COMPETIÇÃO: empate em pontos = mesma posição (ex.: 1,1,3). NÃO exige 1..N único.
    # Valida que o rank de cada aposta bate com a regra: rank = 1 + nº de apostas com MAIS pontos.
    C(all(isinstance(p.get("rank"), int) for p in P), "há aposta sem rank inteiro")
    def _exp_rank(p):
        sc = p.get("score")
        return 1 + sum(1 for o in P if isinstance(o.get("score"), (int, float))
                       and isinstance(sc, (int, float)) and o["score"] > sc)
    bad_rank = [p.get("alias") for p in P if p.get("rank") != _exp_rank(p)]
    C(not bad_rank, f"rank(s) inconsistente(s) com a pontuação (empate=mesma posição): {bad_rank[:5]}")
    missing = {}
    nopicks = []
    for p in P:
        for fld in REQUIRED_FIELDS:
            if fld not in p:
                missing[fld] = missing.get(fld, 0) + 1
        if not (p.get("picks") or {}).get("groups"):
            nopicks.append(p.get("alias"))
    C(not missing, f"apostas com campos faltando: {missing}")
    C(not nopicks, f"{len(nopicks)} aposta(s) sem palpites (picks.groups): {nopicks[:5]}")

    # ---- JOGOS ----
    # Os jogos de GRUPO têm que casar com o catálogo (72). Os jogos de MATA-MATA entram com
    # 'phase' (R32/R16/...) e são contados à parte — não fazem parte do catálogo de grupos.
    grp_M = [m for m in M if not m.get("phase")]
    ko_M = [m for m in M if m.get("phase")]
    if ncat is not None:
        C(len(grp_M) == ncat, f"nº de jogos de grupo ({len(grp_M)}) != catálogo ({ncat}) · mata-mata: {len(ko_M)}")
    # AVISO: fase de mata-mata com jogos no ar mas SEM Form configurado (a coleta da fase não
    # foi ligada -> palpites valem o ORIGINAL). Não bloqueia, mas alerta o organizador (runbook).
    if ko_M:
        try:
            kf = json.load(open(os.path.join(DATA, "knockout_forms.json"), encoding="utf-8"))
            kf_rounds = {r.get("round") for r in (kf.get("rounds") or []) if r.get("csv")}
        except Exception:
            kf_rounds = set()
        # a fase "TER" (3º lugar) não tem rodada própria em knockout_forms.json — ela vem no
        # MESMO Form/rodada "FIN" (mesmo prazo da Final). Sem este mapeamento, o slot TER
        # aparecia como "fase sem Form configurado" mesmo quando FIN já cobre os dois jogos
        # (mesma lógica de build_data.py::load_knockout_deadlines).
        phases = {("FIN" if m.get("phase") == "TER" else m.get("phase")) for m in ko_M if m.get("phase")}
        for ph in sorted(phases - kf_rounds):
            W(False, f"mata-mata: fase {ph} tem jogos mas SEM Form configurado — palpites valem o original (ver forms/RUNBOOK-fases.md)")
    # CRÍTICO: o prazo de cada slot de mata-mata tem que ficar ANTES do kickoff real. Os cards
    # agregados de "jogo de agora" (gameBlockHTML em app.js) só são seguros porque presumem essa
    # ordem sempre (o jogo só vira "ao vivo"/"próximo" DEPOIS que o prazo de atualizar palpite já
    # fechou) — se um slot furar isso (deadline mal configurado, kickoff adiantado), o placar de
    # mata-mata de alguém pode aparecer nos agregados ANTES do prazo terminar. Bloqueia o publish.
    if ko_M:
        try:
            from build_data import load_knockout_deadlines
            from datetime import datetime as _dt
            ko_dl = load_knockout_deadlines(os.path.join(DATA, "knockout_forms.json"))
            furos = []
            for m in ko_M:
                slot, dl, kk = m.get("slot"), ko_dl.get(m.get("slot")), m.get("kickoff_sao_paulo")
                if not (dl and kk):
                    continue
                try:
                    kickoff = _dt.fromisoformat(kk).replace(tzinfo=None)
                except Exception:
                    continue
                if kickoff <= dl:
                    furos.append(f"{slot}: prazo {dl} não é ANTES do kickoff {kickoff}")
            C(not furos, f"mata-mata: prazo de slot(s) sem folga antes do próprio kickoff (risco de vazar palpite nos agregados) — corrija slot_deadlines: {furos[:5]}")
        except Exception:
            pass   # checagem best-effort — nunca derruba o script por conta própria de um import
    C(all(m.get("match_id") for m in M), "há jogo sem match_id")
    badfin = [m.get("match_id") for m in M
              if m.get("status") == "finished" and (m.get("home_score") is None or m.get("away_score") is None)]
    C(not badfin, f"jogo(s) encerrado(s) sem placar: {badfin}")
    # sanidade de placar (AVISO, não bloqueia): pega glitch de fonte — gol negativo ou absurdo.
    SCORE_MAX = 15
    insane = []
    for m in M:
        hs, as_ = m.get("home_score"), m.get("away_score")
        if any(isinstance(s, int) and not (0 <= s <= SCORE_MAX) for s in (hs, as_)):
            insane.append(f"{m.get('match_id')}: {m.get('home_team')} {hs}×{as_} {m.get('away_team')}")
    W(not insane, f"placar implausível — confira a fonte (glitch?): {insane[:5]}")

    # ---- CATEGORIAS EXTRAS ----
    C(len(ex) == len(CFG.EXTRA_CELLS), f"nº de categorias extras ({len(ex)}) != {len(CFG.EXTRA_CELLS)}")
    # vencedores só podem existir quando a categoria tem valor real definido
    bad_winners = [x.get("key") for x in ex if x.get("winners") and x.get("real") in (None, "")]
    C(not bad_winners, f"categoria com 'winners' sem valor real definido: {bad_winners}")

    # ---- ESTATÍSTICAS ----
    for key in ("best_exact", "cursed"):
        s = d.get("stats", {}).get(key)
        if s:
            C(s.get("alias") in aliases, f"stats.{key} aponta apelido inexistente: {s.get('alias')}")

    # ---- AVISOS (não bloqueiam) ----
    mv = d.get("movement", {})
    W(mv.get("biggest_jump") or mv.get("biggest_drop"), "movimentação vazia (normal no início da Copa)")
    au = d.get("audit")
    W(au and au.get("status") != "fonte_indisponivel", "conferência de 2ª fonte indisponível nesta rodada")
    W(any(x.get("real") not in (None, "") for x in ex), "nenhuma categoria extra definida ainda (normal no início)")

    write_report(crit, warn)
    if crit:
        print(f"⛔ AUDITORIA: {len(crit)} problema(s) CRÍTICO(s) — publish bloqueado:")
        for c in crit:
            print("   •", c)
        sys.exit(1)
    print(f"✅ AUDITORIA OK · {len(P)} apostas · {len(M)} jogos · {len(ex)} categorias"
          + (f" · {len(warn)} aviso(s)" if warn else ""))
    for w in warn:
        print("   ⚠", w)
    sys.exit(0)


def write_report(crit, warn):
    lines = ["AUDITORIA AUTOMÁTICA DO data.json", "=" * 34, ""]
    lines.append("STATUS: " + ("⛔ CRÍTICO" if crit else "✅ OK"))
    if crit:
        lines.append("\nProblemas críticos (bloqueiam a publicação):")
        lines += [f"  • {c}" for c in crit]
    if warn:
        lines.append("\nAvisos (não bloqueiam):")
        lines += [f"  ⚠ {w}" for w in warn]
    if not crit and not warn:
        lines.append("\nNenhum problema.")
    try:
        with open(REPORT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
