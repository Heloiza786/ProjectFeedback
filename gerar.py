"""Gera os feedbacks de todos os vendedores e o roteiro da regional para o Diego.
Uso: python gerar.py [AAAA-MM]   (padrão: último mês completo)
Saída: pasta saida/"""
import sys
from pathlib import Path

from src.analise import diagnosticar_todos
from src.carregar_dados import carregar
from src.feedback import gerar_feedback
from src.relatorios import ficha_vendedor, roteiro_regional_para_diego


def main(mes=None):
    dados = carregar()
    saida = Path("saida")
    saida.mkdir(exist_ok=True)
    nomes = list(dados["vendedores"]["nome"])
    for d in diagnosticar_todos(dados, mes):
        f = gerar_feedback(d, [n for n in nomes if n != d["nome"]])
        status = "aprovado" if f["aprovado"] else "REPROVADO: " + "; ".join(f["problemas"])
        arq = saida / f"feedback_{d['nome'].split()[0].lower()}_{d['mes']}.md"
        arq.write_text(ficha_vendedor(d) + "\n\n## Roteiro da conversa (edite antes de usar)\n\n"
                       + f["texto"] + f"\n\n_Validação: {status}_\n", encoding="utf-8")
        print(f"{arq}  [{status}]")
    arq = saida / "roteiro_regional_para_diego.md"
    arq.write_text(roteiro_regional_para_diego(dados, mes), encoding="utf-8")
    print(arq)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
