import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import { Chip, FOCO, FORCA, MODO, Markdown, REACAO, STATUS, dataBR, dec, mesExtenso, pct, primeiroNome, reais } from "./util.jsx";

export default function Gerente({ ctx }) {
  const [aba, setAba] = useState("equipe");
  const [mes, setMes] = useState(ctx.mes_padrao);
  const [aberto, setAberto] = useState(null);

  return (
    <main className="pagina">
      <div className="barra">
        <div className="abas" role="tablist">
          <button className={aba === "equipe" ? "ativo" : ""} onClick={() => { setAba("equipe"); setAberto(null); }}>
            Minha equipe
          </button>
          <button className={aba === "mim" ? "ativo" : ""} onClick={() => setAba("mim")}>
            Feedback para mim
          </button>
        </div>
        <label className="mes">
          Mês
          <select value={mes} onChange={(e) => { setMes(e.target.value); setAberto(null); }}>
            {ctx.meses.map((m) => (
              <option key={m} value={m}>{mesExtenso(m)}</option>
            ))}
          </select>
        </label>
      </div>
      {aba === "mim" ? (
        <ParaMim mes={mes} />
      ) : aberto ? (
        <Preparar nome={aberto} mes={mes} voltar={() => setAberto(null)} />
      ) : (
        <Equipe mes={mes} abrir={setAberto} />
      )}
    </main>
  );
}

/* ------------------------------------------------------------------ equipe */
function Equipe({ mes, abrir }) {
  const [dados, setDados] = useState(null);
  useEffect(() => { api.equipe(mes).then(setDados); }, [mes]);
  if (!dados) return <p className="carregando">Carregando a equipe…</p>;

  const ordem = { sem_feedback: 0, enviado: 1, respondido: 2 };
  const lista = [...dados.equipe].sort((a, b) => ordem[a.status] - ordem[b.status]);

  return (
    <>
      <section className="resumo">
        <h1>{dados.enviados} de {dados.total} conversas feitas em {mesExtenso(mes)}</h1>
        <p>Comece por quem está sem conversa. Cada cartão mostra o que os números dizem, já com o contexto de cada pessoa.</p>
      </section>
      <div className="grade">
        {lista.map((p) => (
          <button key={p.nome} className="cartao pessoa" onClick={() => abrir(p.nome)}>
            <div className="linha">
              <strong>{p.nome}</strong>
              <Chip classe={STATUS[p.status].classe}>{STATUS[p.status].rotulo}</Chip>
            </div>
            <div className="linha pequeno">
              <Chip classe={MODO[p.modo].classe}>{MODO[p.modo].rotulo}</Chip>
              {p.novato && <Chip classe="info">Novato</Chip>}
            </div>
            <Barra valor={p.atingimento} />
            <div className="numeros">
              <span>Conversão <b>{pct(p.conversao)}</b></span>
              <span>P.A. <b>{dec(p.pa)}</b></span>
            </div>
          </button>
        ))}
      </div>
    </>
  );
}

function Barra({ valor }) {
  if (valor == null) return null;
  return (
    <div className="meta" aria-label={`Meta atingida: ${pct(valor)}`}>
      <div className="trilho">
        <div className={"preench" + (valor >= 1 ? " bateu" : "")} style={{ width: `${Math.min(valor, 1.3) / 1.3 * 100}%` }} />
        <div className="marca100" />
      </div>
      <span>{pct(valor)} da meta</span>
    </div>
  );
}

/* ----------------------------------------------------------------- preparar */
function Preparar({ nome, mes, voltar }) {
  const [p, setP] = useState(null);
  const [texto, setTexto] = useState("");
  const [micro, setMicro] = useState("");
  const [retorno, setRetorno] = useState("");
  const [conf, setConf] = useState({ ok: true, problemas: [], avisos: [] });
  const [envio, setEnvio] = useState({ estado: "pronto", mensagem: "" });
  const tempo = useRef();

  useEffect(() => {
    setP(null);
    api.preparo(nome, mes).then((x) => {
      setP(x);
      setTexto(x.roteiro_texto);
      setMicro(x.micro_meta_sugerida);
      setRetorno(x.retorno_sugerido);
    });
  }, [nome, mes]);

  const conferir = useCallback((t) => {
    clearTimeout(tempo.current);
    tempo.current = setTimeout(() => api.validar(nome, mes, t).then(setConf), 350);
  }, [nome, mes]);
  useEffect(() => { if (p) conferir(texto); }, [texto, p, conferir]);

  if (!p) return <p className="carregando">Preparando a conversa com {primeiroNome(nome)}…</p>;

  const enviar = async () => {
    setEnvio({ estado: "enviando", mensagem: "" });
    try {
      const r = await api.enviar({ nome, mes, texto, micro_meta: micro, retorno });
      setP({ ...p, ja_enviado: r });
      setEnvio({ estado: "pronto", mensagem: "" });
    } catch (e) {
      setConf((c) => ({ ...c, ok: false, problemas: e.problemas?.length ? e.problemas : [e.message] }));
      setEnvio({ estado: "pronto", mensagem: e.message });
    }
  };

  const i = p.indicadores, t = p.time, c = p.contexto;
  const bloqueado = !conf.ok || texto.trim().length < 20 || envio.estado === "enviando";

  return (
    <div className="preparo">
      <button className="voltar" onClick={voltar}>← Equipe</button>
      <div className="duas">
        {/* ------------------------------ o que os números dizem */}
        <section className="cartao">
          <h2>{p.nome} <Chip classe={MODO[p.modo].classe}>{MODO[p.modo].rotulo}</Chip></h2>
          <p className="sub">O que os números dizem sobre {mesExtenso(mes)}</p>
          <table className="tabela">
            <thead><tr><th></th><th>{primeiroNome(p.nome)}</th><th>Time</th></tr></thead>
            <tbody>
              <tr><td>Conversão</td><td><b>{pct(i.conversao)}</b></td><td>{pct(t.conversao)}</td></tr>
              <tr><td>Peças por atendimento</td><td><b>{dec(i.pa)}</b></td><td>{dec(t.pa)}</td></tr>
              <tr><td>Ticket médio</td><td><b>{reais(i.ticket_medio)}</b></td><td>{reais(t.ticket_medio)}</td></tr>
              {i.atingimento != null && (
                <tr><td>Meta atingida</td><td><b>{pct(i.atingimento)}</b></td><td>—</td></tr>
              )}
            </tbody>
          </table>

          {(c.ferias || c.novato || c.contexto_pessoal) && (
            <div className="aviso-contexto">
              <b>Contexto que muda a leitura</b>
              <ul>
                {c.ferias && <li>{c.dias_ferias} dias de férias no mês.</li>}
                {c.novato && <li>{c.meses_de_casa} meses de casa: compare com o começo dele, não com os veteranos.</li>}
                {c.contexto_pessoal && <li>Você anotou uma situação pessoal neste mês. Comece pelo apoio, não pelo número.</li>}
              </ul>
            </div>
          )}

          {p.forcas.length > 0 && (
            <div className="grupo"><h5>Pontos fortes</h5>
              {p.forcas.map((f) => <Chip key={f} classe="ok">{FORCA[f]}</Chip>)}
            </div>
          )}
          {p.foco.length > 0 && (
            <div className="grupo"><h5>Para desenvolver</h5>
              {p.foco.map((f) => <Chip key={f} classe="atencao">{FOCO[f]}</Chip>)}
            </div>
          )}
          {p.anotacoes.length > 0 && (
            <div className="grupo"><h5>Suas anotações do mês</h5>
              <ul className="notas">
                {p.anotacoes.map((n, k) => <li key={k}><time>{dataBR(n.data)}</time> {n.texto}</li>)}
              </ul>
            </div>
          )}
        </section>

        {/* ------------------------------ a conversa */}
        <section className="cartao editor">
          {p.ja_enviado ? (
            <Enviado item={p.ja_enviado} nome={p.nome} editar={() => setP({ ...p, ja_enviado: null })} />
          ) : (
            <>
              <h2>Sua conversa com {primeiroNome(p.nome)}</h2>
              <p className="sub">Este é um ponto de partida montado com os números acima. Reescreva com as suas palavras: a conversa é sua.</p>
              <textarea value={texto} onChange={(e) => setTexto(e.target.value)} rows={14} aria-label="Roteiro da conversa" />
              <div className="acoes-linha">
                <button className="link" onClick={() => setTexto(p.roteiro_texto)}>Voltar à sugestão</button>
              </div>

              <div className={"conferencia " + (conf.ok ? "ok" : "erro")} role="status">
                {conf.ok ? (
                  <span>✓ Os números do texto batem com os dados.</span>
                ) : (
                  <>
                    <b>Não posso enviar assim:</b>
                    <ul>{conf.problemas.map((x, k) => <li key={k}>{x}</li>)}</ul>
                  </>
                )}
              </div>
              {conf.avisos?.length > 0 && (
                <ul className="avisos">{conf.avisos.map((x, k) => <li key={k}>{x}</li>)}</ul>
              )}

              <div className="campos">
                <label>Combinado para as próximas semanas
                  <input value={micro} onChange={(e) => setMicro(e.target.value)} placeholder="Ex.: levar o P.A. de 1,26 para 1,5" />
                </label>
                <label>Conversar de novo em
                  <input type="date" value={retorno} onChange={(e) => setRetorno(e.target.value)} />
                </label>
              </div>
              <button className="primario" disabled={bloqueado} onClick={enviar}>
                {envio.estado === "enviando" ? "Enviando…" : `Enviar para ${primeiroNome(p.nome)}`}
              </button>
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function Enviado({ item, nome, editar }) {
  return (
    <div>
      <h2>Enviado para {primeiroNome(nome)} <Chip classe="ok">{item.resposta ? "Respondido" : "Enviado"}</Chip></h2>
      <p className="sub">Enviado em {dataBR(item.enviado_em.slice(0, 10))}{item.retorno ? ` · conversar de novo em ${dataBR(item.retorno)}` : ""}</p>
      {item.micro_meta && <p className="combinado"><b>Combinado:</b> {item.micro_meta}</p>}
      {item.resposta ? (
        <div className="resposta">
          <b>{primeiroNome(nome)} respondeu: {REACAO[item.resposta.reacao]}</b>
          {item.resposta.texto && <p>“{item.resposta.texto}”</p>}
        </div>
      ) : (
        <p className="sub">Ainda sem resposta.</p>
      )}
      <details><summary>Ver o texto enviado</summary><pre className="texto">{item.texto}</pre></details>
      <button className="link" onClick={editar}>Preparar um novo feedback</button>
    </div>
  );
}

/* -------------------------------------------------------------- para mim */
function ParaMim({ mes }) {
  const [d, setD] = useState(null);
  useEffect(() => { api.paraMim(mes).then(setD); }, [mes]);
  if (!d) return <p className="carregando">Carregando…</p>;
  const f = d.fatos;
  return (
    <div className="duas">
      <section className="cartao">
        <h2>Conversa da Patrícia com você</h2>
        <p className="sub">Roteiro da gerente regional, montado só com o que está nos números e nas anotações das visitas dela.</p>
        <Markdown texto={d.roteiro_md} />
      </section>
      <section className="cartao">
        <h2>O que o seu time disse</h2>
        <p className="sub">Respostas dos vendedores aos feedbacks que você enviou.</p>
        {d.respostas_do_time.length === 0 ? (
          <p className="vazio">Ainda não há respostas. Envie um feedback e peça para a pessoa responder na visão do vendedor.</p>
        ) : (
          <ul className="respostas">
            {d.respostas_do_time.map((r) => (
              <li key={r.id}>
                <b>{r.nome}</b> <Chip classe={r.resposta.reacao === "fez_sentido" ? "ok" : "atencao"}>{REACAO[r.resposta.reacao]}</Chip>
                {r.resposta.texto && <p>“{r.resposta.texto}”</p>}
              </li>
            ))}
          </ul>
        )}
        <h5 className="espaco">Fatos usados</h5>
        <ul className="notas">
          <li>Loja em {pct(f.loja.atingimento)} da meta ({reais(f.loja.valor)} de {reais(f.loja.meta)}).</li>
          <li>{f.vendedores_que_bateram_meta.length} de {f.total_vendedores} vendedores bateram a própria meta.</li>
          <li>Você fez {d.gerente.vendas} vendas no mês, com conversão de {pct(d.gerente.conversao)}.</li>
        </ul>
      </section>
    </div>
  );
}
