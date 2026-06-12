"""Gera 3 planilhas de exemplo preenchidas (apenas para ensaio do motor)."""
import os, glob, openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = next(f for f in glob.glob(os.path.join(HERE, "..", "*.xlsx")) if "Modelo v2.1" in f and "~$" not in f)
OUT = os.path.join(HERE, "bets"); os.makedirs(OUT, exist_ok=True)

# A1 = C6/D6 (México x Áfr.Sul) | B1 = I6/J6 (Canadá x Bósnia, ESPECIAL) | C1 = O6/P6 (Brasil x Marrocos)
EXAMPLES = {
    "Crepaldi":  {"C6": 2, "D6": 1, "I6": 1, "J6": 1, "O6": 3, "P6": 0,  # placares
                  "champ": "Brasil", "vice": "França", "third": "Argentina"},
    "PaulinhIA": {"C6": 1, "D6": 0, "I6": 2, "J6": 2, "O6": 2, "P6": 1,
                  "champ": "Argentina", "vice": "Brasil", "third": "Espanha"},
    "Mihalik":   {"C6": 0, "D6": 1, "I6": 1, "J6": 1, "O6": 1, "P6": 0,
                  "champ": "França", "vice": "Inglaterra", "third": "Brasil"},
}

for name, v in EXAMPLES.items():
    wb = openpyxl.load_workbook(TPL)
    wb["1a Fase"]["B2"] = name
    for cell in ("C6", "D6", "I6", "J6", "O6", "P6"):
        wb["1a Fase"][cell] = v[cell]
    # Classificação final (sobrescreve a fórmula com literal — só no exemplo)
    wb["Mata-Mata"]["AC9"], wb["Mata-Mata"]["AC13"], wb["Mata-Mata"]["AC17"] = v["champ"], v["vice"], v["third"]
    # Uma categoria extra de exemplo
    wb["Categorias Extras"]["C5"] = "Mbappé"
    wb["Categorias Extras"]["C19"] = 9      # nº de empates na 1ª fase
    wb.save(os.path.join(OUT, f"{name}.xlsx"))
    print("gerado:", f"{name}.xlsx")
