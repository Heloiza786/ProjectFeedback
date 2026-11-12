import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { Chip, REACAO, dataBR, dec, mesExtenso, pct, primeiroNome, reais } from "./util.jsx";

// Visão do vendedor, pensada para celular: só os números dele, o feedback que recebeu e a resposta.
export default function Vendedor({ ctx }) {
  const salvo = (() => { try { return localStorage.getItem("vendedor"); } catch { return null; } })();
  const [nome, setNome] = useState(ctx.vendedores.includes(salvo) ? salvo : "Bianca Rocha");
  const [d, setD] = useState(null);

  const carregar = () => api.painel(nome, ctx.mes_padrao).then(setD);
  useEffect(() => {
    setD(null);
    carregar();
    try { localStorage.setItem("vendedor", nome); } catch { /* sem armazenamento: segue normal */ }
  }, [nome]);

  return (
    <main className="celular-moldura">
      <div className="celular">
        <label className="entrar">
          Entrar como
          <select value={nome} onChange={(e) => setNome(e.target.value)}>
            {ctx.vendedores.map((v) => <option key={v}>{v}</option>)}
          </select>
        </label>
        {!d ? (
          <p className="carregando">Carregando…</p>
        ) : (
          <>
            <h1 className="ola">Oi, {primeiroNome(d.nome)}</h1>
            <p className="sub">Seu mês de {mesExtenso(d.mes)}</p>
            <Feedback d={d} recarregar={carregar} />
            <Numeros d={d} />
          </>
        )}
      </div>
    </main>
  );
}

function Feedback({ d, recarregar }) {
  const fb = d.feedbacks.find((f) => f.mes === d.mes);
  if (!fb) {
    return (
      <section className="cartao vazio-fb">
        <h2>Seu feedback</h2>
        <p>Seu gerente ainda não enviou a conversa de {mesExtenso(d.mes)}. Enquanto isso, veja como você está logo abaixo.</p>
      </section>
    );
  }
  return (
    <section className="cartao fb">
      <h2>Seu feedback <small>de {dataBR(fb.enviado_em.slice(0, 10))}</small></h2>
      <div className="texto-fb">
        {fb.texto.split("\n").filter(Boolean).map((l, k) => <p key={k}>{l}</p>)}
      </div>
      {fb.micro_meta && (
        <div className="combinado">
          <b>Combinado</b>
          <p>{fb.micro_meta}</p>
          {fb.retorno && <small>Vocês conversam de novo em {dataBR(fb.retorno)}.</small>}
        </div>
      )}
      <Resposta nome={d.nome} fb={fb} recarregar={recarregar} />
    </section>
  );
}

function Resposta({ nome, fb, recarregar }) {
  const [reacao, setReacao] = useState("");
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (fb.resposta) {
    return (
      <div className="resposta">
        <b>Você respondeu: {REACAO[fb.resposta.reacao]}</b>
        {fb.resposta.texto && <p>“{fb.resposta.texto}”</p>}
        <small>Seu gerente vê esta resposta.</small>
      </div>
    );
  }
  const enviar = async () => {
    setEnviando(true);
    await api.responder(nome, fb.id, { reacao, texto });
    await recarregar();
    setEnviando(false);
  };
  return (
    <div className="responder">
      <h3>Esse feedback faz sentido para você?</h3>
      <div className="reacoes" role="group">
        {Object.entries(REACAO).map(([k, v]) => (
          <button key={k} className={reacao === k ? "ativo" : ""} onClick={() => setReacao(k)}>{v}</button>
        ))}
      </div>
      <textarea rows={3} value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Quer acrescentar algo? (opcional)" />
      <button className="primario" disabled={!reacao || enviando} onClick={enviar}>Responder ao meu gerente</button>
    </div>
  );
}

/* ----------------------------------------------------------------- números */
function Numeros({ d }) {
  const s = d.serie;
  const metricas = [
    { chave: "atingimento", titulo: "Meta atingida", fmt: pct, time: null },
    { chave: "conversao", titulo: "Conversão", fmt: pct, time: "conversao" },
    { chave: "pa", titulo: "Peças por atendimento", fmt: dec, time: "pa" },
    { chave: "ticket", titulo: "Ticket médio", fmt: reais, time: "ticket" },
  ];
  const parciais = s.filter((x) => x.parcial);
  return (
    <section>
      <h2 className="titulo-sec">Seus números</h2>
      {d.novato && <p className="nota">Você está no começo: compare-se com você mesmo, mês a mês.</p>}
      <div className="metricas">
        {metricas.map((m) => <Metrica key={m.chave} m={m} serie={s} />)}
      </div>
      {parciais.map((x) => (
        <p key={x.mes} className="nota">
          {mesExtenso(x.mes)} aparece com marca vazada: {x.motivo}. Não compare com os outros meses.
        </p>
      ))}
    </section>
  );
}

function Metrica({ m, serie }) {
  const atual = serie[serie.length - 1];
  const validos = serie.filter((x) => !x.parcial && x[m.chave] != null);
  const ant = validos.length >= 2 && validos[validos.length - 1].mes === atual.mes ? validos[validos.length - 2] : null;
  const delta = ant ? atual[m.chave] - ant[m.chave] : null;
  const subiu = delta != null && delta > 0.0001;
  const desceu = delta != null && delta < -0.0001;
  const fmtDelta = () => {
    if (delta == null) return null;
    const abs = Math.abs(delta);
    const n = Math.round(abs * 100);
    const txt = m.fmt === pct ? `${n} ${n === 1 ? "ponto" : "pontos"}` : m.fmt === dec ? dec(abs) : reais(abs);
    return `${subiu ? "↑" : desceu ? "↓" : "="} ${txt} vs. ${ant.mes.slice(5) === "09" ? "setembro" : ant.mes.slice(5) === "08" ? "agosto" : "mês anterior"}`;
  };
  return (
    <div className="metrica">
      <span className="rotulo">{m.titulo}</span>
      <strong>{m.fmt(atual[m.chave])}</strong>
      {fmtDelta() && <span className={"delta " + (subiu ? "sobe" : desceu ? "desce" : "")}>{fmtDelta()}</span>}
      {m.time && <span className="time">Média do time: {m.fmt(atual.time[m.time])}</span>}
      <Linha pontos={serie.map((x) => ({ y: x[m.chave], parcial: x.parcial, mes: x.mes }))} />
    </div>
  );
}

function Linha({ pontos }) {
  const v = pontos.filter((p) => p.y != null);
  if (v.length < 2) return null;
  const ys = v.map((p) => p.y), min = Math.min(...ys), max = Math.max(...ys);
  const L = 120, A = 34, pad = 5;
  const x = (i) => pad + (i * (L - 2 * pad)) / (pontos.length - 1);
  const y = (val) => (max === min ? A / 2 : A - pad - ((val - min) / (max - min)) * (A - 2 * pad));
  const caminho = pontos.map((p, i) => (p.y == null ? null : `${x(i)},${y(p.y)}`)).filter(Boolean).join(" ");
  return (
    <svg className="linha-mini" viewBox={`0 0 ${L} ${A}`} role="img" aria-label="Evolução nos meses">
      <polyline points={caminho} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      {pontos.map((p, i) => p.y != null && (
        <circle key={p.mes} cx={x(i)} cy={y(p.y)} r="3" className={p.parcial ? "pt vazado" : "pt"} />
      ))}
    </svg>
  );
}
