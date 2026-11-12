
import pandas as pd
import pytest

from src.indicadores import (
    _div,
    indicadores_mensais,
    indicadores_time,
    atingimento_loja,
)


@pytest.fixture
def dados():
    diario = pd.DataFrame({
        "data": pd.to_datetime([
            "2026-09-01",
            "2026-09-01",
            "2026-09-01",
        ]),
        "vendedor_id": ["v1", "v2", "g1"],
        "nome": ["Ana", "João", "Gerente"],
        "valor_vendido": [200.0, 300.0, 100.0],
        "vendas": [2, 3, 1],
        "pecas": [4, 9, 2],
        "atendimentos": [10, 15, 5],
    })

    metas_vendedor = pd.DataFrame({
        "vendedor_id": ["v1", "v2"],
        "mes": ["2026-09", "2026-09"],
        "dias_escalados": [20, 22],
        "meta_valor": [400.0, 500.0],
    })

    vendedores = pd.DataFrame({
        "vendedor_id": ["v1", "v2", "g1"],
        "cargo": ["vendedor", "vendedor", "gerente"],
    })

    metas_loja = pd.DataFrame({
        "mes": ["2026-09"],
        "meta_valor": [1000.0],
    })

    return diario, metas_vendedor, vendedores, metas_loja


def test_indicadores_mensais(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    assert len(resultado) == 3
    assert "mes" in resultado.columns
    assert resultado["mes"].unique().tolist() == ["2026-09"]


def test_ticket_medio(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    ana = resultado[resultado["nome"] == "Ana"].iloc[0]

    assert ana["ticket_medio"] == pytest.approx(100.0)


def test_pa(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    ana = resultado[resultado["nome"] == "Ana"].iloc[0]

    assert ana["pa"] == pytest.approx(2.0)


def test_conversao(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    ana = resultado[resultado["nome"] == "Ana"].iloc[0]

    assert ana["conversao"] == pytest.approx(0.2)


def test_atingimento_individual(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    ana = resultado[resultado["nome"] == "Ana"].iloc[0]

    assert ana["atingimento"] == pytest.approx(0.5)


def test_gerente_nao_tem_meta(dados):
    diario, metas, vendedores, _ = dados

    resultado = indicadores_mensais(
        diario, metas, vendedores
    )

    gerente = resultado[
        resultado["nome"] == "Gerente"
    ].iloc[0]

    assert pd.isna(gerente["atingimento"])


def test_indicadores_time_exclui_gerente(dados):
    diario, metas, vendedores, _ = dados

    mensal = indicadores_mensais(
        diario, metas, vendedores
    )

    resultado = indicadores_time(mensal)

    assert len(resultado) == 1
    assert resultado.iloc[0]["valor"] == 500.0
    assert resultado.iloc[0]["vendas"] == 5
    assert resultado.iloc[0]["pecas"] == 13
    assert resultado.iloc[0]["atendimentos"] == 25


def test_indicadores_ponderados_time(dados):
    diario, metas, vendedores, _ = dados

    mensal = indicadores_mensais(
        diario, metas, vendedores
    )

    resultado = indicadores_time(mensal)

    time = resultado.iloc[0]

    assert time["ticket_medio"] == pytest.approx(100.0)
    assert time["pa"] == pytest.approx(2.6)
    assert time["conversao"] == pytest.approx(0.2)


def test_atingimento_loja_inclui_gerente(dados):
    diario, _, _, metas_loja = dados

    resultado = atingimento_loja(diario, metas_loja)

    loja = resultado.iloc[0]

    assert loja["valor"] == 600.0
    assert loja["atingimento"] == pytest.approx(0.6)


def test_divisao_por_zero():
    numerador = pd.Series([100.0, 50.0])
    denominador = pd.Series([2.0, 0.0])

    resultado = _div(numerador, denominador)

    assert resultado.iloc[0] == 50.0
    assert pd.isna(resultado.iloc[1])


def test_atingimento_sem_meta(dados):
    diario, _, vendedores, _ = dados

    metas_vazias = pd.DataFrame({
        "vendedor_id": [],
        "mes": [],
        "dias_escalados": [],
        "meta_valor": [],
    })

    resultado = indicadores_mensais(
        diario, metas_vazias, vendedores
    )

    assert resultado["atingimento"].isna().all()
