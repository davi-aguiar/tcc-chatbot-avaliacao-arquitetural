# Avaliação arquitetural

O planejamento geral está na [árvore de utilidade refinada](arvore-de-utilidade.md): seis cenários alinhados ao projeto de pesquisa, com prioridades, critérios e evidências previstas. C01 e C02 estão encerrados com ressalvas; C03 a C06 estão planejados e ainda não executados como cenários próprios.

Antes dos próximos cenários, revisar o [levantamento das interfaces e contratos atuais](../13-interfaces-e-contratos.md), produzido por inspeção do código. Ele identifica as fronteiras e lacunas que devem orientar os protocolos.

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
