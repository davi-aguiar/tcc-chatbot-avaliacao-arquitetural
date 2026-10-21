# Árvore de utilidade — plano refinado de avaliação

Versão 1, de 19/10/2026. Base: objetivos, metodologia e árvore preliminar do `PROJETO_DE_PESQUISA.docx`, consultado na pasta superior ao repositório. O documento de pesquisa não é alterado por este plano.

O recorte contempla seis cenários, um por atributo previsto no projeto. Eles combinam execução controlada e inspeção arquitetural; não são seis experimentos de mesma dimensão. C01 permanece encerrado. C02 a C06 são planejamento prospectivo, sem resultados atribuídos nesta etapa.

## Relação com os objetivos

| Objetivo específico do projeto | Entrega correspondente |
|---|---|
| Documentar a arquitetura atual | [Documentação arquitetural](../02-arquitetura.md), conferida contra o código da versão de corte |
| Sistematizar atributos e cenários, incluindo segurança/confidencialidade | Esta árvore, com seis cenários e justificativas de prioridade |
| Aplicar avaliação baseada no ATAM | Protocolos e relatórios por cenário, com evidências e limitações |
| Identificar riscos, sensibilidades e trade-offs e propor melhorias | Síntese conjunta após a avaliação dos seis cenários, distinguindo achados de recomendações |

## Estrutura e prioridades

```text
Utilidade da arquitetura do chatbot híbrido
├── Modificabilidade → C01: incluir serviço por configuração
├── Desempenho → C02: responder e inicializar em ambiente controlado
├── Disponibilidade → C03: preservar navegação diante de falha da geração
├── Testabilidade → C04: exercitar o RAG sem rede ou credenciais reais
├── Confiabilidade → C05: manter respostas ancoradas no contexto
└── Segurança/confidencialidade → C06: limitar dados no envio e nos logs
```

As prioridades de importância retomam a proposta; as dificuldades são estimativas iniciais do autor, com assistência de IA, sujeitas a revisão antes da execução. Não representam votação ou validação por stakeholders. Alta importância indica relação direta com os objetivos ou risco relevante; dificuldade considera preparação, isolamento e análise necessários, não tempo já medido.

| Cenário | Importância | Dificuldade estimada | Justificativa e estado |
|---|---|---|---|
| C01 | Alta | Baixa | Extensão recorrente de serviços; encerrado com ressalvas, sem reclassificação retrospectiva |
| C02 | Alta | Média | Dependência de inferência externa e reconstrução do índice; planejado |
| C03 | Alta | Média | Falha externa pode afetar a continuidade da conversa; planejado |
| C04 | Média | Média | Separação de camadas precisa permitir testes de RAG, além dos testes de navegação; planejado |
| C05 | Alta | Alta | Geração não determinística exige conferir cada resposta contra seu contexto; planejado |
| C06 | Alta | Média | Fluxo externo e persistência podem expor dados além do necessário; planejado |

## C01 — Modificabilidade: inclusão de serviço

| Elemento do cenário | Definição |
|---|---|
| Fonte | Desenvolvedor responsável pela manutenção |
| Estímulo | Solicitação de novo serviço compatível com os mecanismos de menu existentes |
| Ambiente | Desenvolvimento local, dados sintéticos e referência identificada |
| Artefato | JSON de menus e, na variante documental, TXT da base |
| Resposta | Incluir opção, permitir acesso e retorno e preservar os percursos exercitados |
| Medida | Zero Python funcional alterado; mudança restrita a JSON/TXT; testes e percursos previstos aprovados |

**Resultado preservado:** C01-A atendido; C01-B parcialmente atendido na configuração original, com percurso completo demonstrado em ensaio complementar com modelo alternativo. A mudança localizada favorece a modificabilidade; não demonstra esforço nulo. Protocolo e evidências no [resumo do C01](README.md#c01--inclusão-de-serviço-e-modificabilidade).

## C02 — Desempenho: processamento e inicialização

| Elemento do cenário | Definição |
|---|---|
| Fonte | Usuário sintético e operador do sistema |
| Estímulo | Navegação estática, consulta documental pelo menu, pergunta em texto livre e início de processo |
| Ambiente | Uma máquina identificada, requisições sequenciais, sem gateway WhatsApp; modelo disponível identificado e mantido fixo |
| Artefato | ChatService, NLPService e montagem do índice em `setup_system()` |
| Resposta | Concluir os percursos e tornar o retriever utilizável, registrando tempos e falhas |
| Medida | Duração total e de RAG por mensagem; duração das etapas de inicialização; contagens de sucesso e falha separadas |

**Plano mínimo:** selecionar três entradas fixas por percurso (menu estático, consulta de menu e texto livre), executar cinco repetições por entrada, totalizando 45 mensagens medidas, das quais até 30 acionam geração. Preparar e registrar o aquecimento separadamente. Medir três inicializações em processos novos com modelo de embeddings já no cache; uma preparação com download, se ocorrer, fica separada. Fixar perguntas, estado inicial e ordem antes da coleta e informar possível efeito de ordem.

**Julgamento:** análise descritiva, com valores individuais, quantidade, mediana, mínimo e máximo por percurso e entrada. Não atribuir aprovação por “tempo aceitável” sem requisito validado antes da coleta. Falhas permanecem na contagem e não são registradas como respostas rápidas bem-sucedidas. A amostra não sustenta estimativas de cauda, capacidade sob carga ou generalização estatística.

**Evidências previstas:** tabela de medições, logs com durações, inventário do ambiente e parâmetros de modelo/cache. A [instrumentação existente](../12-instrumentacao-e-medicoes.md) mede processamento da aplicação; não mede entrega ao aparelho, nem separa atualmente recuperação e geração dentro do total do RAG. Uma decomposição adicional exige registrar nova instrumentação antes da coleta.

## C03 — Disponibilidade: continuidade após falha externa

| Elemento do cenário | Definição |
|---|---|
| Fonte | Serviço de inferência externo, representado por falhas controladas |
| Estímulo | Timeout, erro de conexão e modelo indisponível durante geração |
| Ambiente | Aplicação já inicializada, banco descartável e sem chamada externa real |
| Artefato | Caminhos de texto livre e de opção de menu com `query`, tratamento de exceções e estado persistido |
| Resposta | Encerrar a mensagem com resposta controlada, permitir `/menu` e continuar navegação estática |
| Medida | Resposta, exceção propagada ou contida, estado, acesso ao menu e nova interação após cada falha |

**Plano mínimo:** três tipos de falha × dois caminhos de chamada × duas repetições, total de 12 casos; cada caso inclui verificação de retomada por `/menu` e acesso/retorno em opção estática. Injetar falha na fronteira do cliente de inferência, preservando o tratamento real do NLPService e ChatService. Não usar um executor que converta a exceção em `None`, pois isso muda o comportamento observado.

**Critério:** atendido no escopo se todos os casos terminarem com resposta controlada, sem encerrar o processo, e a navegação posterior funcionar. Falhas de estado ou retorno implicam resultado parcial ou não atendido, conforme abrangência. Registrar diferenças entre os dois caminhos, mesmo quando ambos permitem recuperação.

**Limites:** erro injetado imediatamente não mede espera por timeout real. Não estima disponibilidade percentual, SLA, recuperação de processo ou comportamento quando o RAG impede a inicialização. O 404 observado no C01 motiva este cenário, mas não substitui sua execução.

## C04 — Testabilidade: RAG sem dependências externas em execução

| Elemento do cenário | Definição |
|---|---|
| Fonte | Desenvolvedor ou pipeline de CI |
| Estímulo | Executar verificações da recuperação e geração sem credenciais e sem acesso à rede |
| Ambiente | Dependências de teste previamente instaladas, cache de modelos vazio e credenciais removidas do processo de teste |
| Artefato | Ingestão, divisão em chunks, indexação/recuperação, composição do prompt e adaptação da resposta |
| Resposta | Testar os componentes reais selecionados com substitutos somente nas fronteiras externas |
| Medida | Etapas realmente exercitadas, alterações necessárias no Python funcional, testes aprovados e tentativas de rede/download |

**Plano mínimo:** verificar ingestão/chunking de documentos sintéticos; indexação e recuperação reais com embeddings determinísticos locais; composição do prompt e processamento real da resposta com cliente gerador substituto. Incluir resposta com contexto, sem contexto e exceção. Bloquear a rede durante a execução para detectar dependências acidentais. Distinguir instalar pacotes de baixar pesos de modelo em tempo de teste.

**Critério:** atendido se os casos definidos puderem executar sem credencial, download de pesos ou rede, preservando os componentes internos sob avaliação e sem alterar Python funcional. Se só a navegação ou um NLP totalmente substituto puder ser testado, o cenário é parcial. Se for necessária refatoração funcional, registrar a limitação da versão avaliada e propor a mudança separadamente.

**Evidências previstas:** matriz componente/teste/substituto, comandos, bloqueio de rede e cobertura separada de `app/` e `api/`. Cobertura descreve linhas exercitadas, não qualidade de resposta. O [CI atual](../../.github/workflows/ci.yml) cobre `api/` e não instala o stack de RAG; seus testes aprovados não comprovam este cenário.

## C05 — Confiabilidade: fidelidade ao contexto documental

| Elemento do cenário | Definição |
|---|---|
| Fonte | Usuário sintético |
| Estímulo | Pergunta respondível, informação ausente e pergunta que pode confundir serviços |
| Ambiente | Base de corte fixa, modelo e parâmetros identificados, consultas sem dados pessoais reais |
| Artefato | Recuperação, prompt, resposta do gerador e tratamento de ausência de contexto |
| Resposta | Responder com fatos sustentados pelo contexto recuperado ou indicar ausência de informação |
| Medida | Presença da fonte esperada, afirmações sustentadas/não sustentadas, abstenção adequada e confusão entre serviços |

**Plano mínimo:** seis perguntas fixadas antes da execução: três respondíveis, duas sobre informações ausentes da base e uma que exija distinguir serviços; duas execuções por pergunta, totalizando 12 respostas. Definir antecipadamente trechos esperados e fatos permitidos. Guardar contexto efetivamente recuperado e resposta de cada execução; não selecionar apenas respostas favoráveis.

**Critério:** atendido apenas na amostra se todas as afirmações factuais forem sustentadas pelo contexto e houver abstenção nos casos sem informação. Registrar separadamente falha de recuperação e falha de geração. Informações corretas na base, mas ausentes do contexto enviado, não contam como ancoragem documental. Resultados mistos são parciais; indisponibilidade que impeça a geração é não avaliada nessa parte.

**Limites:** avaliação de fidelidade documental pelo autor, não validação clínica, experiência do cidadão ou garantia de ausência de alucinação. A resposta única do C01 é evidência daquele percurso, não resultado deste conjunto.

## C06 — Segurança/confidencialidade: fluxo e minimização de dados

| Elemento do cenário | Definição |
|---|---|
| Fonte | Usuário sintético e aplicação |
| Estímulo | Consulta de menu e texto livre contendo nome, identificador e relato de saúde fictícios |
| Ambiente | Cliente de inferência interceptado localmente, sem envio externo dos dados usados na avaliação |
| Artefato | Payload serializado para inferência, contexto, persistência e logs de sucesso/falha |
| Resposta | Restringir o envio ao necessário para responder e evitar duplicação indevida de conteúdo ou exposição de credenciais |
| Medida | Campos que sairiam da aplicação, finalidade técnica declarada, dados persistidos e conteúdo de logs normais e de erro |

**Plano mínimo:** rastrear opção de menu e texto livre até a fronteira HTTP/SDK; capturar o payload montado sem transmiti-lo. Usar marcadores sintéticos distintos para pergunta, nome e identificador. Inspecionar também os logs quando o cliente retorna erro, pois podem seguir outro caminho. Mapear campos em `users`, `messages` e `audit_logs` separadamente do envio externo.

**Critérios técnicos propostos:** identificador do usuário, nome cadastrado e histórico completo não devem ser enviados automaticamente sem necessidade documentada; conteúdo da conversa não deve ser duplicado em logs operacionais; credenciais não devem aparecer em artefatos ou logs. Texto livre pode conter dado de saúde mesmo sem campos extras: sua transmissão deve ser identificada como exposição externa, registrando os controles presentes ou ausentes, sem presumir anonimização. Para cada item, registrar atendido, não atendido ou não avaliado; resultados mistos produzem julgamento parcial do cenário.

**Limites:** inspeção técnica de fluxo e minimização, sem certificação de conformidade jurídica, auditoria completa de segurança ou validação das práticas internas do provedor. O projeto afirma envio de nome e pergunta; isso será verificado no payload, não adotado como resultado. Em particular, receber `user_name` em NLPService não prova envio desse nome ao modelo.

## Regras de execução e julgamento

Antes de cada coleta, criar um protocolo curto com commit de corte, ambiente, entradas, repetições, critérios e localização das evidências. As quantidades acima delimitam um estudo exploratório viável; não constituem cálculo de tamanho amostral nem exigência do ATAM. Alterações no plano devem ser datadas e justificadas antes da coleta afetada.

Aplicar os julgamentos **atendido**, **parcialmente atendido**, **não atendido** e **não avaliado** aos critérios verificáveis, com justificativa. C02 é descritivo enquanto não houver requisito de latência validado. Não converter ausência de execução em aprovação ou falha. Separar a facilidade de implementar um instrumento da qualidade da arquitetura observada.

Identificar separadamente Python funcional, código de avaliação e dados experimentais. Não corrigir a aplicação no meio da coleta e misturar resultados anteriores e posteriores. Se o modelo padrão não estiver disponível, preservar a tentativa e identificar qualquer execução com outro modelo como configuração adaptada. Não assumir que a disponibilidade de um modelo observada no C01 continua válida.

Usar um relatório e um índice curto de evidências por cenário, evitando registros fragmentados sem explicação. Ao final, produzir uma matriz conjunta de decisão arquitetural → evidência → risco/sensibilidade/trade-off → recomendação. Atualização do modelo padrão, revisão de logs e outras correções são propostas de manutenção, não resultados antecipados.

## Sequência proposta

**Etapa anterior às novas execuções:** documentar e revisar as interfaces atuais, seus contratos e dependências, conforme o [levantamento de interfaces](../13-interfaces-e-contratos.md). A versão inicial foi produzida por inspeção; as lacunas registradas orientam os protocolos e não são garantias de comportamento. Fixar a versão de corte antes da coleta. Essa etapa não reabre o C01 nem implica refatoração prévia obrigatória.

1. C02: medições descritivas, aproveitando a instrumentação existente.
2. C03: falhas controladas nos dois caminhos de consulta.
3. C04: isolamento e testabilidade do pipeline de RAG.
4. C05: amostra de fidelidade documental com modelo disponível identificado.
5. C06: rastreamento técnico de dados e logs, sem transmissão dos dados sintéticos ao provedor.
6. Síntese dos seis cenários e recomendações para o TCC.

Este plano refina a proposta para discussão com o orientador; não registra aprovação dele nem de stakeholders. Mantém o recorte de desenvolvimento/teste, sem carga de produção, avaliação clínica ou comparação experimental entre famílias de modelos.
