"""Tratamento: contexto que muda a leitura dos números (férias, novato, anotações)."""
import pandas as pd

PALAVRAS_CONTEXTO_PESSOAL = (
    "internado", "hospital", "luto", "faleceu", "doença", "doente", "médico", "cirurgia",
)
PALAVRAS_CONVERSA = ("combinamos", "conversei", "combinei", "pedi pra")


def adicionar_mes(diario: pd.DataFrame) -> pd.DataFrame:
    d = diario.copy()
    d["mes"] = d["data"].dt.strftime("%Y-%m")
    return d


def meses_completos(diario: pd.DataFrame, min_dias: int = 20) -> list:
    """Meses com dados suficientes (o dia 01/11 sozinho não conta como mês)."""
    d = adicionar_mes(diario)
    dias = d.groupby("mes")["data"].nunique()
    return sorted(dias[dias >= min_dias].index)


def periodo_ferias(texto):
    """'2026-09-08 a 2026-09-27' -> (Timestamp, Timestamp); vazio -> None."""
    if not isinstance(texto, str) or " a " not in texto:
        return None
    ini, fim = texto.split(" a ")
    return pd.Timestamp(ini.strip()), pd.Timestamp(fim.strip())


def contexto_vendedor(vendedores: pd.DataFrame, nome: str, mes: str) -> dict:
    """Flags de contexto do vendedor naquele mês."""
    linha = vendedores[vendedores["nome"] == nome].iloc[0]
    ini_mes = pd.Timestamp(mes + "-01")
    fim_mes = ini_mes + pd.offsets.MonthEnd(0)

    ferias, dias_ferias = False, 0
    periodo = periodo_ferias(linha["ferias_no_periodo"])
    if periodo:
        ini = max(periodo[0], ini_mes)
        fim = min(periodo[1], fim_mes)
        if ini <= fim:
            ferias, dias_ferias = True, (fim - ini).days + 1

    meses_de_casa = int((fim_mes - linha["data_admissao"]).days // 30.4)
    return {
        "ferias": ferias,
        "dias_ferias": dias_ferias,
        "meses_de_casa": meses_de_casa,
        "novato": meses_de_casa < 3,
        "cargo": linha["cargo"],
    }


def anotacoes_da_pessoa(anotacoes: pd.DataFrame, nome: str, ate: str = None) -> list:
    """Anotações do gerente sobre a pessoa, da mais antiga para a mais nova.
    `ate` = 'AAAA-MM' inclui só anotações até o fim daquele mês."""
    a = anotacoes[anotacoes["sobre"] == nome]
    if ate:
        fim = pd.Timestamp(ate + "-01") + pd.offsets.MonthEnd(0)
        a = a[a["data"] <= fim]
    a = a.sort_values("data")
    return [{"data": r["data"], "texto": r["anotacao"]} for _, r in a.iterrows()]


def tem_contexto_pessoal(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in PALAVRAS_CONTEXTO_PESSOAL)


def foi_conversa(texto: str) -> bool:
    """A anotação registra uma conversa/orientação do gerente com a pessoa?"""
    t = texto.lower()
    return any(p in t for p in PALAVRAS_CONVERSA)
