# Avaliação arquitetural

O planejamento geral está na [árvore de utilidade refinada](arvore-de-utilidade.md): seis cenários alinhados ao projeto de pesquisa, com prioridades, critérios e evidências previstas. C01 a C06 estão encerrados com as ressalvas documentadas em cada cenário.

O [levantamento das interfaces e contratos atuais](../13-interfaces-e-contratos.md) identifica as fronteiras e lacunas usadas nos protocolos e confrontadas com os resultados.

## Síntese arquitetural conjunta

A [matriz de síntese](matriz-sintese-arquitetural.md) reúne 14 achados ligados às decisões D01–D12 e a práticas de curadoria/logging, com evidências de C01–C06. Distingue riscos, evidências favoráveis, sensibilidades indicadas, trade-offs observados/analíticos e aspectos não avaliados. Dez recomendações incluem prioridades propostas e formas de verificar uma manutenção futura.

Os 14 achados foram confirmados pelo autor em revisão assistida na conversa, conforme o [registro de revisão](revisao-matriz.json). As prioridades das dez recomendações continuam propostas e não revisadas; não houve priorização validada com stakeholders, novas coletas ou implementação das recomendações. Os fechamentos e as evidências dos cenários são preservados. A matriz subsidia a discussão e as melhorias no TCC; a articulação com a literatura e a conclusão acadêmica continuam como escrita posterior.

## C06 — Fluxo e minimização de dados

**Estado: encerrado com ressalvas em 14/11/2026; parcialmente atendido no recorte, com revisão interpretativa do autor concluída.** O [protocolo](C06-protocolo.md) foi executado em 14 observações válidas, com 12 pedidos serializados pelo SDK e interceptados localmente, dois controles estáticos e zero tentativas externas. Nenhuma chave real ou envio externo foi usado.

O [relatório](C06-relatorio-execucao.md) registra ausência de nome/identificador cadastrados e histórico nos 12 pedidos, preservação dos dados digitados na pergunta e falha de logs: texto integral em quatro observações D04/D06. Banco, auditoria e logs operacionais são examinados separadamente. O [julgamento final](evidencias-c06/julgamento-final.json) registra a concordância explícita do autor com a síntese e seus limites; a [análise preliminar](evidencias-c06/analise-preliminar.json) conserva seu estado histórico. As 381 verificações estruturais e quatro testes do verificador passaram; o [índice de evidências](evidencias-c06/README.md) conserva também a preparação histórica (13 verificações do instrumento e 244 testes existentes aprovados).

## C05 — Fidelidade ao contexto documental

**Estado: encerrado com ressalvas em 14/11/2026.** As 12 respostas foram revisadas pelo autor: fidelidade atendida apenas na amostra; completude parcial em P06-R1. O [protocolo](C05-protocolo.md) foi executado com embeddings/FAISS reais e modelo alternativo explícito `openai/gpt-oss-120b`. As 14 verificações do instrumento e os 244 testes existentes passaram separadamente; a conferência estrutural mantém 167 verificações aprovadas.

O [julgamento final](evidencias-c05/julgamento-final.json) registra 12 fichas confirmadas, nenhuma revisão pendente, quatro abstenções adequadas e nenhuma afirmação sem apoio ou troca de serviços identificada. A revisão foi assistida e não cega.

A leitura preliminar identificou apoio para as afirmações examinadas, quatro abstenções exatas e nenhuma troca de serviços observada. P06-R1 foi truncada no limite de 500 tokens, apesar de contexto suficiente: 28 fatos esperados presentes, um parcial e um omitido no conjunto. O conflito de endereço do CAPS II permaneceu no contexto, mas o modelo escolheu o documento específico nas duas rodadas. O [relatório](C05-relatorio-execucao.md) apresenta resultados e limites; o [índice de evidências](evidencias-c05/README.md) separa preparação histórica, coleta real, análise preliminar de IA e revisão concluída pelo autor. O julgamento vale somente para a amostra adaptada.

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
