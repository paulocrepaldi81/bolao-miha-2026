"""
Configuração do motor de pontuação do Bolão Miha 2026.

Princípio central (decisão do projeto): NÃO confiamos na classificação que a
planilha calcula. Lemos apenas os INPUTS do apostador (placares digitados,
campeão/vice/3º deduzidos pelo chaveamento, categorias extras) e recalculamos
tudo aqui — eliminando o problema de cache de fórmula do openpyxl e dando
verificação independente.
"""

# ---- Detecção de jogo especial (5 pts) pela cor da célula ----
SPECIAL_FILL = "FFDBFC14"   # verde-limão = especial · amarelo (FFFFFF99) = normal

# ---- Layout da aba "1a Fase" (12 grupos × 6 jogos) ----
# Cada bloco de colunas = (mandante, placar_mandante, placar_visitante, visitante, data)
COL_BLOCKS = [("B", "C", "D", "E", "F"),
              ("H", "I", "J", "K", "L"),
              ("N", "O", "P", "Q", "R"),
              ("T", "U", "V", "W", "X")]
ROW_BLOCKS = [range(6, 12), range(15, 21), range(24, 30)]
# Grupos por (linha_bloco, coluna_bloco)
GROUPS_BY_BLOCK = [["A", "B", "C", "D"],
                   ["E", "F", "G", "H"],
                   ["I", "J", "K", "L"]]

NAME_SHEET, NAME_CELL = "1a Fase", "B2"   # apelido da aposta

# ---- Classificação Final (aba Mata-Mata, deduzida do chaveamento) ----
FINAL_SHEET = "Mata-Mata"
FINAL_CELLS = {"champion": "AC9", "vice": "AC13", "third": "AC17"}

# ---- Categorias Extras (4ª aba, input uma linha abaixo de cada rótulo) ----
EXTRA_SHEET = "Categorias Extras"
EXTRA_CELLS = {
    "artilheiro_nome":      "C5",
    "artilheiro_equipe":    "C7",
    "artilheiro_gols":      "C9",
    "mais_goleadora":       "C13",
    "menos_vazada":         "C15",
    "mais_gols_jogo":       "C17",
    "empates_1f":           "C19",
    "jogos_penaltis":       "C21",
    "equipe_1o_expulso":    "C23",
    "equipe_1o_gol_contra": "C25",
    "azarao":               "C27",
}

# ---- Regras de pontuação (aba "Regras") ----
PTS_OUTCOME_NORMAL  = 3      # vencedor/empate correto (jogo normal)
PTS_OUTCOME_SPECIAL = 5      # vencedor/empate correto (jogo especial)
BONUS_MIN           = 2      # bônus mínimo por placar exato
# bônus por placar exato = nº de gols na partida (mínimo BONUS_MIN)

PTS_CHAMP = 15
PTS_VICE  = 10
PTS_THIRD = 5
PTS_TOP3_WRONG_POS = 3       # equipe no top-3 real, mas em posição errada

# Categorias extras
PTS_ART_NOME   = 8
PTS_ART_EQUIPE = 4
PTS_ART_GOLS   = 3
PTS_ART_BONUS  = 5           # acertar nome + equipe + gols
PTS_CURIOSIDADE = 5          # cada curiosidade

CURIOSIDADES = ["mais_goleadora", "menos_vazada", "mais_gols_jogo", "empates_1f",
                "jogos_penaltis", "equipe_1o_expulso", "equipe_1o_gol_contra", "azarao"]

# ---- Bolão ----
BET_VALUE = 60              # R$ por aposta paga
PRIZE_SPLIT = {"champ": 0.40, "vice": 0.25, "third": 0.10, "fourth": 0.05, "bom_palpite": 0.20}
# Lanterna de Ouro: recebe a aposta de volta (BET_VALUE) ANTES; percentuais sobre o resto.

# Limite superior generoso p/ "matematicamente vivo" (nunca elimina por engano)
MAX_BONUS_CAP = 6           # bônus máximo plausível por jogo não disputado
KNOCKOUT_POTENTIAL = 250    # estimativa de pontos ainda em jogo no mata-mata (v1: ninguém é eliminado na fase de grupos)
