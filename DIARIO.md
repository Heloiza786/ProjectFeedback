# Diário

Uma entrada por dia, com as suas palavras: o que você tentou, o que decidiu e por quê, o que deu errado
e o que aprendeu. Errar faz parte; o que conta é o que você fez com o erro.

## 10-11-2026

- **Tentei: entender como o projeto funcionava e escolher linguagens**
- **Decidi, e por quê:*entendi como funciona e achei ma boa ideia usar python/fastApi e react *
- **Deu errado:**
- **Aprendi:**

## 12/11/2026 — Tratamento, indicadores e relatórios

**Contextualização:** Dediquei mais tempo ao desenvolvimento e avancei na implementação dos módulos de tratamento de dados, indicadores, relatórios e respectivos testes automatizados. Algumas etapas foram realizadas sem registro detalhado das interações.

- **Tentei:** Implementar o tratamento dos dados e criar testes com Pytest para validar as funções e a integração entre os módulos.

- **Problemas encontrados:**

  - `ModuleNotFoundError` ao importar módulos localizados em `src/`.

- **Decidi, e por quê:** Padronizar os imports conforme a estrutura de pacotes do projeto, utilizando `from src.relatorios import ...` nos pontos de entrada e imports relativos entre módulos de `src/`. Também adotei `python -m pytest -v` para executar os testes a partir da raiz do projeto.

- **Deu errado:** As primeiras execuções dos testes falharam devido à resolução incorreta dos módulos e à necessidade de ajustar a estrutura de importação.

- **Aprendi:** A importância da organização de pacotes em Python, da padronização dos imports e dos testes automatizados para identificar falhas de integração e garantir a consistência dos dados.
