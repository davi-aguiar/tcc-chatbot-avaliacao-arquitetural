# C02 — Relatório de execução

Coleta iniciada em 03/11/2026 e refeita em 05/11/2026 pelo autor com assistência de IA. Protocolo: [C02](C02-protocolo.md). Evidências: [índice](evidencias-c02/README.md). Estado: **encerrado com ressalvas; análise descritiva**.

## Síntese

Na série principal (segunda máquina, 05/11/2026), todas as 45 mensagens foram concluídas com o modelo alternativo `openai/gpt-oss-120b`, configuração adaptada. O modelo padrão `llama-3.3-70b-versatile` falhou nas 36 gerações (`NotFoundError`). Três inicializações foram bem-sucedidas.

| Medida | Resultado |
|---|---|
| Navegação estática | 15/15; mediana 7,67 ms |
| Consulta pelo menu | 15/15; mediana 23,19 s (2,17 a 26,15 s) |
| Texto livre | 15/15; mediana 21,34 s (1,32 a 27,57 s) |
| Montagem do índice (`setup_system()`) | 3/3; mediana 5,47 s (4,85 a 7,05 s) |
| Processo completo de inicialização | 27,7 a 37,2 s |

**Os tempos de RAG desta série refletem principalmente a espera imposta pelo limite de uso do provedor, e não a latência da geração.** Por isso, as medianas acima não devem ser citadas como tempo de resposta do modelo; ver [Limite de uso do provedor](#limite-de-uso-do-provedor).

## Corte e ambiente

- Máquina: Windows 11, Intel Core i7-6700, 8 CPUs lógicas, 16 GB, uso geral. Python 3.12.6 em `.venv` isolado; versões seguem o inventário anterior ([adendo](C02-protocolo.md#adendo-de-nova-série-em-outra-máquina--05112026-antes-da-coleta)).
- Python funcional, menus e base têm o conteúdo do corte `46a87a7`. Os novos manifestos citam commits posteriores, que só acrescentam protocolo e evidências: `b009a10` e `f257f9c`.
- 244 testes do projeto e 4 do instrumento passaram antes da coleta.
- Embeddings na mesma revisão da série anterior, com tamanhos e SHA-256 idênticos; `EMBEDDINGS_MODEL` aponta para o snapshot local e a coleta ocorreu offline quanto ao Hub.
- O manifesto do lote `6e6565` registra `git_status` não vazio: o lote de inicialização anterior ainda não estava no commit. Python funcional e instrumentos conferem por hash nos três lotes.

## Mensagens com modelo padrão

Lote `20261105-093054-mensagens-todos-6e6565`, modelo `llama-3.3-70b-versatile`, conforme a configuração do corte. A navegação estática teve 15/15 sucessos (mediana 6,88 ms). As 30 consultas medidas e as 6 de aquecimento falharam com `NotFoundError`, sem geração concluída, em cerca de 0,1 s (externo: 89,72 a 659,66 ms). A listagem da API do provedor no mesmo dia não incluía esse identificador.

Os dois percursos tratam a falha de modo diferente:

| Percurso | Resposta ao usuário | Auditoria | Chamadas (com aquecimento) |
|---|---|---|---|
| Menu RAG | `Desculpe, ocorreu um erro interno.` | `MESSAGE_FAILED` | 18 |
| Texto livre | `Opção inválida...` e menu principal | `MESSAGE_SENT`, com `chamou_rag: true` | 18 |

No texto livre, **a falha de geração não aparece como falha na auditoria**, e o usuário recebe mensagem que atribui o problema à própria entrada. Só o envelope de observação do instrumento distinguiu esses casos. Eles foram contados como falhas neste relatório. A navegação estática permaneceu operante no mesmo processo. O comportamento em falha será aprofundado no C03.

## Mensagens com modelo adaptado

Lote `20261105-093139-mensagens-todos-48d334`, modelo `openai/gpt-oss-120b`, definido no adendo antes da coleta. Temperatura 0,1, 500 tokens, `max_retries` 2; `request_timeout` sem valor definido no cliente LangChain (`modelo.json`). Mesmo processo para estático e RAG, com índice residente. As 54 mensagens (9 de aquecimento e 45 medidas) tiveram sucesso operacional, conforme o critério do protocolo: estado, auditoria, consulta prevista e resposta não vazia. Isso não julga o conteúdo das respostas, escopo do C05.

| Caso | Medidas | Sucessos | Mediana (ms) | Mínimo (ms) | Máximo (ms) |
|---|---:|---:|---:|---:|---:|
| E1 — Principal → Agendamento | 5 | 5 | 7,80 | 7,49 | 10,94 |
| E2 — Principal → Serviços | 5 | 5 | 7,38 | 4,96 | 13,00 |
| E3 — Serviços → CEMERF | 5 | 5 | 8,41 | 3,77 | 10,89 |
| **Percurso estático** | **15** | **15** | **7,67** | **3,77** | **13,00** |
| M1 — Onde agendar | 5 | 5 | 25.067,56 | 2.166,74 | 26.149,80 |
| M2 — Documentos obrigatórios | 5 | 5 | 22.547,43 | 4.693,82 | 23.190,26 |
| M3 — Serviço CEO | 5 | 5 | 23.798,78 | 19.384,70 | 24.909,30 |
| **Consulta pelo menu** | **15** | **15** | **23.190,26** | **2.166,74** | **26.149,80** |
| L1 — Onde agendar | 5 | 5 | 26.011,50 | 4.580,03 | 27.568,70 |
| L2 — Documentos obrigatórios | 5 | 5 | 3.823,01 | 1.320,72 | 25.715,63 |
| L3 — Serviço CEO | 5 | 5 | 18.961,71 | 2.780,89 | 24.300,20 |
| **Texto livre** | **15** | **15** | **21.337,48** | **1.320,72** | **27.568,70** |

Valores de `duracao_total_ms`, obtida antes do commit final da auditoria; `duracao_rag_ms` e intervalos externos estão no CSV e no JSON. Nos percursos com geração, a duração de RAG responde por quase todo o total.

## Limite de uso do provedor

As 30 gerações medidas formaram dois grupos sem valores intermediários: 9 entre 1,3 e 4,8 s, e 21 entre 19,0 e 27,6 s. O instrumento desabilita logs e não registra tentativas HTTP, portanto a série não identifica retries, ao contrário do que o protocolo pedia. Essa lacuna foi percebida durante a coleta.

Para esclarecer a causa, um [diagnóstico](evidencias-c02/diagnostico-retries.json) separado ([script](c02/diagnostico_retries.py)) repetiu as seis consultas duas vezes com o mesmo modelo, sem aquecimento e fora da série. **Esse procedimento foi definido depois da coleta, não integra o protocolo prévio e seus tempos não compõem as tabelas.**

| Diagnóstico | Gerações | Duração total, mediana (mín.–máx.) |
|---|---:|---:|
| Com HTTP 429 seguido de 200 | 8 | 23,36 s (2,84–25,96 s) |
| Sem 429 | 4 | 1,32 s (0,90–4,67 s) |

Os cabeçalhos informaram limite de 8.000 tokens por minuto e `retry-after` de 2 a 25 s. Cada tentativa bem-sucedida levou de 0,71 a 1,35 s (mediana 0,77 s). Nas duas primeiras gerações, o saldo informado caiu 2.866 tokens, o que comporta menos de três consultas por minuto. Os retries internos do SDK absorveram os 429: nenhuma geração do diagnóstico falhou nem precisou de mais de uma repetição.

A atribuição dos 21 tempos longos da série ao mesmo mecanismo é **inferência** apoiada no padrão, no modelo e nas durações equivalentes, não uma observação direta daquele lote. O plano da conta não foi identificado; outro limite produziria outros tempos. Como a espera depende da janela de consumo acumulada, diferenças entre casos (por exemplo, L2 e M3) não devem ser atribuídas às perguntas. O resultado também não permite estimar capacidade sob carga.

## Inicialização

Lote `20261105-092629-inicializacao-todos-87297f`. Preparação e três inicializações em processos distintos, sem download durante a série, com 17 documentos, 39 chunks e 10 documentos na consulta de verificação.

| Inicialização | Embeddings (ms) | Vetorização/índice (ms) | Total de montagem (ms) | Processo completo (ms) |
|---|---:|---:|---:|---:|
| 1 | 1.792,03 | 3.662,04 | 5.468,20 | 34.274 |
| 2 | 2.935,00 | 4.104,28 | 7.049,94 | 27.695 |
| 3 | 1.706,22 | 3.135,86 | 4.853,73 | 37.196 |

Mediana de montagem: **5.468,20 ms**. A preparação separada levou 21.618,48 ms de montagem e 155 s de processo; não entra no resumo.

Vetorização/indexação superou o carregamento dos embeddings nas três execuções, como na série anterior, em outra máquina. Isso não sustenta a justificativa genérica de que o custo é dominado por carregar o modelo, dentro das condições de cache local e deste corpus pequeno. A montagem representa parcela minoritária do processo: o intervalo até a verificação foi de 24,7 a 30,7 s, incluindo importações, montagem e consulta. O instrumento não separa importações da verificação, então a parcela exata de cada uma não foi medida. Persistir o índice não foi implementado nem comparado, e seu benefício não foi quantificado.

## Série anterior — 03/11/2026, primeira máquina

Preservada sem reclassificação, em outra máquina (Windows 10, 8 CPUs lógicas, 16 GB), com Python 3.12.6 e ambiente herdado do sistema. **Não é somada nem comparada diretamente à série principal.**

- Navegação estática em lote isolado, sem RAG carregado (`20261103-170404-mensagens-estatico-9fba4b`): 15/15; mediana 3,68 ms (3,45–6,28 ms).
- Consultas (`20261103-170409-mensagens-rag-722aae`): impedimento por falta de `GROQ_API_KEY`, zero mensagens medidas.
- Preparação de inicialização com identificador remoto (`20261103-170416-inicializacao-todos-044ce8`): falha com `OfflineModeIsEnabled`, apesar do cache presente; diagnóstico em `diagnostico-cache.txt`. A carga por identificador remoto não fica demonstrada como operante offline.
- Inicialização com snapshot local (`20261103-170640-inicializacao-todos-64f9d8`): 3/3; mediana de montagem 7.061,15 ms (6.947,90–8.278,37 ms).

## Interpretação e limites

O C02 é descritivo: não havia requisito validado de latência, logo não há aprovação ou reprovação por rapidez. O que os dados sustentam nesta amostra:

- **Separação de percursos.** A navegação custa milissegundos e não chama o NLP; continuou funcionando com a geração indisponível. As consultas dependem do provedor externo e ficam ordens de grandeza acima.
- **Dependência da inferência externa.** Identificador fixo no código tornou-se inválido e impediu toda geração. A quota de tokens, combinada ao tamanho do contexto enviado, passou a dominar os tempos de resposta sequenciais. Esses são riscos e sensibilidades para a síntese final; as eventuais correções são propostas de manutenção.
- **Observabilidade.** No texto livre, falhas de geração são auditadas como `MESSAGE_SENT`. A duração total registrada não distingue geração de espera por retry.

Limites adicionais: resultados de RAG válidos apenas para o modelo adaptado e o limite de uso observado; nada se conclui sobre o modelo padrão além de sua indisponibilidade. SQLite em memória, chamadas diretas e sequenciais, sem HTTP, WhatsApp ou PostgreSQL. Ordem fixa e estado crescente do banco. Máquina de uso geral com aplicativos abertos; durante o lote adaptado houve uma leitura pontual de progresso do `mensagens.json`, por processo Python separado. Amostra sem percentis de cauda, capacidade sob carga, simultaneidade ou validação clínica.
