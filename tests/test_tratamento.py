
import pandas as pd
import pytest

from src.tratamento import (
    adicionar_mes,
    meses_completos,
    periodo_ferias,
    contexto_vendedor,
    anotacoes_da_pessoa,
    tem_contexto_pessoal,
    foi_conversa,
)


def test_adicionar_mes():
    diario = pd.DataFrame({
        "data": pd.to_datetime(["2026-09-05", "2026-10-10"])
    })

    resultado = adicionar_mes(diario)

    assert "mes" in resultado.columns
    assert resultado["mes"].tolist() == ["2026-09", "2026-10"]
    assert "mes" not in diario.columns


def test_meses_completos():
    datas = pd.date_range("2026-09-01", periods=20).tolist()
    datas += [pd.Timestamp("2026-10-01")]

    diario = pd.DataFrame({"data": datas})

    resultado = meses_completos(diario)

    assert resultado == ["2026-09"]


def test_periodo_ferias():
    resultado = periodo_ferias("2026-09-08 a 2026-09-27")

    assert resultado is not None
    assert resultado[0] == pd.Timestamp("2026-09-08")
    assert resultado[1] == pd.Timestamp("2026-09-27")


def test_periodo_ferias_invalido():
    assert periodo_ferias("") is None
    assert periodo_ferias(None) is None
    assert periodo_ferias("2026-09-08") is None


def test_contexto_vendedor():
    vendedores = pd.DataFrame({
        "nome": ["Maria"],
        "ferias_no_periodo": ["2026-09-08 a 2026-09-17"],
        "data_admissao": [pd.Timestamp("2026-08-01")],
        "cargo": ["Vendedora"]
    })

    resultado = contexto_vendedor(
        vendedores, "Maria", "2026-09"
    )

    assert resultado["ferias"] is True
    assert resultado["dias_ferias"] == 10
    assert resultado["novato"] is True
    assert resultado["cargo"] == "Vendedora"


def test_anotacoes_da_pessoa():
    anotacoes = pd.DataFrame({
        "sobre": ["Maria", "Maria", "João"],
        "data": pd.to_datetime([
            "2026-09-10",
            "2026-09-20",
            "2026-09-15"
        ]),
        "anotacao": [
            "Primeira conversa",
            "Segunda conversa",
            "Outra pessoa"
        ]
    })

    resultado = anotacoes_da_pessoa(anotacoes, "Maria")

    assert len(resultado) == 2
    assert resultado[0]["texto"] == "Primeira conversa"
    assert resultado[1]["texto"] == "Segunda conversa"


def test_anotacoes_ate_mes():
    anotacoes = pd.DataFrame({
        "sobre": ["Maria", "Maria"],
        "data": pd.to_datetime([
            "2026-09-10",
            "2026-10-10"
        ]),
        "anotacao": [
            "Anotação de setembro",
            "Anotação de outubro"
        ]
    })

    resultado = anotacoes_da_pessoa(
        anotacoes, "Maria", ate="2026-09"
    )

    assert len(resultado) == 1
    assert resultado[0]["texto"] == "Anotação de setembro"


@pytest.mark.parametrize("texto", [
    "Funcionário internado",
    "Afastamento por cirurgia",
    "Familiar faleceu",
    "Pessoa está doente",
])
def test_tem_contexto_pessoal(texto):
    assert tem_contexto_pessoal(texto) is True


def test_sem_contexto_pessoal():
    assert tem_contexto_pessoal("Bom desempenho no mês") is False


@pytest.mark.parametrize("texto", [
    "Combinamos uma nova meta",
    "Conversei com o vendedor",
    "Combinei uma orientação",
    "Pedi pra melhorar os resultados",
])
def test_foi_conversa(texto):
    assert foi_conversa(texto) is True


def test_nao_foi_conversa():
    assert foi_conversa("Resultado mensal satisfatório") is False
