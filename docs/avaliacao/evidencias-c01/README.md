# Evidências do C01

Estes arquivos registram a execução do experimento e permitem conferir as afirmações da [análise para o TCC](../C01-analise-resultados.md). Para acompanhar o resultado, comece pelo [resumo da avaliação](../README.md); a leitura de todos os JSONs é necessária apenas para uma conferência detalhada.

## Evidências principais

| Pergunta | Arquivos | O que demonstram |
|---|---|---|
| O que precisou mudar? | [Patch A](C01-A.patch), [patch incremental B](C01-B-incremental.patch) | Inclusão no JSON e no TXT, sem mudança no Python funcional |
| Os testes passaram? | [Inicial](testes-baseline.txt), [A](testes-A.txt), [B](testes-B.txt), [retomada](testes-geracao.txt) | 240 testes na referência; 244 após inclusão e na retomada |
| A navegação funcionou? | [Percursos A](percursos-A.json), [percursos B](percursos-B.json) | Entradas, estados e saídas com NLP substituto; não comprovam geração real |
| O documento entrou na base e foi recuperado? | [Ingestão](ingestao.json), [recuperação histórica](rag-recuperacao-historico.json) | Carga documental e recuperação vetorial reais |
| Por que o modelo foi substituído no ensaio? | [Tentativa original](rag-tentativa-modelo-original.json), [modelos acessíveis](modelos-groq.json) | Falha de geração com modelo original e listagem da conta na data da consulta |
| A integração completa funcionou com outro modelo? | [Execução real complementar](rag-real.json) | Documentos recuperados, modelo utilizado, resposta e seis etapas do percurso real |

`rag-real.json` mantém o estado técnico `geracao_executada_requer_analise_da_resposta` emitido pelo executor. A análise humana dessa resposta e o julgamento final estão no relatório e na análise para o TCC; o registro bruto foi preservado.

## Ambiente e preparação

| Arquivos | Finalidade |
|---|---|
| [ambiente.json](ambiente.json), [dependencias.json](dependencias.json) | Ambiente da primeira máquina e inventário inicial |
| [baseline.txt](baseline.txt) | Falha inicial de preparação, antes de instalar dependências; não representa falha da inclusão do serviço |
| [pre-requisitos-rag.json](pre-requisitos-rag.json), [instalacao-rag.json](instalacao-rag.json), [dependencias-pos-rag.json](dependencias-pos-rag.json) | Preparação do RAG na primeira máquina e inventário atualizado |
| [ambiente-geracao.json](ambiente-geracao.json) | Ambiente isolado e versões da segunda máquina, utilizada para a geração real |

Os ambientes diferem entre si e do CI. Durações registradas não medem esforço humano nem permitem comparar desempenho diretamente entre máquinas. A chave da API não faz parte das evidências.

## Instrumentos e preservação

[executar.py](executar.py) executa os testes e percursos controlados. [executar_rag.py](executar_rag.py) executa recuperação e, com os argumentos correspondentes, geração real. São instrumentos de avaliação, contabilizados separadamente dos arquivos funcionais da aplicação.

O [relatório](../C01-relatorio-execucao.md#reprodução) contém os comandos e as condições de reprodução. Os executores sobrescrevem resultados; preservar cópias antes de repetir. A recuperação histórica e a tentativa com o modelo original foram guardadas separadamente da execução complementar. O relatório também explica a diferença de tratamento de falhas entre a primeira versão do executor e a versão final.
