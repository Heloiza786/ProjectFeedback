"""Relatórios de saída: ficha do vendedor para o Diego e feedback para o próprio Diego."""
import pandas as pd

from .analise import diagnosticar_todos
from .indicadores import atingimento_loja, indicadores_mensais
from .tratamento import foi_conversa, meses_completos


def _pct(x):
    return f"{x * 100:.0f}%"


def _mes_extenso(mes: str) -> str:
    nomes = {"08": "agosto", "09": "setembro", "10": "outubro", "11": "novembro"}
    return f"{nomes.get(mes[-2:], mes)} de {mes[:4]}"


def ficha_vendedor(d: dict) -> str:
    """Resumo de uma página com os fatos que sustentam a conversa."""
    i, t = d["indicadores"], d["time"]
    linhas = [
        f"# {d['nome']} — {d['mes']}",
        f"Modo da conversa: {d['modo']}",
        "",
        "| Indicador | Pessoa | Time |",
        "| --- | --- | --- |",
        f"| P.A. | {i['pa']:.2f} | {t['pa']:.2f} |",
        f"| Ticket médio | R$ {i['ticket_medio']:.0f} | R$ {t['ticket_medio']:.0f} |",
        f"| Conversão | {_pct(i['conversao'])} | {_pct(t['conversao'])} |",
    ]
    if i["atingimento"] is not None:
        linhas.append(f"| Atingimento da meta | {_pct(i['atingimento'])} | — |")
    c = d["contexto"]
    avisos = []
    if c["ferias"]:
        avisos.append(f"{c['dias_ferias']} dias de férias no mês")
    if c["novato"]:
        avisos.append(f"{c['meses_de_casa']} meses de casa")
    if c["contexto_pessoal"]:
        avisos.append("anotação de situação pessoal no mês")
    if avisos:
        linhas += ["", "Contexto: " + "; ".join(avisos) + "."]
    if d["anotacoes"]:
        linhas += ["", "Suas anotações do mês:"]
        linhas += [f"- {n['data']:%d/%m}: {n['texto']}" for n in d["anotacoes"]]
    return "\n".join(linhas)


def panorama_do_time(dados: dict, mes: str = None) -> list:
    return [
        {"nome": d["nome"], "modo": d["modo"],
         "atingimento": d["indicadores"]["atingimento"],
         "pa": d["indicadores"]["pa"], "conversao": d["indicadores"]["conversao"]}
        for d in diagnosticar_todos(dados, mes)
    ]


def feedback_para_o_gerente(dados: dict, mes: str = None) -> dict:
    """Fatos para a regional (Patrícia) dar feedback ao Diego, só com o que está nos dados.
    Não julga: reúne evidências para a conversa."""
    mes = mes or meses_completos(dados["diario"])[-1]
    loja = atingimento_loja(dados["diario"], dados["metas_loja"])
    loja_mes = loja[loja["mes"] == mes].iloc[0]

    diag = diagnosticar_todos(dados, mes)
    bateram = [d["nome"] for d in diag if (d["indicadores"]["atingimento"] or 0) >= 1]
    em_queda = [d["nome"] for d in diag
                if ("conversao_em_queda" in d["foco"] or "queda_recente" in d["foco"])
                and not d["contexto"]["contexto_pessoal"]]  # quem tem situação pessoal é caso de apoio

    # Quem recebeu orientação registrada pelo próprio Diego (anotações com conversa/combinado)
    notas = dados["anotacoes_gerente"]
    com_conversa = sorted({r["sobre"] for _, r in notas.iterrows()
                           if foi_conversa(r["anotacao"]) and r["sobre"] != "(time)"})
    equipe = [d["nome"] for d in diag]
    sem_conversa = [n for n in equipe if n not in com_conversa]
    # Quem está em queda e não tem conversa registrada: ponto de atenção
    queda_sem_conversa = [n for n in em_queda if n not in com_conversa]

    reg = dados["anotacoes_regional"].sort_values("data")
    notas_regional = [{"data": r["data"], "texto": r["anotacao"]} for _, r in reg.iterrows()]

    # Atrito pendente: anotação do Diego/regional que cita dois vendedores
    atrito = [n for n in notas_regional if "atrito" in n["texto"].lower()]

    return {
        "mes": mes,
        "loja": {"atingimento": float(loja_mes["atingimento"]),
                 "valor": float(loja_mes["valor"]),
                 "meta": float(loja_mes["meta_valor"])},
        "vendedores_que_bateram_meta": bateram,
        "total_vendedores": len(equipe),
        "com_conversa_registrada": com_conversa,
        "sem_conversa_registrada": sem_conversa,
        "em_queda_sem_conversa": queda_sem_conversa,
        "anotacoes_regional": notas_regional,
        "atrito_pendente": atrito,
    }


def roteiro_regional_para_diego(dados: dict, mes: str = None) -> str:
    """Roteiro que a Patrícia pode usar com o Diego, montado só com fatos rastreáveis."""
    f = feedback_para_o_gerente(dados, mes)
    n_bateram, n_total = len(f["vendedores_que_bateram_meta"]), f["total_vendedores"]
    linhas = [
        "# Roteiro de feedback para o Diego",
        "",
        "## O que reconhecer",
        f"- A loja fechou {_mes_extenso(f['mes'])} em {_pct(f['loja']['atingimento'])} da meta.",
    ]
    if f["com_conversa_registrada"]:
        linhas.append(
            "- Há conversas de orientação registradas por ele com "
            + ", ".join(f["com_conversa_registrada"])
            + " (a evolução da Tatiane depois da conversa de 10/09 é exemplo do que funciona).")
    linhas += [
        "",
        "## O que desenvolver (com evidência)",
        f"- A loja bateu a meta, mas só {n_bateram} dos {n_total} vendedores bateram a própria.",
    ]
    if f["em_queda_sem_conversa"]:
        linhas.append(
            "- Sem conversa registrada, apesar de queda nos números: "
            + ", ".join(f["em_queda_sem_conversa"]) + ".")
    if f["sem_conversa_registrada"]:
        linhas.append(
            f"- {len(f['sem_conversa_registrada'])} de {n_total} vendedores sem nenhuma conversa "
            "de orientação registrada nas suas anotações.")
    for n in f["anotacoes_regional"]:
        linhas.append(f"- Visita de {n['data']:%d/%m} (Patrícia): {n['texto']}")
    linhas += [
        "",
        "## Perguntas para ele",
        "- Quem precisa de uma conversa esta semana, e o que você vai dizer a cada um?",
        "- O que está te impedindo de fazer a reunião da manhã e de sair do caixa no pico?",
        "- Como posso ajudar com a escala de sábado?",
        "",
        "## Combinado",
        "Definir 1 ação para a semana e a data da próxima conversa.",
    ]
    return "\n".join(linhas)
