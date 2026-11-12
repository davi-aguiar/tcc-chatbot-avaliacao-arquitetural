# Avaliação arquitetural

O planejamento geral está na [árvore de utilidade refinada](arvore-de-utilidade.md): seis cenários alinhados ao projeto de pesquisa, com prioridades, critérios e evidências previstas. C01 a C04 estão encerrados com ressalvas; C05 está em preparação, sem respostas reais coletadas, e C06 permanece planejado.

Antes dos próximos cenários, revisar o [levantamento das interfaces e contratos atuais](../13-interfaces-e-contratos.md), produzido por inspeção do código. Ele identifica as fronteiras e lacunas que devem orientar os protocolos.

## C05 — Fidelidade ao contexto documental

**Estado: preparação iniciada em 12/11/2026; geração e julgamento pendentes.** O [protocolo](C05-protocolo.md) fixa seis perguntas, duas rodadas, fatos esperados e critérios separados de recuperação, geração, abstenção e completude. A preparação local com embeddings semânticos e FAISS reais recuperou as fontes esperadas das seis perguntas e os 15 trechos de referência dos quatro casos respondíveis/distinção. Isso não comprova fidelidade de respostas.

A preparação confirmou que uma seção ambígua do documento do Ambulatório, que pergunta pelo CAPS II e fornece outro endereço, aparece no contexto de P03/P06. A revisão deve distinguir essa inconsistência documental de geração sem apoio. As [evidências de preparação](evidencias-c05/README.md) preservam contexto, fontes e inventário. Nenhuma chave Groq estava configurada; as 12 respostas reais ainda não foram coletadas. As 14 verificações do instrumento passaram separadamente, incluindo SDK com transporte sintético.

## C04 — Testabilidade do núcleo RAG sem rede

**Estado: encerrado com ressalvas em 09/11/2026; critério atendido no recorte.** Os 16 casos exercitaram ingestão, chunking, FAISS, montagem, prompt/parser e NLP reais com embeddings e gerador locais substitutos. Zero tentativas externas, nenhuma credencial, caches de modelos vazios antes/depois e zero Python funcional alterado. Os 244 testes existentes e as 13 verificações do instrumento passaram separadamente.

A cobertura de linhas foi 105/110 (95,45%) em `app/` e 21/520 (4,04%) em `api/`; o lote se concentra no núcleo RAG e no NLPService, sem somar a suíte de navegação. O isolamento exige ajustar `ingestion.__file__` e preencher `CACHED_LLM` no teste, evidenciando acoplamento a detalhes internos. Não houve avaliação de embeddings semânticos ou respostas de modelo real.

O [relatório](C04-relatorio-execucao.md) apresenta resultados e limites; o [protocolo](C04-protocolo.md) fixa os 16 casos, substituições e critérios; o [índice de evidências](evidencias-c04/README.md) localiza corpus, prompts, cobertura e conferência posterior.

## C03 — Disponibilidade após falha e sob concorrência

**Estado: coletas C03-A e C03-B concluídas com ressalvas em 08/11/2026. Há bloqueio sob concorrência; não há aprovação geral de disponibilidade.**

**C03-A — Falhas imediatas sequenciais:** os 12 casos (três tipos × dois percursos × duas repetições) tiveram retorno controlado e estado preservado; as 48 interações de retomada funcionaram sem NLP/SDK adicional. Essa coleta não fez geração real nem mediu mensagens simultâneas.

Pelo menu, o usuário recebe erro interno e a auditoria registra `MESSAGE_FAILED`; em texto livre, recebe opção inválida e a auditoria registra `MESSAGE_SENT`. Continuidade operacional não significa comunicação adequada da falha nem disponibilidade durante espera real por timeout.

**C03-B — Concorrência:** 21 rajadas controladas (104 mensagens de carga) e duas rajadas reais (11 consultas) em servidor HTTP isolado, com um worker. Com dez usuários e provedor real, o menu de outro usuário levou **193,832 s**, a saúde levou **139,729 s** e um cliente excedeu 180 s. As inferências foram serializadas; oito HTTP 429 foram absorvidos por retries. O processo permaneceu vivo e os menus voltaram após drenagem. Isso reproduz bloqueio/timeout, sem determinar a causa exata do incidente anterior relatado pelo autor.

Nenhum Python funcional foi alterado. Os relatórios de [C03-A](C03-relatorio-execucao.md) e [C03-B](C03-B-relatorio-execucao.md) apresentam resultados e limites; os protocolos de [C03-A](C03-protocolo.md) e [C03-B](C03-B-protocolo.md) fixam os recortes; os índices de evidências de [C03-A](evidencias-c03/README.md) e [C03-B](evidencias-c03-b/README.md) localizam registros e instrumentos.

## C02 — Desempenho de processamento e inicialização

**Estado: encerrado com ressalvas em 05/11/2026; análise descritiva, sem aprovação por rapidez.** Coleta sobre o conteúdo do corte `46a87a7`, sem alterações no Python funcional.

| Medida (série principal) | Resultado |
|---|---|
| Navegação estática | 15/15; mediana 7,67 ms |
| Consulta pelo menu, modelo adaptado | 15/15; mediana 23,19 s |
| Texto livre, modelo adaptado | 15/15; mediana 21,34 s |
| Montagem do índice | 3/3; mediana 5,47 s |
| Modelo padrão | 0/30 consultas; `NotFoundError` |

Os tempos de RAG refletem principalmente a espera pelo limite de uso do provedor, não a latência da geração. O [relatório](C02-relatorio-execucao.md) detalha resultados e limites; o [protocolo](C02-protocolo.md) fixa entradas, ordem, aquecimento e critérios; o [índice de evidências](evidencias-c02/README.md) localiza medições e tentativas preservadas.

## C01 — Inclusão de serviço e modificabilidade

**Estado: encerrado com ressalvas em 19/10/2026.** A inclusão de um serviço compatível com os mecanismos existentes ficou restrita ao JSON de menus e, na variante documental, a um TXT, sem alterar Python funcional. Isso favorece a modificabilidade nesse cenário, mas não demonstra ausência de esforço de manutenção.

| Resultado | Julgamento |
|---|---|
| C01-A — Serviço com conteúdo estático | Atendido no escopo local |
| C01-B — Consulta documental, configuração original | Parcialmente atendido; recuperação verificada, geração retornou HTTP 404 |
| Ensaio complementar com modelo alternativo | Percurso completo demonstrado, incluindo geração real e retorno |

## Por onde ler

1. [Análise dos resultados para o TCC](C01-analise-resultados.md): conclusão, interpretação arquitetural e limitações; ponto de partida para a redação acadêmica.
2. [Relatório de execução](C01-relatorio-execucao.md): procedimentos efetivamente realizados, resultados e falhas.
3. [Registro inicial](C01-modificabilidade-registro-inicial.md): hipótese, cenário e critérios definidos antes da execução. O formulário original permanece como registro histórico, não como lista de pendências atuais.
4. [Índice das evidências](evidencias-c01/README.md): explica os arquivos técnicos que sustentam as conclusões.

No corpo do TCC, utilizar a descrição do cenário, uma tabela dos resultados e a discussão das limitações. Os JSONs, saídas de testes e patches ficam como material de apoio no repositório; não precisam ser transcritos integralmente no trabalho.

O fechamento não depende de corrigir o modelo padrão nem de repetir chamadas ao provedor. Uma atualização desse modelo constitui manutenção posterior e deve ser registrada separadamente do C01.
