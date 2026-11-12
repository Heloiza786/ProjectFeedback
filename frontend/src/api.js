// Camada fina de chamadas à API. Erros viram exceções com a mensagem do servidor.
async function chamar(url, opcoes) {
  const r = await fetch(url, opcoes);
  const corpo = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = corpo.detail;
    const erro = new Error(typeof d === "string" ? d : d?.mensagem || "Algo deu errado.");
    erro.problemas = d?.problemas || [];
    throw erro;
  }
  return corpo;
}
const post = (url, dados) =>
  chamar(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(dados) });
const enc = encodeURIComponent;

export const api = {
  contexto: () => chamar("/api/contexto"),
  equipe: (mes) => chamar(`/api/gerente/equipe?mes=${mes}`),
  preparo: (nome, mes) => chamar(`/api/gerente/preparo/${enc(nome)}?mes=${mes}`),
  validar: (nome, mes, texto) => post(`/api/gerente/validar/${enc(nome)}`, { texto, mes }),
  enviar: (dados) => post("/api/gerente/enviar", dados),
  paraMim: (mes) => chamar(`/api/gerente/para-mim?mes=${mes}`),
  painel: (nome, mes) => chamar(`/api/vendedor/${enc(nome)}?mes=${mes}`),
  responder: (nome, id, dados) => post(`/api/vendedor/${enc(nome)}/feedbacks/${id}/resposta`, dados),
  reiniciar: () => post("/api/demo/reiniciar", {}),
};
