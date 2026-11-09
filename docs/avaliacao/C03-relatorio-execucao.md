# C03 — Disponibilidade: relatório de execução

**Escopo deste relatório: C03-A, falhas imediatas sequenciais.** Após esta coleta, o autor solicitou verificar mensagens simultâneas. O [adendo C03-B](C03-B-relatorio-execucao.md) reproduziu bloqueio de outras requisições, com menu levando 193,832 s na rajada real de dez usuários. O resultado abaixo permanece válido em seu recorte e não constitui aprovação de disponibilidade sob concorrência.

**Estado: encerrado com ressalvas em 08/11/2026. Critério de continuidade atendido no recorte local de falhas imediatas; comunicação da falha e auditoria apresentam limitações.** Protocolo e critérios foram registrados [antes da coleta](C03-protocolo.md).

## Resultado

Os 12 estímulos de falha foram contidos pela aplicação, com resposta não vazia, estado inicial preservado e retomada estática funcionando no mesmo processo, sessão e usuário. As 48 mensagens posteriores (`/menu`, Serviços, CEMERF e retorno) tiveram os estados e textos previstos, persistência do par usuário/bot e `MESSAGE_SENT`, sem nova chamada ao NLP ou SDK. A injeção permaneceu ativa durante toda a retomada.

| Falha injetada no SDK | Menu com `query` | Texto livre | Interações de retomada atendidas |
|---|---|---|---|
| `APITimeoutError` | 2/2 | 2/2 | 16/16 |
| `APIConnectionError` | 2/2 | 2/2 | 16/16 |
| `NotFoundError` — modelo indisponível | 2/2 | 2/2 | 16/16 |
| **Total** | **6/6** | **6/6** | **48/48** |

Cada célula dos percursos conta casos que satisfizeram retorno controlado, estado e continuidade; não conta respostas geradas. Os erros foram produzidos localmente, sem geração ou espera de rede.

O julgamento usa a definição operacional prévia de retorno controlado: `ChatResponse` com texto não vazio e nenhuma exceção propagada ao chamador do `ChatService`. Isso não avalia a adequação do texto ao cidadão. Nos dois percursos, a aplicação continua respondendo, mas informa o problema de formas diferentes.

## Diferenças entre os percursos

| Observação durante a mensagem com falha | Menu com `query` — 6 casos | Texto livre — 6 casos |
|---|---|---|
| Estado inicial e após a falha | `WAITING_1_1_INFO`, preservado | `WAITING_MAIN_MENU`, preservado |
| Resposta devolvida | `Desculpe, ocorreu um erro interno.` | `Opção inválida. Por favor, digite um número válido:` e menu principal |
| Exceção sai do NLP? | Sim, o mesmo objeto injetado | Sim, o mesmo objeto injetado |
| Exceção sai do ChatService? | Não | Não |
| Auditoria da mensagem | `MESSAGE_RECEIVED` e `MESSAGE_FAILED` | `MESSAGE_RECEIVED` e `MESSAGE_SENT`, com `chamou_rag: true` |
| Novas linhas em `messages` na falha | 0 por caso | 2 por caso, entrada e resposta |
| Instrução de retomada na resposta | Não apresenta `/menu` nem o menu | Exibe menu, mas atribui a falha à entrada |

Pelo menu, `handle_dynamic_menu` deixa a exceção subir até a captura geral de `process_message`. O serviço executa rollback e devolve erro interno. O `MESSAGE_RECEIVED` já havia sido confirmado pela auditoria, mas as mensagens de usuário/bot não são persistidas nesse caminho: a resposta devolvida ao chamador não fica no histórico de `messages`. Há `MESSAGE_FAILED` com o tipo do erro.

Em texto livre, `_perguntar_ao_rag` captura a exceção e retorna `None`. `_dentro_do_menu` trata esse resultado como ausência de resposta e usa a mesma devolutiva de opção inválida. A transação segue pelo caminho comum: salva a pergunta e a resposta e audita `MESSAGE_SENT`. O log Python contém a exceção, mas o evento terminal de auditoria não distingue a falha de geração. Não foi o instrumento que converteu a exceção em `None`; essa conversão é comportamento do `ChatService` avaliado.

O 404 real de C01 e C02 já havia mostrado essa assimetria. C03 a reproduziu nos três tipos de falha, com retomada explícita e fronteira controlada. Isso amplia a evidência de continuidade sem transformar os ensaios anteriores em parte desta amostra.

## Corte, ambiente e validade da injeção

- Referência: `666b60175f8e16c6678ae3da3aca975ae2a4fa5e`, branch `experimento/c03-disponibilidade`. Python funcional, menus, base e testes iguais ao corte C02 (`46a87a7`); nenhuma alteração nesses arquivos nesta etapa.
- Windows 11, Python 3.12.10 em `.venv`; SQLAlchemy 2.0.51, LangChain Core 1.7.3, LangChain Groq 1.1.3, Groq 0.37.1 e HTTPX 0.28.1. Inventário completo e hashes em [ambiente.json](evidencias-c03/20261108-212956-falhas-4781d2/ambiente.json).
- Banco SQLite em memória novo por caso, com usuário/chat sintéticos previamente confirmados. A mesma sessão e usuário permanecem entre o estímulo e as quatro etapas seguintes; não há reparo de estado ou sessão pelo instrumento.
- `ChatService`, menus, `NLPService`, `run_rag`, composição do prompt e `ChatGroq` reais. Recuperação substituída por documento sintético local; sem embeddings, FAISS ou `setup_system()`.
- Injeção em `llm.client.create`, com exceções reais do SDK. Em cada um dos 12 casos, houve exatamente uma recuperação local, uma chamada SDK e prompt contendo a consulta e o marcador documental. O envelope do NLP observou e relançou o mesmo objeto de erro.
- Rede bloqueada durante preparação do cliente/NLP e execução: **zero tentativas registradas**. `.env` não carregado, credencial sintética e tracing externo desativado. O modelo do código foi mantido; não houve consulta ao catálogo do provedor ou verificação de disponibilidade atual.
- Os instrumentos/protocolo estavam ainda sem commit durante a coleta: o `git_status` do manifesto registra arquivos novos desta etapa. Os hashes e as cópias preservadas identificam o conteúdo efetivamente executado. Relatório e índices foram escritos após a coleta.

Na preparação, o bloqueio inicial também impediu criar o loop `asyncio`, pois o Windows usa um par de sockets locais para essa infraestrutura. O executor foi corrigido para criar/fechar o loop fora do bloqueio, mantendo cliente, NLP e todas as mensagens dentro dele. O protocolo recebeu essa informação antes da coleta. Essa falha ocorreu nos testes do instrumento, sem produzir lote arquitetural nem exigir mudança na aplicação.

## Evidências e verificações

Lote único: [20261108-212956-falhas-4781d2](evidencias-c03/20261108-212956-falhas-4781d2/), iniciado às 21:30 de 08/11/2026 em America/Sao_Paulo (00:30 de 09/11 em UTC). As datas UTC do manifesto não representam uma coleta em outro dia local.

O [registro por caso](evidencias-c03/20261108-212956-falhas-4781d2/casos-executados.json) conserva as 60 respostas, estado e auditoria por etapa, contagens de chamadas e persistência. O [resumo](evidencias-c03/20261108-212956-falhas-4781d2/resumo.json) traz os critérios agregados; o [log](evidencias-c03/20261108-212956-falhas-4781d2/aplicacao.log) conserva as capturas de exceção da aplicação. O [índice](evidencias-c03/README.md) explica os demais arquivos.

Antes da coleta: **244 testes do projeto, 6 verificações do instrumento C03 e 4 do instrumento C02 aprovados**, lint sem erros e compilação concluída. O [registro de verificação](evidencias-c03/verificacao-previa.txt) separa esses testes dos casos do cenário. As verificações C03 também rejeitam ausência de injeção/prompt e conferem que uma falha de continuidade produz julgamento parcial, sem confundir isso com coleta inválida.

## Interpretação arquitetural

| Decisão/achado | Evidência | Implicação e recomendação |
|---|---|---|
| Menus estáticos independem da geração após preparação | 48/48 interações sem NLP/SDK, com injeção ativa | Favorece continuidade de navegação diante das falhas exercitadas; preservar esse caminho local |
| Captura geral protege a entrada do ChatService | 6 falhas de menu com resposta de erro, estado preservado e retomada | Contém a exceção, mas a resposta não orienta recuperação; incluir instrução clara e preservar registro da resposta |
| Texto livre compartilha `None` para falha e ausência de resposta | 6 falhas viram opção inválida e `MESSAGE_SENT` | Risco de atribuir indisponibilidade ao usuário e ocultar falha na auditoria; distinguir resultados e padronizar tratamento |
| Auditoria confirma operações em pontos intermediários | Evento de recebimento persiste, mensagens são revertidas no menu | Revisar a consistência entre auditoria, histórico e resposta; avaliar commits de auditoria junto das transações da conversa |
| Inferência continua síncrona e sem prazo total declarado | Falhas injetadas imediatamente, SDK/retries fora do recorte | Não inferir continuidade durante espera longa; investigar timeout, retries e concorrência em manutenção/ensaio próprio |

As recomendações não foram implementadas durante a coleta. O resultado atende ao critério operacional de continuidade definido, com ressalvas de comunicação, rastreabilidade e alcance. Não demonstra disponibilidade plena da aplicação.

## Limites e fechamento

Injeção imediata no método SDK, sem transporte HTTP, retries internos ou timeout decorrido. Nenhuma medição de SLA, duração máxima de falha, recuperação do provedor ou percentual de disponibilidade. A aplicação foi representada após preparação; falhas ao carregar embeddings/índice e disponibilizar o servidor ficam fora do recorte. Chamadas diretas sequenciais, SQLite em memória, dois percursos e uma consulta por percurso; sem HTTP, gateways, PostgreSQL, concorrência, usuários reais ou qualidade de geração.

A coleta C03 está concluída: os 12 casos válidos satisfizeram retorno controlado, preservação de estado e navegação posterior, com zero tentativas de rede. A conclusão deve ser citada junto da assimetria entre os caminhos e da limitação de falhas imediatas. C04 pode partir dessa referência funcional preservada para avaliar isolamento e testabilidade do núcleo RAG.
