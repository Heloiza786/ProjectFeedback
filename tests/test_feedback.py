
from src import feedback


def criar_dados():
    """Dados mínimos para gerar um roteiro de feedback."""
    return {
        "nome": "Ana Souza",
        "mes": "2026-08",
        "modo": "normal",
        "indicadores": {},
        "time": {},
        "forcas": [],
        "serie_conversao": [],
        "anterior_atingimento": None,
        "ultima_conversa_registrada": None,
        "foco": [],
        "micro_meta": {},
        "atendimentos_em_queda": False,
        "contexto": {"novato": False},
        "numeros_permitidos": [2],
    }


def test_montar_rascunho():
    dados = criar_dados()

    blocos = feedback.montar_rascunho(dados)

    assert "abertura" in blocos
    assert "o_que_reconhecer" in blocos
    assert "o_que_desenvolver" in blocos
    assert "pergunta_aberta" in blocos
    assert "fechamento" in blocos


def test_texto_do_roteiro():
    dados = criar_dados()

    blocos = feedback.montar_rascunho(dados)
    texto = feedback.texto_do_roteiro(blocos)

    assert isinstance(texto, str)
    assert "Ana" in texto
    assert len(texto) > 0


def test_feedback_sem_llm(monkeypatch):
    dados = criar_dados()

    monkeypatch.setattr(
        feedback,
        "validar",
        lambda texto, numeros, colegas: []
    )

    resultado = feedback.gerar_feedback(dados)

    assert resultado["origem"] == "modelo"
    assert resultado["aprovado"] is True
    assert resultado["problemas"] == []
    assert resultado["nome"] == "Ana Souza"


def test_feedback_com_llm_aprovada(monkeypatch):
    dados = criar_dados()

    monkeypatch.setattr(
        feedback,
        "reescrever_com_llm",
        lambda texto, d: "Ana, vamos conversar sobre seu mês."
    )

    monkeypatch.setattr(
        feedback,
        "validar",
        lambda texto, numeros, colegas: []
    )

    resultado = feedback.gerar_feedback(
        dados,
        usar_llm=True
    )

    assert resultado["origem"] == "llm"
    assert resultado["aprovado"] is True
    assert resultado["texto"] == "Ana, vamos conversar sobre seu mês."


def test_feedback_volta_ao_modelo_se_llm_for_reprovada(monkeypatch):
    dados = criar_dados()

    monkeypatch.setattr(
        feedback,
        "reescrever_com_llm",
        lambda texto, d: "Versão com informação inventada."
    )

    def validar_simulado(texto, numeros, colegas):
        if texto == "Versão com informação inventada.":
            return ["Informação não permitida."]
        return []

    monkeypatch.setattr(feedback, "validar", validar_simulado)

    resultado = feedback.gerar_feedback(
        dados,
        usar_llm=True
    )

    assert resultado["origem"] == "modelo"
    assert resultado["aprovado"] is True
    assert "informação inventada" not in resultado["texto"]


def test_feedback_modo_apoio(monkeypatch):
    dados = criar_dados()
    dados["modo"] = "apoio"

    monkeypatch.setattr(
        feedback,
        "validar",
        lambda texto, numeros, colegas: []
    )

    resultado = feedback.gerar_feedback(dados)

    assert resultado["aprovado"] is True
    assert resultado["blocos"]["o_que_reconhecer"] == []
    assert resultado["blocos"]["o_que_desenvolver"] == []
    assert resultado["blocos"]["fechamento"] == []
    assert "como você está" in resultado["texto"]
