"""Roteiro de conversa de feedback, montado só a partir dos fatos de analise.py.

Fluxo: fatos -> rascunho (modelo de texto, sem LLM) -> [opcional] LLM reescreve
com mais naturalidade -> validador -> o gerente edita e aprova.
O LLM nunca calcula nem inventa: se o validador reprovar, volta ao rascunho.
"""
import os

from .validador import validar


MESES = {"08": "agosto", "09": "setembro", "10": "outubro", "11": "novembro"}


def _pct(x):
    return f"{x * 100:.0f}%"


def _num(x):
    return f"{x:.2f}".replace(".", ",")


def _reais(x):
    return "R$ " + f"{x:,.0f}".replace(",", ".")


# --- Blocos de texto: cada um fala de um comportamento observável -------------

def _abertura(d):
    nome = d["nome"].split()[0]
    if d["modo"] == "apoio":
        return (f"{nome}, antes de falar de número: eu soube do que está acontecendo com "
                f"você e quero saber como você está e se precisa de algo de mim.")
    return f"{nome}, queria conversar com calma sobre o seu {MESES[d['mes'][-2:]]}."


def _forcas(d):
    i, t = d["indicadores"], d["time"]
    linhas = []
    if "bateu_meta" in d["forcas"]:
        linhas.append(f"Você chegou a {_pct(i['atingimento'])} da sua meta do mês.")
    if "conversao_acima" in d["forcas"]:
        linhas.append(
            f"Das clientes que você atende, {_pct(i['conversao'])} compram, e a média da "
            f"loja é {_pct(t['conversao'])}. O seu atendimento convence.")
    if "evolucao_conversao" in d["forcas"]:
        s = d["serie_conversao"]
        linhas.append(
            f"Sua conversão foi de {_pct(s[0]['conversao'])} para {_pct(s[-1]['conversao'])} "
            f"nos últimos meses. Isso é evolução sua.")
    if "evolucao_meta" in d["forcas"] and d["anterior_atingimento"] is not None:
        linhas.append(
            f"Sua meta foi de {_pct(d['anterior_atingimento'])} para "
            f"{_pct(i['atingimento'])} de um mês para o outro.")
    ultima = d["ultima_conversa_registrada"]
    if "evolucao_conversao" in d["forcas"] and ultima:
        linhas.append(
            f"Depois da nossa conversa de {ultima['data']:%d/%m} você mudou a "
            f"abordagem. Quero reconhecer isso.")
    return linhas


def _desenvolvimento(d):
    i, t = d["indicadores"], d["time"]
    n = d["nome"].split()[0]
    m = d["micro_meta"]
    linhas = []
    if "pa_baixo" in d["foco"]:
        linhas += [
            f"Cada cliente sua leva em média {_num(i['pa'])} peça por compra; na loja a "
            f"média é {_num(t['pa'])}. Esse é o ponto com mais espaço para crescer, e a "
            f"venda você já sabe fazer.",
            "Para amanhã: depois que a cliente escolher a peça principal, ofereça uma "
            "peça que combine com ela ainda no salão, antes do caixa. Já vi funcionar: "
            "no dia 08/10 a cliente levou o cinto quando ele foi oferecido no caixa. "
            "A diferença é fazer essa oferta de propósito, no seu atendimento.",
            f"Combinado possível: levar o P.A. de {_num(i['pa'])} para {_num(m['pa'])} "
            f"nas próximas 2 semanas. Vamos olhar juntos.",
        ]
    if "conversao_em_queda" in d["foco"]:
        s = d["serie_conversao"]
        linhas += [
            f"Sua conversão veio de {_pct(s[0]['conversao'])} para {_pct(s[-1]['conversao'])} "
            f"em três meses. Quero entender o que você está vendo no salão.",
            "Para amanhã: no primeiro minuto, cumprimente e pergunte o que a cliente "
            "procura, antes de deixá-la olhar sozinha.",
        ]
    if "conversao_baixa" in d["foco"]:
        linhas += [
            f"Das clientes que você atende, {_pct(i['conversao'])} compram, e a média da loja "
            f"é {_pct(t['conversao'])}. Vamos ver onde a venda escapa.",
            "Para amanhã: quando a cliente disser que vai pensar, pergunte o que "
            "faltou e ofereça guardar a peça.",
        ]
    if d["atendimentos_em_queda"] and "conversao_em_queda" in d["foco"]:
        linhas.append("Você também está atendendo menos clientes que antes. Vale "
                      "olharmos juntos como está o seu tempo no salão.")
    if "objecao_preco" in d["foco"]:
        linhas.append(
            "Um ponto para treinarmos juntos: quando a cliente diz que está caro. "
            "Para amanhã, antes de falar de preço, pergunte o que ela valoriza na peça "
            "e mostre o que justifica o valor (tecido, caimento).")
    if "queda_recente" in d["foco"] and d["modo"] != "apoio":
        linhas.append("Seu faturamento caiu em relação ao mês passado. Quero ouvir o "
                      "que você acha que mudou.")
    return linhas


def _ajuda(d):
    if d["contexto"]["novato"]:
        return [f"{d['nome'].split()[0]}, você tem poucos meses de casa. Estou comparando "
                f"você com o seu próprio começo, não com os veteranos."]
    return []


def _pergunta(d):
    n = d["nome"].split()[0]
    if d["modo"] == "apoio":
        return f"{n}, o que posso ajustar na escala ou na rotina para facilitar agora?"
    return f"E você, {n}: como enxerga o seu mês? O que está difícil no dia a dia?"


def _fechamento(d):
    return ("Vamos combinar uma conversa curta daqui a 2 semanas para olharmos "
            "como ficou.")


def montar_rascunho(d: dict) -> dict:
    """Roteiro em blocos (o gerente edita cada bloco)."""
    blocos = {
        "abertura": [_abertura(d)],
        "o_que_reconhecer": _forcas(d) if d["modo"] != "apoio" else [],
        "o_que_desenvolver": [] if d["modo"] == "apoio" else _desenvolvimento(d),
        "contexto": _ajuda(d),
        "pergunta_aberta": [_pergunta(d)],
        "fechamento": [] if d["modo"] == "apoio" else [_fechamento(d)],
    }
    return blocos


def texto_do_roteiro(blocos: dict) -> str:
    ordem = ["abertura", "o_que_reconhecer", "contexto", "o_que_desenvolver",
             "pergunta_aberta", "fechamento"]
    return "\n".join(f for k in ordem for f in blocos[k])


def reescrever_com_llm(texto: str, d: dict):
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        return None
    try:
        import anthropic  # pip install anthropic
        cliente = anthropic.Anthropic(api_key=chave)
        resp = cliente.messages.create(
            model=os.environ.get("MODELO_LLM", "claude-sonnet-4-5"),
            max_tokens=700,
            system=("Você reescreve roteiros de feedback de um gerente de loja para um "
                    "vendedor, em português do Brasil, tom humano e direto. Regras: "
                    "mantenha TODOS os números exatamente como estão; não acrescente "
                    "fatos, números, nomes de colegas nem comparações; sem rótulos "
                    "pessoais; mantenha a ação concreta para amanhã e a pergunta aberta."),
            messages=[{"role": "user", "content": texto}],
        )
        return resp.content[0].text
    except Exception:
        return None


def gerar_feedback(d: dict, nomes_colegas: list = (), usar_llm: bool = False) -> dict:
    """Devolve o roteiro final, já validado. Se o LLM falhar na validação, usa o rascunho."""
    blocos = montar_rascunho(d)
    texto = texto_do_roteiro(blocos)
    origem = "modelo"
    if usar_llm:
        reescrito = reescrever_com_llm(texto, d)
        if reescrito and not validar(reescrito, d["numeros_permitidos"], nomes_colegas):
            texto, origem = reescrito, "llm"
    problemas = validar(texto, d["numeros_permitidos"], nomes_colegas)
    return {"nome": d["nome"], "mes": d["mes"], "modo": d["modo"], "origem": origem,
            "blocos": blocos, "texto": texto, "problemas": problemas,
            "aprovado": not problemas}
