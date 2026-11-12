"""Indicadores (as contas do LEIAME). Tudo é calculado aqui, nunca pelo LLM."""
import pandas as pd

from .tratamento import adicionar_mes


def _div(a: pd.Series, b: pd.Series) -> pd.Series:
    """Divisão segura: denominador zero vira NaN."""
    return a.where(b > 0) / b.where(b > 0)


def _calcular(g: pd.DataFrame) -> pd.DataFrame:
    g["ticket_medio"] = _div(g["valor"], g["vendas"])       # valor ÷ vendas
    g["pa"] = _div(g["pecas"], g["vendas"])                 # peças ÷ vendas
    g["conversao"] = _div(g["vendas"], g["atendimentos"])   # vendas ÷ atendimentos
    return g


def indicadores_mensais(diario, metas_vendedor, vendedores) -> pd.DataFrame:
    """Uma linha por pessoa por mês. O gerente não tem meta (atingimento = NaN)."""
    d = adicionar_mes(diario)
    g = d.groupby(["vendedor_id", "nome", "mes"], as_index=False).agg(
        valor=("valor_vendido", "sum"),
        vendas=("vendas", "sum"),
        pecas=("pecas", "sum"),
        atendimentos=("atendimentos", "sum"),
        dias_trabalhados=("data", "nunique"),
    )
    g = g.merge(
        metas_vendedor[["vendedor_id", "mes", "dias_escalados", "meta_valor"]],
        on=["vendedor_id", "mes"], how="left",
    )
    g = g.merge(vendedores[["vendedor_id", "cargo"]], on="vendedor_id", how="left")
    g = _calcular(g)
    g["atingimento"] = _div(g["valor"], g["meta_valor"])    # valor do mês ÷ meta do mês
    return g


def indicadores_time(ind: pd.DataFrame) -> pd.DataFrame:
    """Média ponderada do time de vendedores (sem o gerente), por mês."""
    v = ind[ind["cargo"] != "gerente"]
    g = v.groupby("mes", as_index=False).agg(
        valor=("valor", "sum"), vendas=("vendas", "sum"),
        pecas=("pecas", "sum"), atendimentos=("atendimentos", "sum"),
    )
    return _calcular(g)


def atingimento_loja(diario, metas_loja) -> pd.DataFrame:
    """Meta da loja: conta as vendas de todos, inclusive as do gerente."""
    d = adicionar_mes(diario)
    g = d.groupby("mes", as_index=False)["valor_vendido"].sum().rename(
        columns={"valor_vendido": "valor"})
    g = g.merge(metas_loja, on="mes", how="left")
    g["atingimento"] = _div(g["valor"], g["meta_valor"])
    return g
