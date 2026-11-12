import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import Gerente from "./Gerente.jsx";
import Vendedor from "./Vendedor.jsx";

// A visão fica no endereço (#gerente / #vendedor) para trocar rápido na demo.
const lerVisao = () => (location.hash === "#vendedor" ? "vendedor" : "gerente");

export default function App() {
  const [visao, setVisao] = useState(lerVisao());
  const [ctx, setCtx] = useState(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    api.contexto().then(setCtx).catch((e) => setErro(e.message));
    const f = () => setVisao(lerVisao());
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);

  const trocar = (v) => {
    location.hash = v;
    setVisao(v);
  };

  return (
    <div className="app">
      <header className="topo">
        <div className="marca">
          <span className="sol" aria-hidden="true" />
          <div>
            <strong>Copiloto de Feedback</strong>
            <small>{ctx?.loja || "Rede Aurora"}</small>
          </div>
        </div>
        <nav className="visoes" aria-label="Visão">
          <button className={visao === "gerente" ? "ativo" : ""} onClick={() => trocar("gerente")}>
            Gerente
          </button>
          <button className={visao === "vendedor" ? "ativo" : ""} onClick={() => trocar("vendedor")}>
            Vendedor
          </button>
        </nav>
      </header>
      {erro && (
        <p className="erro caixa">
          Não consegui falar com a API ({erro}). Confira se o servidor está rodando: <code>uvicorn src.api:app</code>
        </p>
      )}
      {ctx && (visao === "gerente" ? <Gerente ctx={ctx} /> : <Vendedor ctx={ctx} />)}
    </div>
  );
}
