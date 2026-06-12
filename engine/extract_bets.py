"""
Extrai os INPUTS de todas as planilhas de aposta para um único JSON
(data/bets_extracted.json). Roda UMA vez (e de novo só se chegarem
planilhas novas/atualizadas).

Por que existe: o robô de atualização (GitHub Actions) pontua a cada rodada
sem precisar das planilhas .xlsx — só do JSON extraído. As planilhas ficam
na sua máquina; o JSON contém apenas apelido + palpites.

Uso:
  cd engine
  python3 extract_bets.py --bets ./bets
"""
import argparse, glob, json, os

from catalog import build_group_catalog
from read_bets import read_bet

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bets", default="./bets")
    ap.add_argument("--template", default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "data", "bets_extracted.json"))
    args = ap.parse_args()

    template = args.template or next(
        f for f in glob.glob(os.path.join(HERE, "..", "*.xlsx"))
        if "Modelo v2.1" in f and "~$" not in f)
    catalog = build_group_catalog(template)

    files = [f for f in sorted(glob.glob(os.path.join(args.bets, "*.xlsx")))
             if "~$" not in os.path.basename(f)]
    bets, issues = [], 0
    for path in files:
        b = read_bet(path, catalog)
        issues += len(b["issues"])
        bets.append(b)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"bets": bets}, f, ensure_ascii=False, indent=1)
    print(f"OK · {len(bets)} apostas extraídas → {args.out}")
    if issues:
        print(f"  ⚠ {issues} aviso(s) de leitura — rode build_data.py p/ ver o relatório")


if __name__ == "__main__":
    main()
