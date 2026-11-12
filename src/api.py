"""API do Copiloto de Feedback (Rede Aurora, loja L004).

Duas visões sobre os mesmos dados:
- gerente (Diego): prepara, edita, valida e envia o feedback; vê as respostas; recebe feedback da regional;
- vendedor: vê só o que é dele (seus números, o feedback que o gerente enviou) e responde.

Sem login (o briefing dispensa): a pessoa é escolhida na tela. Mesmo assim o vendedor
só recebe os próprios dados e a média agregada do time, nunca os números de um colega.

Rodar:  uvicorn src.api:app --reload
"""
import json
import threading
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .analise import _mes_valido, diagnosticar
from .carregar_dados import carregar
from .feedback import gerar_feedback
from .indicadores import indicadores_mensais, indicadores_time
from .relatorios import feedback_para_o_gerente, ficha_vendedor, roteiro_regional_para_diego
from .tratamento import contexto_vendedor, meses_completos
from .validador import validar

RAIZ = Path(__file__).resolve().parent.parent
ARQ_ESTADO = RAIZ / "estado" / "feedbacks.json"
DIST = RAIZ / "frontend" / "dist"

app = FastAPI(title="Copiloto de Feedback — Rede Aurora")
_trava = threading.Lock()

DADOS = carregar()
IND = indicadores_mensais(DADOS["diario"], DADOS["metas_vendedor"], DADOS["vendedores"])
TIME = indicadores_time(IND)
MESES = meses_completos(DADOS["diario"])
VENDEDORES = [n for n in DADOS["vendedores"].query("cargo != 'gerente'")["nome"]]
GERENTE = DADOS["vendedores"].query("cargo == 'gerente'")["nome"].iloc[0]
NOMES_TODOS = list(DADOS["vendedores"]["nome"])


# ----------------------------------------------------------------- utilitários
def jf(o):
    """Converte tipos do pandas/numpy para JSON."""
    if isinstance(o, dict):
        return {k: jf(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jf(v) for v in o]
    if isinstance(o, pd.Timestamp):
        return o.strftime("%Y-%m-%d")
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if o != o else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


@lru_cache(maxsize=64)
def _diag(nome: str, mes: str) -> dict:
    return diagnosticar(DADOS, nome, mes)


def _checar(nome: str, mes: str = None) -> str:
    if nome not in VENDEDORES:
        raise HTTPException(404, f"Vendedor não encontrado: {nome}")
    mes = mes or MESES[-1]
    if mes not in MESES:
        raise HTTPException(400, f"Mês inválido: {mes}. Use um destes: {MESES}")
    return mes


def _ler_estado() -> list:
    if not ARQ_ESTADO.exists():
        return []
    return json.loads(ARQ_ESTADO.read_text(encoding="utf-8"))


def _gravar_estado(itens: list) -> None:
    ARQ_ESTADO.parent.mkdir(exist_ok=True)
    ARQ_ESTADO.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")


def _status(item) -> str:
    if item is None:
        return "sem_feedback"
    return "respondido" if item.get("resposta") else "enviado"


def _micro_meta_sugerida(d: dict) -> str:
    m, i = d["micro_meta"], d["indicadores"]
    if "pa" in m:
        de, para = f"{i['pa']:.2f}".replace(".", ","), f"{m['pa']:.1f}".replace(".", ",")
        return f"Levar o P.A. de {de} para {para} em 2 semanas"
    if "conversao_pct" in m:
        return f"Levar a conversão de {i['conversao'] * 100:.0f}% para {m['conversao_pct']}% em 2 semanas"
    return ""


def _mensagens(problemas: list) -> list:
    return problemas  # já estão em português e legíveis


# ----------------------------------------------------------------- geral
@app.get("/api/contexto")
def contexto():
    return {"gerente": GERENTE, "vendedores": VENDEDORES, "meses": MESES,
            "mes_padrao": MESES[-1], "loja": "Aurora Shopping Centro (L004)"}


# ----------------------------------------------------------------- gerente
@app.get("/api/gerente/equipe")
def equipe(mes: str = None):
    mes = mes or MESES[-1]
    estado = _ler_estado()
    itens = []
    for nome in VENDEDORES:
        d = _diag(nome, mes)
        feedback = next((x for x in reversed(estado) if x["nome"] == nome and x["mes"] == mes), None)
        i = d["indicadores"]
        itens.append({"nome": nome, "modo": d["modo"], "foco": d["foco"], "forcas": d["forcas"],
                      "atingimento": i["atingimento"], "pa": i["pa"], "conversao": i["conversao"],
                      "novato": d["contexto"]["novato"], "status": _status(feedback)})
    enviados = sum(1 for x in itens if x["status"] != "sem_feedback")
    return jf({"mes": mes, "equipe": itens, "enviados": enviados, "total": len(itens)})


@app.get("/api/gerente/preparo/{nome}")
def preparo(nome: str, mes: str = None):
    mes = _checar(nome, mes)
    d = _diag(nome, mes)
    outros = [n for n in NOMES_TODOS if n != nome]
    f = gerar_feedback(d, outros)
    resp = {k: v for k, v in d.items() if k not in ("numeros_permitidos",)}
    resp["ficha_md"] = ficha_vendedor(d)
    resp["roteiro"] = f["blocos"]
    resp["roteiro_texto"] = f["texto"]
    resp["problemas"] = f["problemas"]
    resp["micro_meta_sugerida"] = _micro_meta_sugerida(d)
    resp["retorno_sugerido"] = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    estado = _ler_estado()
    resp["ja_enviado"] = next((x for x in reversed(estado) if x["nome"] == nome and x["mes"] == mes), None)
    return jf(resp)


class Texto(BaseModel):
    texto: str
    mes: str | None = None


@app.post("/api/gerente/validar/{nome}")
def validar_texto(nome: str, corpo: Texto):
    """Conferência ao vivo enquanto o Diego edita: o texto continua dele, a checagem é nossa."""
    mes = _checar(nome, corpo.mes)
    d = _diag(nome, mes)
    problemas = validar(corpo.texto, d["numeros_permitidos"], [n for n in NOMES_TODOS if n != nome])
    avisos = []
    baixo = corpo.texto.lower()
    if d["modo"] != "apoio" and "amanhã" not in baixo:
        avisos.append("Falta uma ação concreta para amanhã (o que a pessoa vai fazer diferente?).")
    if d["modo"] != "apoio" and "?" not in corpo.texto:
        avisos.append("Falta uma pergunta aberta: deixe a pessoa falar também.")
    return {"ok": not problemas, "problemas": _mensagens(problemas), "avisos": avisos}


class Envio(BaseModel):
    nome: str
    mes: str
    texto: str
    micro_meta: str = ""
    retorno: str = ""


@app.post("/api/gerente/enviar")
def enviar(corpo: Envio):
    mes = _checar(corpo.nome, corpo.mes)
    if len(corpo.texto.strip()) < 20:
        raise HTTPException(400, "O feedback está vazio ou curto demais.")
    d = _diag(corpo.nome, mes)
    outros = [n for n in NOMES_TODOS if n != corpo.nome]
    problemas = validar(corpo.texto + "\n" + corpo.micro_meta, d["numeros_permitidos"], outros)
    if problemas:
        raise HTTPException(422, {"mensagem": "O texto não passou na conferência.", "problemas": problemas})
    item = {"id": uuid.uuid4().hex[:8], "nome": corpo.nome, "mes": mes, "texto": corpo.texto.strip(),
            "micro_meta": corpo.micro_meta.strip(), "retorno": corpo.retorno,
            "enviado_em": datetime.now().isoformat(timespec="minutes"), "resposta": None}
    with _trava:
        estado = _ler_estado()
        estado.append(item)
        _gravar_estado(estado)
    return item


@app.get("/api/gerente/respostas")
def respostas():
    """O que o time respondeu: o gerente também recebe feedback."""
    itens = [x for x in _ler_estado() if x.get("resposta")]
    return {"respostas": list(reversed(itens))}


@app.get("/api/gerente/para-mim")
def para_mim(mes: str = None):
    """Feedback da regional (Patrícia) para o Diego, só com fatos rastreáveis."""
    mes = mes or MESES[-1]
    fatos = feedback_para_o_gerente(DADOS, mes)
    ind = IND[(IND["nome"] == GERENTE) & (IND["mes"] == mes)].iloc[0]
    return jf({"mes": mes, "roteiro_md": roteiro_regional_para_diego(DADOS, mes), "fatos": fatos,
               "respostas_do_time": list(reversed([x for x in _ler_estado() if x.get("resposta")])),
               "gerente": {"nome": GERENTE, "vendas": int(ind["vendas"]), "pa": float(ind["pa"]),
                           "conversao": float(ind["conversao"])}})


# ----------------------------------------------------------------- vendedor
@app.get("/api/vendedor/{nome}")
def painel_vendedor(nome: str, mes: str = None):
    """Painel do vendedor: só os dados dele + média agregada do time."""
    mes = _checar(nome, mes)
    meses = [m for m in MESES if m <= mes]
    serie = []
    for m in meses:
        linha = IND[(IND["nome"] == nome) & (IND["mes"] == m)]
        if linha.empty:
            continue
        r = linha.iloc[0]
        ctx = contexto_vendedor(DADOS["vendedores"], nome, m)
        parcial = not _mes_valido(r, DADOS, nome, m)
        motivo = ("férias no mês" if ctx["ferias"] else "mês incompleto") if parcial else ""
        t = TIME[TIME["mes"] == m].iloc[0]
        serie.append({"mes": m, "pa": r["pa"], "ticket": r["ticket_medio"], "conversao": r["conversao"],
                      "atingimento": r["atingimento"], "parcial": parcial, "motivo": motivo,
                      "time": {"pa": t["pa"], "ticket": t["ticket_medio"], "conversao": t["conversao"]}})
    ctx = contexto_vendedor(DADOS["vendedores"], nome, mes)
    meus = [x for x in _ler_estado() if x["nome"] == nome]
    return jf({"nome": nome, "mes": mes, "serie": serie, "novato": ctx["novato"],
               "feedbacks": list(reversed(meus))})


class Resposta(BaseModel):
    reacao: str  # "fez_sentido" | "em_parte" | "nao_concordo"
    texto: str = ""


@app.post("/api/vendedor/{nome}/feedbacks/{id_fb}/resposta")
def responder(nome: str, id_fb: str, corpo: Resposta):
    if corpo.reacao not in ("fez_sentido", "em_parte", "nao_concordo"):
        raise HTTPException(400, "Reação inválida.")
    with _trava:
        estado = _ler_estado()
        item = next((x for x in estado if x["id"] == id_fb and x["nome"] == nome), None)
        if item is None:
            raise HTTPException(404, "Feedback não encontrado.")
        item["resposta"] = {"reacao": corpo.reacao, "texto": corpo.texto.strip(),
                            "em": datetime.now().isoformat(timespec="minutes")}
        _gravar_estado(estado)
    return item


@app.post("/api/demo/reiniciar")
def reiniciar():
    """Zera os feedbacks enviados (útil antes de gravar a demo)."""
    with _trava:
        _gravar_estado([])
    return {"ok": True}


# ----------------------------------------------------------------- front (build)
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{caminho:path}")
    def front(caminho: str):
        arq = DIST / caminho
        return FileResponse(arq if caminho and arq.is_file() else DIST / "index.html")
