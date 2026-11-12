import React from "react";

export const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
export const dec = (x) => (x == null ? "—" : x.toFixed(2).replace(".", ","));
export const reais = (x) => (x == null ? "—" : "R$ " + Math.round(x).toLocaleString("pt-BR"));
export const NOME_MES = { "08": "agosto", "09": "setembro", "10": "outubro", "11": "novembro" };
export const mesExtenso = (m) => `${NOME_MES[m.slice(5)] || m} de ${m.slice(0, 4)}`;
export const primeiroNome = (n) => n.split(" ")[0];
export const dataBR = (iso) => (iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) : "");

export const MODO = {
  reconhecer: { rotulo: "Reconhecer", classe: "ok" },
  desenvolver: { rotulo: "Desenvolver", classe: "atencao" },
  apoio: { rotulo: "Apoiar", classe: "apoio" },
};
export const STATUS = {
  sem_feedback: { rotulo: "Sem conversa", classe: "neutro" },
  enviado: { rotulo: "Enviado", classe: "ok" },
  respondido: { rotulo: "Respondido", classe: "info" },
};
export const FOCO = {
  pa_baixo: "Cliente leva poucas peças por compra",
  conversao_em_queda: "Conversão caindo há 3 meses",
  conversao_baixa: "Conversão abaixo do time",
  queda_recente: "Faturamento caiu vs. mês anterior",
  objecao_preco: "Trava quando a cliente diz que está caro",
};
export const FORCA = {
  bateu_meta: "Bateu a meta do mês",
  conversao_acima: "Conversão acima do time",
  evolucao_conversao: "Conversão subindo",
  evolucao_meta: "Meta evoluindo",
};
export const REACAO = {
  fez_sentido: "Fez sentido",
  em_parte: "Em parte",
  nao_concordo: "Não concordo",
};

export function Chip({ classe = "neutro", children }) {
  return <span className={`chip ${classe}`}>{children}</span>;
}

// Renderizador mínimo de markdown (títulos ## e listas -), suficiente para o roteiro da regional.
export function Markdown({ texto }) {
  const blocos = [];
  let lista = [];
  const fecha = () => {
    if (lista.length) blocos.push(<ul key={blocos.length}>{lista}</ul>);
    lista = [];
  };
  texto.split("\n").forEach((l, i) => {
    if (l.startsWith("- ")) lista.push(<li key={i}>{l.slice(2)}</li>);
    else {
      fecha();
      if (l.startsWith("## ")) blocos.push(<h4 key={i}>{l.slice(3)}</h4>);
      else if (l.trim() && !l.startsWith("# ")) blocos.push(<p key={i}>{l}</p>);
    }
  });
  fecha();
  return <div className="md">{blocos}</div>;
}
