# Avaliação arquitetural

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
