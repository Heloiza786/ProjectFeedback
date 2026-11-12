"""Leitura dos CSVs do Desafio 3 (loja do Diego, L004)."""
from pathlib import Path

import pandas as pd

PASTA_PADRAO = Path(__file__).resolve().parent.parent / "dados" / "desafio-3-feedback"

ARQUIVOS = {
    "vendedores": ("vendedores.csv", ["data_admissao", "no_cargo_desde"]),
    "diario": ("indicadores_diarios_vendedor.csv", ["data"]),
    "metas_vendedor": ("metas_vendedor.csv", []),
    "metas_loja": ("metas_loja.csv", []),
    "anotacoes_gerente": ("anotacoes_gerente.csv", ["data"]),
    "anotacoes_regional": ("anotacoes_regional.csv", ["data"]),
}


def carregar(pasta=None) -> dict:
    """Devolve um dicionário com um DataFrame por arquivo."""
    pasta = Path(pasta) if pasta else PASTA_PADRAO
    dados = {}
    for chave, (arquivo, datas) in ARQUIVOS.items():
        caminho = pasta / arquivo
        if not caminho.exists():
            raise FileNotFoundError(
                f"Não encontrei {caminho}. Confira se os CSVs estão em {pasta}."
            )
        dados[chave] = pd.read_csv(caminho, parse_dates=datas)
    return dados
