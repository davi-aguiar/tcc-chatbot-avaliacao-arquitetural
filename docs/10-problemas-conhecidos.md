# 10 — Problemas conhecidos e limitações abertas

Revisão em 08/11/2026, sobre `65e28a0`, após C01–C03. O conteúdo funcional permanece igual ao corte `666b601`. Os itens distinguem implementação inspecionada, problemas observados e funcionalidades ausentes; não atribuem intenção histórica sem registro. Nenhuma correção funcional foi aplicada nesta revisão.

## 1. Operações síncronas bloqueiam outras requisições

As [rotas](../api/routes/), o [ChatService](../api/services/chat_service.py) e o [pipeline](../app/core/rag_pipeline.py) executam banco/RAG síncronos dentro do fluxo assíncrono; Evolution também envia via `requests.post` síncrono. Não há fila de processamento ou consumidores separados implementados.

[C03-B](avaliacao/C03-B-relatorio-execucao.md) reproduziu o bloqueio em um worker: na rajada real de dez usuários, o menu de outro usuário levou 193,832 s e um cliente excedeu 180 s. O processo permaneceu vivo e os menus voltaram após drenagem. Isso demonstra espera/bloqueio naquele ambiente, sem provar a causa exata do incidente anterior ou um limite fixo de usuários em produção. RabbitMQ permanece hipótese de manutenção, sem comparação implementada.

## 2. Configuração fixa de inferência e dependência de quota

[get_llm](../app/core/rag_pipeline.py) mantém `llama-3.3-70b-versatile` fixo e não explicita timeout/retries no construtor da aplicação. C02 registrou `NotFoundError` para esse padrão; a listagem da conta em 08/11/2026, na preparação de C03-B, também não o incluía. A configuração adaptada dos instrumentos não atualizou a aplicação.

C02 e C03-B registraram limite de uso do provedor com o modelo alternativo. Em C03-B, oito 429 foram absorvidos por retries na rajada real de dez, ampliando a espera compartilhada. Não se presume que identificadores ou quotas observados nessa conta sejam universais ou permanentes.

## 3. Falha e ausência de contexto têm tratamento assimétrico

O [NLPService](../api/services/nlp_service.py) retorna `None` para ausência reconhecida de contexto, mas deixa exceções propagarem. Texto livre captura a exceção e também a transforma em `None`; a opção de menu com `query` alcança a captura geral.

[C03-A](avaliacao/C03-relatorio-execucao.md) confirmou: texto livre retorna opção inválida e audita `MESSAGE_SENT`; menu retorna erro interno e audita `MESSAGE_FAILED`, sem salvar o par de mensagens dessa interação. Retomada posterior funcionou, mas comunicação da falha, classificação da auditoria e histórico diferem.

## 4. Montagem do índice vinculada à inicialização da aplicação

[api.main](../api/main.py) chama [setup_system](../app/main.py) durante a importação. O índice FAISS fica em memória e é reconstruído por processo; falha na montagem impede concluir a importação, sem caminho explícito de inicialização somente com menus.

A justificativa antiga de que o custo é sempre dominado pelos embeddings não é sustentada por C02. Na série principal com cache identificado, vetorização/indexação superou carregamento dos embeddings nas três inicializações medidas. C03-B observou outra distribuição em outra execução. Persistir o índice não foi comparado, portanto seu ganho não foi quantificado. Uma eventual persistência também precisa tratar invalidação quando a base muda. A base usada em C03-B tinha 17 documentos e 39 chunks, não os 16 arquivos/~50 chunks citados anteriormente.

## 5. Histórico persistido não é memória do gerador

[generate_response](../app/core/conversation.py) ignora `historico`; [run_rag](../app/core/rag_pipeline.py) recebe pergunta e retriever. O [NLPService](../api/services/nlp_service.py) não fornece histórico de turnos à geração. Perguntas de acompanhamento não recebem automaticamente as referências de mensagens anteriores.

O backend mantém estado de menu e mensagens no banco, o que é distinto de memória conversacional do LLM. O histórico tampouco é garantido como registro de todas as respostas: C03-A observou a lacuna do caminho de menu com falha. Incorporar histórico à geração exige definir seleção de turnos e sua relação com o contexto documental; isso permanece funcionalidade ausente.

## 6. Transações compartilhadas entre serviços e auditoria

[DbLogger](../api/utils/logger.py), [ConfigService](../api/services/config_service.py) e [FlowMediaService](../api/services/flow_media_service.py) podem confirmar ou reverter a sessão recebida; a auditoria não usa transação independente da conversa. As [interfaces I03 e I06](13-interfaces-e-contratos.md) descrevem os efeitos e a evidência limitada de C03-A.

Não há avaliação completa de atomicidade, consistência sob falhas de banco ou ordenação de mensagens simultâneas do mesmo usuário. Não se pode inferir essas garantias do commit final do ChatService.

## 7. Retenção e proteção do conteúdo persistido sem política implementada

Os [modelos](../api/models/models.py) relacionam mensagens textuais, usuário, nome e identificador. O código inspecionado não aplica criptografia de campo nem define rotina de expurgo/prazo de retenção. Isso não permite concluir se a infraestrutura utiliza criptografia de disco, controles de backup ou acesso ao banco: esses controles não foram verificados.

Caminhos de erro também podem registrar pergunta ou exceção em logs. [C06](avaliacao/arvore-de-utilidade.md#c06--segurançaconfidencialidade-fluxo-e-minimização-de-dados) permanece planejado para avaliar fluxo e minimização com dados sintéticos. Definições institucionais de retenção, acesso e uso dos dados continuam fora do que o código, isoladamente, comprova. A revisão técnica não constitui avaliação jurídica ou certificação de conformidade.

## 8. Testes de navegação não cobrem todo o núcleo RAG

O [CI](../.github/workflows/ci.yml) não instala `app/requirements.txt`; seus testes e cobertura de API não avaliam toda a recuperação/geração. Os instrumentos locais C03 exercitaram componentes reais com substituição de fronteiras, mas isso não equivale a cobertura sistemática do núcleo ou avaliação da qualidade documental.

C04 e C05 permanecem planejados para isolamento/testabilidade e fidelidade, respectivamente. As versões livres do stack RAG também exigem consultar o inventário de cada execução; versões do ambiente do autor e do CI não devem ser presumidas iguais.
