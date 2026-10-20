# C01 — Análise dos resultados para o TCC

Texto baseado nas evidências da execução e da retomada de 19/10/2026. O [protocolo](C01-modificabilidade-registro-inicial.md) preserva o planejamento e o [relatório](C01-relatorio-execucao.md) reúne resultados, falhas e condições de reprodução. A coleta foi encerrada com resultado parcial na configuração original e sucesso técnico no ensaio complementar com outro modelo remoto.

## Objetivo e procedimento

O experimento C01 avaliou a modificabilidade do chatbot diante da inclusão de um serviço fictício no menu. A hipótese foi que o interpretador genérico permitiria localizar a mudança na configuração JSON e, no caso da consulta documental, em um arquivo TXT, sem alterar código Python funcional. A avaliação utilizou um cenário de atributo de qualidade inspirado no ATAM, adaptado a um estudo individual, sem constituir aplicação completa do método.

Foram consideradas duas variantes incrementais: C01-A, com descrição estática e navegação de retorno; e C01-B, com uma opção de consulta documental. O ensaio utilizou dados sintéticos, SQLite em memória e execução local, sem gateway WhatsApp. A referência efetivamente executada foi o commit `46b6da2213733a809adfefffecb5336023f4d401`; essa diferença em relação à referência histórica do planejamento foi registrada, e a suíte inicial foi executada novamente.

## Resultados observados

| Indicador | C01-A | C01-B, acumulado |
|---|---|---|
| Arquivos funcionais modificados ou incluídos | 1 JSON | 1 JSON e 1 TXT |
| Arquivos Python funcionais alterados | 0 | 0 |
| Suíte automatizada registrada | 244 aprovados | 244 aprovados |
| Etapas de conversa com NLP substituto | 13 | 18 |
| Consulta encaminhada ao NLP substituto | Nenhuma | Uma, com pergunta e nome sintético conferidos |
| Recuperação vetorial real | Não se aplica | Documento sintético recuperado na primeira posição |
| Geração com modelo real | Não se aplica | Modelo original: HTTP 404; modelo alternativo: resposta gerada e retorno verificado |
| Julgamento | Atendido no escopo local | Parcialmente atendido na configuração original; percurso completo demonstrado com adaptação experimental de modelo |

A suíte inicial registrou 240 testes aprovados. O total de 244 após a inclusão resulta da parametrização já existente para o novo estado, e não da escrita de quatro novos testes. Os percursos verificaram acesso, retorno, entrada inválida, comando `/menu` e um serviço preexistente. As evidências estão nos arquivos [testes A](evidencias-c01/testes-A.txt), [testes B](evidencias-c01/testes-B.txt), [percursos A](evidencias-c01/percursos-A.json) e [percursos B](evidencias-c01/percursos-B.json).

Na variante documental, a ingestão carregou 17 documentos e a indexação produziu 39 chunks. A pergunta configurada no menu recuperou o documento fictício C01 na primeira posição, conforme [registro histórico da recuperação](evidencias-c01/rag-recuperacao-historico.json). A montagem do pipeline registrou 59.422,79 ms nessa execução, incluindo o carregamento de embeddings. Na retomada em outra máquina, o índice manteve essas quantidades e a montagem do ensaio complementar registrou 31.358,45 ms. As condições diferem e não permitem interpretar a diferença como ganho de desempenho ou estimar variabilidade.

A retomada utilizou Python 3.12.10 e `.venv` isolado, com [inventário próprio](evidencias-c01/ambiente-geracao.json). A suíte voltou a registrar [244 testes aprovados em 6,13 s](evidencias-c01/testes-geracao.txt). Com chave configurada, a requisição de geração pelo modelo original `llama-3.3-70b-versatile` retornou HTTP 404, preservado na [tentativa original](evidencias-c01/rag-tentativa-modelo-original.json). A listagem autenticada funcionou, mas não continha esse modelo; isso não comprova sua descontinuação global.

Foi então realizado um ensaio complementar com `openai/gpt-oss-120b`, disponível na conta. A substituição ocorreu somente na memória do processo do instrumento de avaliação, sem editar o código funcional da aplicação. O [registro completo](evidencias-c01/rag-real.json) mostra seis etapas pelo `ChatService`, com geração pelo `NLPService` real e retorno até o menu principal. A resposta explicou corretamente a finalidade experimental, sem inventar atendimento, contato ou orientação clínica. Não explicitou, entretanto, que o serviço é fictício; essa advertência estava presente no menu exibido antes da consulta. O sucesso técnico é condicionado ao modelo alternativo e não equivale à aprovação da configuração original.

## Interpretação arquitetural

Os resultados sustentam a hipótese de localização da mudança para o tipo de extensão exercitado. A inclusão reutilizou os mecanismos existentes de transição de estado e encaminhamento de consulta, sem introduzir condicionais específicos no código Python da aplicação. Isso sugere que a separação entre interpretação e configuração favorece a inclusão de serviços que se ajustam ao modelo atual de menus.

Essa conclusão tem alcance delimitado: o ensaio não avaliou novos tipos de interação, integrações externas adicionais ou regras de negócio que exigissem modificar o interpretador. A fidelidade observada na única resposta gerada com o modelo alternativo não comprova fidelidade geral. A falha do modelo original evidencia que a disponibilidade do serviço remoto também condiciona o funcionamento da extensão documental.

| Aspecto | Evidência e implicação |
|---|---|
| Decisão favorável à modificabilidade | Menus e documentos separados do código; mudança funcional restrita a dois arquivos na variante acumulada |
| Sensibilidade da navegação | Destinos e opções dependem da integridade do JSON; os testes estruturais e de percurso detectam parte dos erros possíveis |
| Sensibilidade da consulta | A opção `query` depende da disponibilidade do documento no índice e do serviço de geração; a recuperação foi verificada separadamente |
| Compromisso operacional | A carga na inicialização simplifica o mecanismo, mas incorporar alterações requer recarregar a configuração e reconstruir o índice; atualização dinâmica não foi demonstrada |
| Dependência externa observada | O modelo original retornou 404; o identificador fixo no código exige manutenção quando deixa de estar acessível |
| Risco residual | Uma resposta fiel foi observada com outro modelo, mas não há avaliação ampla de geração; a advertência de ficção não foi repetida na resposta |

## Limitações e validade

O estudo abrange um serviço sintético, uma consulta documental e percursos selecionados. A execução pelo autor com assistência de IA limita inferências sobre esforço de outro desenvolvedor. Não houve medição separada do tempo de edição, estudo e espera; portanto, os horários e durações disponíveis não medem produtividade humana.

O ambiente inicial Windows com Python 3.12.6 e dependências herdadas e o ambiente da retomada com Python 3.12.10 e dependências isoladas diferem do CI com Python 3.11 e versões fixadas. A preparação exigiu instalação de dependências ausentes. A substituição do modelo limita a comparabilidade com a configuração original. Não foram avaliados produção, qualidade clínica, usuários reais, concorrência ou entrega de mensagens pelo WhatsApp. A aprovação da suíte representa ausência de regressões detectadas nos comportamentos exercitados.

## Fechamento

A inclusão de um serviço compatível com os mecanismos existentes exigiu apenas alterações na configuração JSON e, na variante documental, a adição de um arquivo à base de conhecimento, sem modificar o código Python da aplicação. Esse resultado indica que a arquitetura localiza as alterações e favorece a modificabilidade para esse tipo de manutenção. Permanecem as tarefas de edição, validação e recarga da configuração e, quando aplicável, reconstrução do índice. Como o esforço não foi medido separadamente, não se pode concluir que a manutenção tenha custo nulo nem quantificar a redução de trabalho de um desenvolvedor ou de uma IA.

A coleta do experimento C01 foi concluída e documentada com ressalvas. C01-A foi atendido no escopo local. C01-B foi parcialmente atendido na configuração original: a mudança ficou localizada em JSON e TXT e a recuperação funcionou, mas a geração falhou por indisponibilidade do modelo para a chamada realizada. Um ensaio complementar demonstrou o percurso completo com modelo disponível, sustentando a viabilidade da integração sob essa condição.

O achado favorável à modificabilidade deve ser apresentado junto da dependência operacional do provedor e da limitação da resposta gerada. Como manutenção posterior, recomenda-se permitir configurar o identificador do modelo e verificar sua disponibilidade antes da operação. Essa manutenção não foi aplicada durante o ensaio, para preservar o escopo da mudança funcional.
