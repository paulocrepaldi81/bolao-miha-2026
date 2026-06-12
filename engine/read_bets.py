"""
Lê UM arquivo de aposta (.xlsx preenchido) e extrai apenas os INPUTS do apostador.
Não confia em nenhuma classificação calculada pela planilha.

Retorna um dict 'bet':
  alias, file, group_preds{match_id:(h,a)}, final{champion,vice,third}, extras{...},
  issues[]  (problemas de leitura encontrados)
"""
import os
import openpyxl
import config as C


def _int_or_none(v):
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _txt(v):
    return str(v).strip() if v not in (None, "") else None


def read_bet(path, catalog):
    """catalog = saída de catalog.build_group_catalog (define onde estão os placares)."""
    issues = []
    wb = openpyxl.load_workbook(path, data_only=True)   # valores em cache p/ fórmulas (AC*)
    alias = _txt(wb[C.NAME_SHEET][C.NAME_CELL].value) or os.path.splitext(os.path.basename(path))[0]

    # --- Placares da 1ª fase (células diretas, sempre presentes se digitadas) ---
    f1 = wb["1a Fase"]
    group_preds = {}
    for m in catalog:
        h = _int_or_none(f1[m["sh_cell"]].value)
        a = _int_or_none(f1[m["sa_cell"]].value)
        if h is None or a is None:
            issues.append(f"palpite faltando no jogo {m['match_id']} ({m['home']} x {m['away']})")
            continue
        group_preds[m["match_id"]] = (h, a)

    # --- Classificação Final (fórmulas em AC*; pode vir None se salvo fora do Excel) ---
    mm = wb[C.FINAL_SHEET]
    final = {}
    for k, cell in C.FINAL_CELLS.items():
        final[k] = _txt(mm[cell].value)
        if final[k] is None:
            issues.append(f"classificação final '{k}' vazia ({cell}) — reenviar salvo no Excel")

    # --- Categorias Extras ---
    ce = wb[C.EXTRA_SHEET]
    extras = {}
    for k, cell in C.EXTRA_CELLS.items():
        raw = ce[cell].value
        extras[k] = _int_or_none(raw) if k in ("artilheiro_gols", "empates_1f", "jogos_penaltis",
                                               "mais_gols_jogo") else _txt(raw)
        if extras[k] is None:
            issues.append(f"categoria extra '{k}' vazia ({cell})")

    return {
        "alias": alias,
        "file": os.path.basename(path),
        "group_preds": group_preds,
        "final": final,
        "extras": extras,
        "issues": issues,
    }


if __name__ == "__main__":
    import sys, glob
    from catalog import build_group_catalog
    tpl = next(f for f in glob.glob("../*.xlsx") if "Modelo v2.1" in f and not f.startswith("../~$"))
    cat = build_group_catalog(tpl)
    path = sys.argv[1] if len(sys.argv) > 1 else tpl
    bet = read_bet(path, cat)
    print("Apelido:", bet["alias"])
    print("Palpites lidos (1ª fase):", len(bet["group_preds"]), "de", len(cat))
    print("Final:", bet["final"])
    print("Extras:", bet["extras"])
    print("Problemas:", len(bet["issues"]))
    for i in bet["issues"][:8]:
        print("  -", i)
