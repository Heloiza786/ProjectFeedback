# Histórico de prompts — Desafio 3: O feedback que ninguém dá

**Ferramenta:** Claude.ai  
**Arquivo:** `chats.md`  
**Período:** 10/11/2026 a 12/11/2026

Este documento registra a utilização de inteligência artificial durante o desenvolvimento do projeto, incluindo planejamento, definição arquitetural, implementação, testes, depuração e integração.

Os prompts foram revisados para apresentar melhor os objetivos técnicos das solicitações, preservando a intenção das interações originais. Portanto, não são transcrições literais de todas as mensagens.

---

## 1. Planejamento e arquitetura

| Etapa | Prompt (solicitação realizada à IA) | Resultado da interação |
|---|---|---|
| 1. Modelagem funcional | Analise o briefing do Desafio 3 e elabore um fluxograma funcional que represente o funcionamento completo da aplicação, desde a importação dos dados até a geração, validação, revisão e disponibilização dos feedbacks para gerentes e vendedores. | Estruturação do fluxo de processamento, análise dos indicadores, identificação de pontos de atenção, geração dos feedbacks e revisão humana. |
| 2. Definição arquitetural | Com base nos requisitos do projeto, elabore um fluxograma da arquitetura da aplicação. Identifique os componentes, suas responsabilidades, as tecnologias mais adequadas e as formas de comunicação entre back-end, inteligência artificial e front-end. Avalie uma arquitetura modular que facilite a manutenção e a evolução do sistema. | Definição de uma arquitetura modular, com Python para processamento, FastAPI para disponibilização dos recursos e React para as interfaces. Separação entre cálculos determinísticos e geração de linguagem natural. |

## 2. Histórico de desenvolvimento

| # | Data/hora | Prompt (solicitação realizada à IA) | Resultado da interação |
|---|---|---|---|
| 1 | 10/11 — 13:23 | Analise o briefing do Desafio 3, identifique os requisitos funcionais e proponha uma solução técnica que utilize análise de dados e inteligência artificial para apoiar a gestão de feedbacks. | Proposta de um copiloto de feedback, com cálculos realizados pelo código e geração textual assistida por IA. |
| 2 | 10/11 — 13:24 | Analise os arquivos CSV disponibilizados, calcule os indicadores individuais e mensais dos vendedores e identifique padrões de desempenho, considerando metas e informações contextuais. | Identificação de diferenças de desempenho, metas e fatores contextuais, incluindo o P.A. da Bianca. |
| 3 | 10/11 — 13:26 | Analise a estrutura atual do meu projeto Python, identifique a responsabilidade de cada módulo e indique quais componentes ainda precisam ser implementados para completar a solução. | Mapeamento dos módulos e identificação de componentes ausentes, como testes, validação e relatórios. |
| 4 | 10/11 — 13:26 | Implemente os módulos necessários para a aplicação, respeitando a arquitetura definida e a separação de responsabilidades. Utilize os dados reais do desafio para verificar as regras de negócio e corrija possíveis inconsistências encontradas durante a execução. | Implementação inicial dos módulos e correção de inconsistências encontradas com os dados reais. |
| 5 | 10/11 — 22:03 | Execute o processamento completo da aplicação com os arquivos CSV, gere os feedbacks individuais dos vendedores e execute os testes automatizados. Verifique se os resultados correspondem aos dados de origem e corrija eventuais divergências. | Geração de oito feedbacks e execução dos testes automatizados. Uma contagem incorreta foi identificada e corrigida. |
| 6 | 10/11 — 22:08 | Informe os comandos necessários para instalar as dependências do projeto, executar o processamento dos dados e rodar a suíte de testes no ambiente Python. | Instruções para instalação de Pandas e Pytest, geração dos resultados e execução dos testes. |
| 7 | 10/11 — 22:09 | Analise o erro apresentado no terminal durante a execução do projeto, identifique sua causa e indique como corrigir o problema de carregamento dos arquivos de entrada. | Identificação de `FileNotFoundError` causado pela ausência dos CSVs no diretório esperado. |
| 8 | 10/11 — 22:10 | Oriente-me na organização dos arquivos CSV, considerando a estrutura de diretórios esperada pelo módulo de carregamento. Indique os caminhos e nomes que devo utilizar. | Orientações para criação e preenchimento da pasta `dados/desafio-3-feedback/`. |
| 9 | 10/11 — 22:11 | Analise o resultado da execução dos testes automatizados e confira os indicadores calculados para verificar se estão consistentes com os dados fornecidos pelo desafio. | Confirmação de oito testes aprovados e conferência dos indicadores de Bianca. |
| 10 | 10/11 — 22:12 | Implemente a integração do back-end com duas interfaces de usuário: uma destinada ao gerente, com recursos de gestão e acompanhamento, e outra destinada aos vendedores, com visualização dos próprios feedbacks. Utilize uma API para a comunicação entre as camadas. | Proposta de API com FastAPI e interface React, com ajustes de apresentação e validação dos textos. |
| 11 | 10/11 — 22:19 | Analise o erro apresentado durante a inicialização do servidor Uvicorn. Verifique os caminhos dos arquivos, as dependências e a configuração necessária para executar a API corretamente. | Identificação de problema relacionado à localização dos arquivos de dados. |
| 12 | 10/11 — 22:28 | Verifique se minha aplicação utiliza algum banco de dados. Explique como os dados estão sendo armazenados atualmente e quais seriam as implicações de utilizar uma solução como SQLite. | Identificação do uso de CSV e JSON, sem banco de dados relacional na implementação atual. |
| 13 | 10/11 — 22:29 | Revise a solução implementada com base nos requisitos do briefing. Identifique funcionalidades ausentes, avalie se os fluxos atendem ao desafio e prepare uma demonstração que apresente o funcionamento da aplicação de ponta a ponta. | Identificação da necessidade de incluir o feedback da regional para o gerente Diego e estruturação do roteiro de demonstração. |
| 14 | 12/11 — 09:29 | Organize meu histórico de utilização de inteligência artificial durante o desenvolvimento. Estruture as interações em ordem cronológica e diferencie as solicitações, as entregas da IA e as decisões tomadas durante a implementação. | Estruturação dos registros de interação e documentação do processo. |

## 3. Decisões técnicas e validações

Durante o desenvolvimento, considerei as seguintes decisões:

- Utilizar Python e Pandas para leitura, tratamento e processamento dos dados.
- Implementar indicadores por meio de funções determinísticas, sem delegar cálculos à IA.
- Considerar férias, tempo de experiência e anotações contextuais na interpretação dos resultados.
- Utilizar Pytest para testes automatizados.
- Implementar validação das respostas geradas para reduzir afirmações sem respaldo nos dados.
- Utilizar FastAPI para disponibilizar os recursos do back-end.
- Desenvolver interfaces React para os perfis de gerente e vendedor.
- Manter a revisão e aprovação humana como parte do fluxo de utilização dos feedbacks.

## 4. Considerações sobre o uso da IA

Utilizei a inteligência artificial como ferramenta de apoio ao desenvolvimento, desde o planejamento da solução até a implementação e a depuração.

Os cálculos, as regras de negócio e a interpretação dos indicadores permaneceram sob responsabilidade do código e foram conferidos com os dados originais. A IA foi utilizada principalmente para auxiliar na construção dos textos de feedback e apoiar tarefas de desenvolvimento.

As sugestões geradas foram analisadas e, quando necessário, corrigidas durante a implementação e os testes.

**Objetivo:** utilizar inteligência artificial de maneira controlada, preservando a rastreabilidade das informações e evitando que conteúdos sem respaldo nos dados sejam apresentados como fatos.