
import pytest

from src.validador import validar


def test_aceita_texto_sem_problemas():
    texto = "Você atingiu 90% da sua meta."
    numeros_permitidos = [90.0]

    resultado = validar(texto, numeros_permitidos, [])

    assert resultado == []


def test_identifica_numero_nao_permitido():
    texto = "Você atingiu 90% da sua meta e vendeu 150 peças."
    numeros_permitidos = [90.0]

    resultado = validar(texto, numeros_permitidos, [])

    assert resultado != []

def test_identifica_nome_de_colega():
    texto = "Você teve um resultado melhor que Maria."
    numeros_permitidos = []
    nomes_colegas = ["Maria"]

    resultado = validar(texto, numeros_permitidos, nomes_colegas)

    assert resultado != []


def test_aceita_texto_sem_nome_de_colega():
    texto = "Você apresentou uma boa evolução neste mês."
    numeros_permitidos = []
    nomes_colegas = ["Maria"]

    resultado = validar(texto, numeros_permitidos, nomes_colegas)

    assert resultado == []
