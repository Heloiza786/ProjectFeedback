
import pandas as pd
import pytest

import src.relatorios as relatorio


@pytest.fixture
def dados():
    return {
        "diario": pd.DataFrame({
            "data": pd.to_datetime(["2026-09-01"]),
            "valor_vendido": [600.0],
        }),
        "metas_loja": pd.DataFrame({
            "mes": ["2026-09"],
            "meta_valor": [1000.0],
        }),
        "anotacoes_gerente": pd.DataFrame({
            "sobre": ["Ana", "Ana", "(time)"],
            "anotacao": [
                "Conversei com Ana sobre a meta",
                "Bom resultado no mês",
                "Combinamos uma reunião",
            ],
        }),
        "anotacoes_regional": pd.DataFrame({
            "data": pd.to_datetime(["2026-09-15"]),
            "anotacao": ["Foi identificado um atrito na equipe"],
        }),
    }


@pytest.fixture
def diagnosticos():
    return [
        {
            "nome": "Ana",
            "modo": "reconhecimento",
            "indicadores": {
                "pa": 2.5,
                "ticket_medio": 100.0,
                "conversao": 0.25,
                "atingimento": 1.2,
            },
            "time": {
                "pa": 2.0,
                "ticket_medio": 90.0,
                "conversao": 0.20,
            },
            "contexto": {
                "ferias": False,
                "dias_ferias": 0,
                "novato": False,
                "meses_de_casa": 12,
                "contexto_pessoal": False,
            },
            "anotacoes": [],
            "foco": [],
        },
        {
            "nome": "Bruno",
            "modo": "desenvolvimento",
            "indicadores": {
                "pa": 1.5,
                "ticket_medio": 80.0,
                "conversao": 0.10,
                "atingimento": 0.7,
            },
            "time": {
                "pa": 2.0,
                "ticket_medio": 90.0,
                "conversao": 0.20,
            },
            "contexto": {
                "ferias": True,
                "dias_ferias": 5,
                "novato": False,
                "meses_de_casa": 8,
                "contexto_pessoal": False,
            },
            "anotacoes": [],
            "foco": ["conversao_em_queda"],
        },
    ]


def test_ficha_vendedor():
    vendedor = {
        "nome": "Ana",
        "mes": "setembro de 2026",
        "modo": "reconhecimento",
        "indicadores": {
            "pa": 2.5,
            "ticket_medio": 100.0,
            "conversao": 0.25,
            "atingimento": 1.2,
        },
        "time": {
            "pa": 2.0,
            "ticket_medio": 90.0,
            "conversao": 0.20,
        },
        "contexto": {
            "ferias": True,
            "dias_ferias": 5,
            "novato": True,
            "meses_de_casa": 2,
            "contexto_pessoal": True,
        },
        "anotacoes": [
            {
                "data": pd.Timestamp("2026-09-10"),
                "texto": "Conversa sobre resultados",
            }
        ],
    }

    resultado = relatorio.ficha_vendedor(vendedor)

    assert "# Ana" in resultado
    assert "reconhecimento" in resultado
    assert "2.50" in resultado
    assert "R$ 100" in resultado
    assert "25%" in resultado
    assert "120%" in resultado
    assert "5 dias de férias" in resultado
    assert "2 meses de casa" in resultado
    assert "situação pessoal" in resultado
    assert "Conversa sobre resultados" in resultado


def test_ficha_sem_contexto_ou_anotacoes():
    vendedor = {
        "nome": "Carlos",
        "mes": "setembro de 2026",
        "modo": "acompanhamento",
        "indicadores": {
            "pa": 2.0,
            "ticket_medio": 100.0,
            "conversao": 0.20,
            "atingimento": None,
        },
        "time": {
            "pa": 2.0,
            "ticket_medio": 90.0,
            "conversao": 0.20,
        },
        "contexto": {
            "ferias": False,
            "dias_ferias": 0,
            "novato": False,
            "meses_de_casa": 12,
            "contexto_pessoal": False,
        },
        "anotacoes": [],
    }

    resultado = relatorio.ficha_vendedor(vendedor)

    assert "Carlos" in resultado
    assert "Atingimento da meta" not in resultado
    assert "Contexto:" not in resultado
    assert "Suas anotações" not in resultado


def test_panorama_do_time(monkeypatch, dados, diagnosticos):
    monkeypatch.setattr(
        relatorio,
        "diagnosticar_todos",
        lambda dados, mes: diagnosticos,
    )

    resultado = relatorio.panorama_do_time(dados, "2026-09")

    assert len(resultado) == 2
    assert resultado[0]["nome"] == "Ana"
    assert resultado[0]["modo"] == "reconhecimento"
    assert resultado[1]["nome"] == "Bruno"
    assert resultado[1]["atingimento"] == 0.7


def test_feedback_para_gerente(monkeypatch, dados, diagnosticos):
    monkeypatch.setattr(
        relatorio,
        "diagnosticar_todos",
        lambda dados, mes: diagnosticos,
    )

    monkeypatch.setattr(
        relatorio,
        "atingimento_loja",
        lambda diario, metas: pd.DataFrame({
            "mes": ["2026-09"],
            "valor": [600.0],
            "meta_valor": [1000.0],
            "atingimento": [0.6],
        }),
    )

    resultado = relatorio.feedback_para_o_gerente(
        dados, "2026-09"
    )

    assert resultado["mes"] == "2026-09"
    assert resultado["loja"]["valor"] == 600.0
    assert resultado["loja"]["meta"] == 1000.0
    assert resultado["loja"]["atingimento"] == 0.6

    assert "Ana" in resultado["vendedores_que_bateram_meta"]
    assert resultado["total_vendedores"] == 2

    assert "Ana" in resultado["com_conversa_registrada"]
    assert "Bruno" in resultado["sem_conversa_registrada"]

    assert "Bruno" in resultado["em_queda_sem_conversa"]

    assert len(resultado["anotacoes_regional"]) == 1
    assert len(resultado["atrito_pendente"]) == 1


def test_feedback_identifica_conversa_do_gerente(
    monkeypatch, dados, diagnosticos
):
    monkeypatch.setattr(
        relatorio,
        "diagnosticar_todos",
        lambda dados, mes: diagnosticos,
    )

    monkeypatch.setattr(
        relatorio,
        "atingimento_loja",
        lambda diario, metas: pd.DataFrame({
            "mes": ["2026-09"],
            "valor": [600.0],
            "meta_valor": [1000.0],
            "atingimento": [0.6],
        }),
    )

    resultado = relatorio.feedback_para_o_gerente(
        dados, "2026-09"
    )

    assert "Ana" in resultado["com_conversa_registrada"]
    assert "Bruno" not in resultado["com_conversa_registrada"]


def test_roteiro_regional(monkeypatch, dados, diagnosticos):
    monkeypatch.setattr(
        relatorio,
        "diagnosticar_todos",
        lambda dados, mes: diagnosticos,
    )

    monkeypatch.setattr(
        relatorio,
        "atingimento_loja",
        lambda diario, metas: pd.DataFrame({
            "mes": ["2026-09"],
            "valor": [600.0],
            "meta_valor": [1000.0],
            "atingimento": [0.6],
        }),
    )

    resultado = relatorio.roteiro_regional_para_diego(
        dados, "2026-09"
    )

    assert "# Roteiro de feedback para o Diego" in resultado
    assert "## O que reconhecer" in resultado
    assert "## O que desenvolver" in resultado
    assert "## Perguntas para ele" in resultado
    assert "## Combinado" in resultado

    assert "60%" in resultado
    assert "Ana" in resultado
    assert "Bruno" in resultado
    assert "atrito" in resultado.lower()


def test_percentual():
    assert relatorio._pct(0.5) == "50%"
    assert relatorio._pct(1.0) == "100%"
    assert relatorio._pct(0.75) == "75%"


@pytest.mark.parametrize(
    "mes, esperado",
    [
        ("2026-08", "agosto de 2026"),
        ("2026-09", "setembro de 2026"),
        ("2026-10", "outubro de 2026"),
        ("2026-11", "novembro de 2026"),
    ],
)
def test_mes_extenso(mes, esperado):
    assert relatorio._mes_extenso(mes) == esperado
