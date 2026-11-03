# Evidências do C02

Instrumento: [executar.py](../c02/executar.py). Entradas fixas: [casos.json](../c02/casos.json). Interpretação e limites: [relatório](../C02-relatorio-execucao.md).

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

Cada lote contém `ambiente.json` e `execucao.json`. Lotes de mensagem com coleta têm `mensagens.json` (inclui aquecimento e auditoria), `medicoes.csv` (somente medidas) e `resumo.json`. Os lotes anteriores ao adendo contêm cópia do protocolo original para conferir o hash registrado.

Na inicialização, `preparacao.json` fica separada de `inicializacao-1.json` a `inicializacao-3.json`. Os arquivos `.log` preservam saída e avisos dos subprocessos. A duração externa inclui importações e consulta de verificação; o tempo de montagem está em `metricas.total_ms`. Nenhuma tentativa anterior é sobrescrita pelo executor.
