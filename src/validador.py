"""Validador: barra no texto do feedback o que não vem dos dados ou fere o tom.

Três checagens:
1. todo número do texto precisa existir nos fatos calculados (anti-invenção);
2. nada de rótulo pessoal nem de comparação nominal com colega;
3. nada de "texto de robô" (jargão genérico dos exemplos ruins).
"""
import re

ROTULOS_PESSOAIS = (
    "preguiç", "desleix", "incompetent", "desinteress", "problema de atitude",
    "não tem jeito", "burr", "fraca", "fraco", "relaxad",
)
JARGAO_ROBO = (
    "prezado colaborador", "oportunidades de melhoria", "múltiplas dimensões",
    "busque excelência", "foque em resultados",
)
FRASES_PROIBIDAS = (
    "problema pessoal fica em casa", "tô de olho", "por que você não faz igual",
)

_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")
_DATA = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b20\d\d\b")


def numeros_do_texto(texto: str) -> list:
    achados = []
    for m in _NUMERO.findall(texto):
        achados.append(float(m.replace(".", "").replace(",", ".")) if "," in m and "." in m
                       else float(m.replace(",", ".")))
    return achados


def _casa(valor: float, permitidos: list) -> bool:
    for p in permitidos:
        # tolera arredondamento (1,26 ~ 1.2634; 51 ~ 50.7; 228 ~ 228.14)
        if abs(valor - p) <= max(0.06, abs(p) * 0.006) or abs(valor - round(p)) < 1e-9:
            return True
        if abs(valor - round(p, 1)) < 1e-9 or abs(valor - round(p, 2)) < 1e-9:
            return True
    return False


def validar(texto: str, numeros_permitidos: list, nomes_colegas: list = ()) -> list:
    """Devolve a lista de problemas encontrados (vazia = texto aprovado)."""
    problemas = []
    baixo = texto.lower()

    for n in numeros_do_texto(_DATA.sub(" ", texto)):
        if n in (1, 2, 3):          # "1 min", "2 semanas", "3 itens": contagens soltas
            continue
        if not _casa(n, numeros_permitidos):
            problemas.append(f"Número sem origem nos dados: {n:g}")

    for termo in ROTULOS_PESSOAIS:
        if termo in baixo:
            problemas.append(f"Rótulo pessoal: '{termo}'")
    for termo in JARGAO_ROBO:
        if termo in baixo:
            problemas.append(f"Texto genérico de robô: '{termo}'")
    for termo in FRASES_PROIBIDAS:
        if termo in baixo:
            problemas.append(f"Frase proibida: '{termo}'")
    for nome in nomes_colegas:
        if nome.split()[0].lower() in baixo:
            problemas.append(f"Comparação nominal com colega: '{nome.split()[0]}'")
    return problemas
