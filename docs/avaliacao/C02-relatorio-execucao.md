# C02 — Relatório de execução

Coleta iniciada em 03/11/2026 pelo autor com assistência de IA. Protocolo: [C02](C02-protocolo.md). Evidências: [índice](evidencias-c02/README.md). Estado: **execução parcial; geração real pendente**.

## Corte e validação

O corte é `46a87a7`, versão de `origin/main` conferida com `git fetch origin`; branch `experimento/c02-desempenho`. Python funcional, menus e base documental não foram alterados. Ambiente existente `.venv-c01`, Python 3.12.6 em Windows; inventário, hardware e hashes por lote. Os 244 testes existentes passaram antes da coleta (3,06 s). Quatro verificações do instrumento também passaram: resposta, ausência de contexto, exceção nos dois caminhos e credencial ausente. Seus tempos não compõem o experimento.

## Navegação estática

Lote `20261103-170404-mensagens-estatico-9fba4b`: três mensagens de aquecimento, depois cinco rodadas E1/E2/E3. Todas as 15 mensagens medidas tiveram texto e estado esperados, auditoria de envio e nenhuma chamada NLP. O aquecimento está preservado e excluído dos resumos.

| Caso | Medidas | Sucessos | Mediana (ms) | Mínimo (ms) | Máximo (ms) |
|---|---:|---:|---:|---:|---:|
| E1 — Principal → Agendamento | 5 | 5 | 3,85 | 3,49 | 4,59 |
| E2 — Principal → Serviços | 5 | 5 | 3,52 | 3,45 | 3,66 |
| E3 — Serviços → CEMERF | 5 | 5 | 3,81 | 3,48 | 6,28 |
| Percurso estático | 15 | 15 | 3,68 | 3,45 | 6,28 |

Tempos da instrumentação `duracao_total_ms`; os intervalos externos, que incluem o commit final da auditoria, estão no CSV e JSON. O lote usa SQLite em memória e RAG não carregado. Emissão de logs Python desabilitada pelo instrumento, auditoria real preservada. Não extrapolar esses tempos para PostgreSQL, HTTP, WhatsApp ou aplicação com RAG residente e concorrência.

## Inicialização

A primeira preparação (`20261103-170416-inicializacao-todos-044ce8`) falhou com `OfflineModeIsEnabled`. Não foi contada como inicialização rápida nem substituída silenciosamente. A série de três não chegou a ser iniciada nessa configuração.

O diagnóstico mostrou acesso a `model_info` na etapa de correção de tokenizer da biblioteca Transformers, apesar do cache presente. Os pesos locais foram inventariados, incluindo hashes e revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Um adendo ao protocolo foi registrado antes da nova coleta, usando `EMBEDDINGS_MODEL` como caminho do snapshot do mesmo modelo, sem alterar código funcional ou dependências. Essa configuração de carregamento é adaptada e não demonstra que a resolução pelo identificador remoto funcione offline.

Nova série `20261103-170640-inicializacao-todos-64f9d8`: preparação e três inicializações concluídas, em processos distintos e sem download. Cada inicialização montou 17 documentos/39 chunks e retornou 10 documentos na consulta de verificação.

| Inicialização | Embeddings (ms) | Vetorização/índice (ms) | Total de montagem (ms) |
|---|---:|---:|---:|
| 1 | 1.429,82 | 6.838,83 | 8.278,37 |
| 2 | 1.369,41 | 5.679,45 | 7.061,15 |
| 3 | 1.420,84 | 5.517,80 | 6.947,90 |

Mediana de montagem: **7.061,15 ms**; mínimo 6.947,90 ms; máximo 8.278,37 ms. A preparação separada levou 7.764,00 ms de montagem e não entrou nesse resumo. Os tempos completos dos processos são maiores e estão nos JSONs.

Nessa configuração com pesos em cache, a vetorização/indexação foi mais demorada que o carregamento dos embeddings nas três execuções. A amostra não sustenta a justificativa genérica de que o custo de montagem é dominado por carregar o modelo; isso depende do cache e do ambiente. Não demonstra que persistir o índice seja necessário nem quantifica seu benefício, pois essa alternativa não foi implementada/comparada. Importações também consomem tempo fora de `setup_system()`.

## Geração real e pendências

Lote `20261103-170409-mensagens-rag-722aae`: `GROQ_API_KEY` ausente, zero mensagens medidas. Trata-se de impedimento de preparação, não de 30 falhas de desempenho. As consultas pelo menu e em texto livre continuam **não avaliadas**. Não foi usado substituto como evidência de tempo de RAG e não foi presumida disponibilidade do modelo com base no C01.

Para continuar, configurar a credencial local e executar o lote RAG conforme o protocolo. Preservar a tentativa com modelo padrão; se indisponível, identificar outra configuração antes de nova coleta. O executor identifica ausência de resposta e exceção do NLP mesmo quando o `ChatService` retorna fallback e grava `MESSAGE_SENT`.

## Interpretação e limites

O desenho segue análise descritiva exploratória. Não existe requisito de latência validado para aprovar/reprovar por rapidez. Navegação estática e inicialização com carregamento local adaptado foram concluídas operacionalmente nessa amostra; o cenário completo ainda não foi coletado. Ordem fixa, máquina de uso geral, estado crescente do banco, bibliotecas herdadas e lotes separados limitam a comparação. Não há percentis de cauda, capacidade sob carga, simultaneidade ou validação clínica.
