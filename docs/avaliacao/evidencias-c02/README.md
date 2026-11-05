# Evidências do C02

## Resultado em resumo

Teste de desempenho com **um usuário por vez**, em 05/11/2026. Cada linha soma cinco repetições de três entradas.

| O que foi testado | Funcionou? | Tempo típico (mediana) | Menor e maior tempo |
|---|---|---|---|
| Navegar pelo menu | 15 de 15 | 0,008 s (7,67 ms) | 0,004 a 0,013 s |
| Consultar documento pelo menu | 15 de 15 | 23,2 s | 2,2 a 26,1 s |
| Perguntar em texto livre | 15 de 15 | 21,3 s | 1,3 a 27,6 s |
| Montar o índice ao iniciar | 3 de 3 | 5,5 s | 4,9 a 7,0 s |
| Modelo padrão do código | 0 de 30 | Sem resposta: modelo inexistente no provedor | — |

**Como ler:**

- As consultas usaram `openai/gpt-oss-120b`, porque o modelo padrão não está mais disponível.
- Tempos acima de 19 s vêm, com alta probabilidade, da espera pelo limite de 8.000 tokens por minuto do provedor. Sem essa espera, as consultas levaram de 1,3 a 4,8 s.
- Todas as 30 consultas medidas ficaram abaixo de 30 s, limite considerado aceitável pelo autor depois da coleta.
- **Este teste não mede usuários simultâneos.** O limite observado comporta menos de três consultas por minuto no total.

Dados por repetição: [medicoes.csv](20261105-093139-mensagens-todos-48d334/medicoes.csv). Análise e limitações: [relatório](../C02-relatorio-execucao.md).

## Índice

Instrumento: [executar.py](../c02/executar.py). Entradas fixas: [casos.json](../c02/casos.json). Interpretação e limites: [relatório](../C02-relatorio-execucao.md).

## Série principal — 05/11/2026, segunda máquina

| Arquivo ou diretório | Finalidade |
|---|---|
| [Preparação](maquina2-preparacao/) | Conferência de hashes e embeddings, versões, testes e listagem de modelos, antes da coleta |
| [Inicialização](20261105-092629-inicializacao-todos-87297f/) | Preparação e três inicializações em processos distintos |
| [Mensagens, modelo padrão](20261105-093054-mensagens-todos-6e6565/) | 9 aquecimentos e 45 medidas; todas as gerações falharam com `NotFoundError` |
| [Mensagens, modelo adaptado](20261105-093139-mensagens-todos-48d334/) | `openai/gpt-oss-120b`; 9 aquecimentos e 45 medidas; resultado principal de RAG |
| [diagnostico-retries.json](diagnostico-retries.json) | Tentativas HTTP, 429 e limites; definido após a coleta, fora da série e das tabelas |
| [validacao-evidencias-maquina2.json](validacao-evidencias-maquina2.json) | Integridade dos hashes, contagens e processos distintos dos novos lotes |

## Série anterior — 03/11/2026, primeira máquina

Preservada sem reclassificação; não somar nem comparar diretamente à série principal.

| Arquivo ou diretório | Finalidade |
|---|---|
| [verificacao-corte.txt](verificacao-corte.txt) | Resumo da validação dos 244 testes antes da coleta |
| [verificacao-instrumento.txt](verificacao-instrumento.txt) | Quatro verificações da classificação do executor; não são medições C02 |
| [validacao-evidencias.json](validacao-evidencias.json) | Integridade dos hashes de corte/instrumentos, contagens e processos distintos |
| [Lote estático](20261103-170404-mensagens-estatico-9fba4b/) | 15 medidas, três aquecimentos, inventário e resumo |
| [Impedimento RAG](20261103-170409-mensagens-rag-722aae/) | Ausência de credencial; nenhuma mensagem medida |
| [Preparação padrão](20261103-170416-inicializacao-todos-044ce8/) | Falha offline antes da série, preservada |
| [diagnostico-cache.txt](diagnostico-cache.txt) | Traceback local da consulta de metadados em modo offline |
| [cache-embeddings.json](cache-embeddings.json) | Revisão, tamanhos e SHA-256 dos arquivos dos pesos locais |
| [Nova série de inicialização](20261103-170640-inicializacao-todos-64f9d8/) | Mesmo modelo, caminho do snapshot local; configuração de carregamento adaptada |

## Conteúdo dos lotes

Cada lote contém `ambiente.json` e `execucao.json`. Lotes de mensagem com coleta têm `mensagens.json` (inclui aquecimento e auditoria), `medicoes.csv` (somente medidas) e `resumo.json`; com RAG, também `modelo.json`. Os lotes de 03/11/2026 contêm cópia do protocolo então vigente para conferir o hash registrado. Os manifestos desses lotes usam fim de linha LF em `casos.json`, `executar.py` e protocolo; o checkout da segunda máquina usa CRLF, conforme [conferência](maquina2-preparacao/hashes-corte.json). Nos lotes de 05/11/2026, os hashes correspondem ao checkout local com CRLF.

Na inicialização, `preparacao.json` fica separada de `inicializacao-1.json` a `inicializacao-3.json`. Os arquivos `.log` preservam saída e avisos dos subprocessos. A duração externa inclui importações e consulta de verificação; o tempo de montagem está em `metricas.total_ms`. Nenhuma tentativa anterior é sobrescrita pelo executor.
