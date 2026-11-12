"""Diagnóstico por vendedor: regras que escolhem o foco da conversa.

A saída é um dicionário de FATOS (números + contexto). O texto do feedback é
gerado em feedback.py a partir dele, e o validador só aceita números daqui.
"""
from .indicadores import indicadores_mensais, indicadores_time
from .tratamento import (
    anotacoes_da_pessoa, contexto_vendedor, foi_conversa, meses_completos,
    tem_contexto_pessoal,
)

# Limiares das regras (ajuste com o que aprender conversando com gerentes)
DIAS_MIN_MES_VALIDO = 15      # abaixo disso o mês é "parcial" e não entra em comparações
LIM_PA_ABAIXO_TIME = 0.30     # P.A. 0,30 abaixo da média do time
LIM_CONV_ACIMA_TIME = 0.05    # 5 pontos percentuais acima do time = força
LIM_QUEDA_CONV_TOTAL = 0.03   # queda de 3 p.p. ao longo da série = queda
LIM_QUEDA_FATURAMENTO = 0.10  # -10% vs. mês anterior
LIM_EVOLUCAO_CONV = 0.05
LIM_EVOLUCAO_META = 0.05
LIM_QUEDA_ATENDIMENTOS = 0.10


def _linha(df, nome, mes):
    x = df[(df["nome"] == nome) & (df["mes"] == mes)]
    return None if x.empty else x.iloc[0]


def _mes_valido(linha, dados, nome, mes) -> bool:
    if linha is None or linha["dias_trabalhados"] < DIAS_MIN_MES_VALIDO:
        return False
    return not contexto_vendedor(dados["vendedores"], nome, mes)["ferias"]


def diagnosticar(dados: dict, nome: str, mes: str = None) -> dict:
    ind = indicadores_mensais(dados["diario"], dados["metas_vendedor"], dados["vendedores"])
    time = indicadores_time(ind)
    meses = meses_completos(dados["diario"])
    mes = mes or meses[-1]
    atual = _linha(ind, nome, mes)
    if atual is None:
        raise ValueError(f"Sem dados de {nome} em {mes}.")
    t_atual = time[time["mes"] == mes].iloc[0]

    # Série dos últimos meses completos e válidos (exclui mês de férias/parcial)
    candidatos = [m for m in meses if m <= mes][-3:]
    serie = []
    for m in candidatos:
        linha = _linha(ind, nome, m)
        if _mes_valido(linha, dados, nome, m):
            serie.append(linha)
    mes_ant = (__import__("pandas").Timestamp(mes + "-01") - __import__("pandas").offsets.MonthBegin(1)).strftime("%Y-%m")
    linha_ant = _linha(ind, nome, mes_ant)
    anterior = linha_ant if _mes_valido(linha_ant, dados, nome, mes_ant) else None

    ctx = contexto_vendedor(dados["vendedores"], nome, mes)
    notas = anotacoes_da_pessoa(dados["anotacoes_gerente"], nome, ate=mes)
    notas_mes = [n for n in notas if n["data"].strftime("%Y-%m") == mes]
    contexto_pessoal = any(tem_contexto_pessoal(n["texto"]) for n in notas_mes)

    permitidos = []

    def reg(*valores):
        permitidos.extend(float(v) for v in valores if v == v)  # ignora NaN

    reg(atual["pa"], atual["ticket_medio"], atual["conversao"] * 100, atual["valor"],
        atual["atendimentos"], atual["vendas"], atual["pecas"],
        t_atual["pa"], t_atual["ticket_medio"], t_atual["conversao"] * 100)
    if atual["atingimento"] == atual["atingimento"]:
        reg(atual["atingimento"] * 100, atual["meta_valor"])

    # ---- Foco (o que trabalhar) --------------------------------------------
    foco, forcas = [], []
    conv, pa = atual["conversao"], atual["pa"]
    conv_t, pa_t = t_atual["conversao"], t_atual["pa"]

    queda_conv = False
    if len(serie) >= 3:
        c = [s["conversao"] for s in serie[-3:]]
        queda_conv = c[0] > c[1] > c[2] and (c[0] - c[2]) >= LIM_QUEDA_CONV_TOTAL
    if conv >= conv_t and pa <= pa_t - LIM_PA_ABAIXO_TIME:
        foco.append("pa_baixo")
    if queda_conv:
        foco.append("conversao_em_queda")
    elif (conv <= conv_t - LIM_CONV_ACIMA_TIME and atual["atingimento"] < 1
          and not ctx["novato"]):
        foco.append("conversao_baixa")
    if anterior is not None and anterior["valor"] > 0:
        var = atual["valor"] / anterior["valor"] - 1
        if var <= -LIM_QUEDA_FATURAMENTO:
            foco.append("queda_recente")
            reg(abs(var) * 100)

    if ctx["novato"] and any("caro" in n["texto"].lower() for n in notas):
        foco.append("objecao_preco")

    # ---- Forças (o que reconhecer) -----------------------------------------
    if atual["atingimento"] >= 1:
        forcas.append("bateu_meta")
    if conv >= conv_t + LIM_CONV_ACIMA_TIME:
        forcas.append("conversao_acima")
    if len(serie) >= 2:
        ini, fim = serie[0], serie[-1]
        reg(ini["conversao"] * 100, fim["conversao"] * 100)
        if fim["conversao"] - ini["conversao"] >= LIM_EVOLUCAO_CONV:
            forcas.append("evolucao_conversao")
    if anterior is not None and anterior["atingimento"] == anterior["atingimento"]:
        reg(anterior["atingimento"] * 100)
        if atual["atingimento"] - anterior["atingimento"] >= LIM_EVOLUCAO_META:
            forcas.append("evolucao_meta")

    # ---- Detalhes usados no texto ------------------------------------------
    serie_conv = [{"mes": s["mes"], "conversao": float(s["conversao"]),
                   "atendimentos": int(s["atendimentos"])} for s in serie]
    for s in serie_conv:
        reg(s["conversao"] * 100, s["atendimentos"])
    atend_queda = (
        len(serie) >= 2 and serie[0]["atendimentos"] > 0
        and serie[-1]["atendimentos"] / serie[0]["atendimentos"] - 1 <= -LIM_QUEDA_ATENDIMENTOS
    )

    # Micro-metas (também são números permitidos no texto)
    micro = {}
    if "pa_baixo" in foco:
        micro["pa"] = round(float(pa) + 0.2, 1)
        reg(micro["pa"])
    if "conversao_em_queda" in foco or "conversao_baixa" in foco:
        micro["conversao_pct"] = round(float(conv) * 100) + 2
        reg(micro["conversao_pct"])

    combinado = next((n for n in reversed(notas) if foi_conversa(n["texto"])), None)

    if contexto_pessoal:
        modo = "apoio"          # não é hora de cobrar número
    elif foco:
        modo = "desenvolver"
    else:
        modo = "reconhecer"

    return {
        "nome": nome,
        "mes": mes,
        "modo": modo,
        "foco": foco,
        "forcas": forcas,
        "contexto": {**ctx, "contexto_pessoal": contexto_pessoal,
                     "mes_parcial": not _mes_valido(atual, dados, nome, mes)},
        "indicadores": {
            "pa": float(pa), "ticket_medio": float(atual["ticket_medio"]),
            "conversao": float(conv), "valor": float(atual["valor"]),
            "atendimentos": int(atual["atendimentos"]),
            "atingimento": (None if atual["atingimento"] != atual["atingimento"]
                            else float(atual["atingimento"])),
        },
        "time": {"pa": float(pa_t), "ticket_medio": float(t_atual["ticket_medio"]),
                 "conversao": float(conv_t)},
        "anterior_atingimento": (None if anterior is None or anterior["atingimento"] != anterior["atingimento"]
                                 else float(anterior["atingimento"])),
        "serie_conversao": serie_conv,
        "atendimentos_em_queda": bool(atend_queda),
        "micro_meta": micro,
        "anotacoes": notas_mes,
        "ultima_conversa_registrada": combinado,
        "numeros_permitidos": permitidos,
    }


def diagnosticar_todos(dados: dict, mes: str = None) -> list:
    """Diagnóstico de todos os vendedores (sem o gerente)."""
    ind = indicadores_mensais(dados["diario"], dados["metas_vendedor"], dados["vendedores"])
    mes = mes or meses_completos(dados["diario"])[-1]
    nomes = ind[(ind["cargo"] != "gerente") & (ind["mes"] == mes)]["nome"].tolist()
    return [diagnosticar(dados, n, mes) for n in nomes]
