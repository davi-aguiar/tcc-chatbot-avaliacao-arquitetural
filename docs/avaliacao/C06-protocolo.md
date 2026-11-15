# C06 — Segurança/confidencialidade: fluxo e minimização de dados

Versão 1, definida em 14/11/2026 antes da coleta. C01 a C05 estão encerrados com ressalvas; o [fechamento do C05](evidencias-c05/julgamento-final.json) registra 12 revisões confirmadas pelo autor. Plano: [árvore de utilidade](arvore-de-utilidade.md#c06--segurançaconfidencialidade-fluxo-e-minimização-de-dados).

## Pergunta e corte

Quais dados são colocados no pedido de inferência, persistidos e registrados nos logs quando o ChatService processa consulta de menu e texto livre, com sucesso e falha do provedor?

Referência: `92e48ab6eb76608904a3367a3b596ad34b12590d`, após o fechamento do C05. O conteúdo funcional de `api/`, `app/`, `data/` e `tests/` permanece igual ao corte `ffcd30fe07cbf281a030a14d481d3eee5533db5c`. Não modificar aplicação, corpus, menus, prompts ou testes existentes durante o cenário. Cada lote identifica Git, dependências, hashes e cópias das fontes efetivamente utilizadas. Não corrigir vazamentos durante a coleta nem reclassificar lotes anteriores.

O recorte é técnico, exploratório e baseado em cenários; não constitui certificação jurídica, auditoria completa de segurança, validação clínica ou avaliação das práticas internas do provedor.

## Matriz e isolamento

[casos.json](c06/casos.json) fixa sete perfis, duas rodadas D01–D07, total de **14 observações previstas**. Cada observação usa banco SQLite em memória novo, com usuário, conversa e duas mensagens anteriores sintéticas. Identificador cadastrado, nome cadastrado, nome/identificador digitados no texto, histórico e contexto têm marcadores distintos.

| ID | Entrada | Resposta local do transporte |
|---|---|---|
| D01 | Query do menu do serviço experimental C01 | HTTP 200 e resposta sintética |
| D02 | Mesma query de menu | HTTP 400 com erro sintético genérico |
| D03 | Texto livre com relato de saúde fictício | HTTP 200 |
| D04 | Mesmo texto livre | HTTP 400 |
| D05 | Texto livre contendo nome e identificador autodeclarados, diferentes dos cadastrados | HTTP 200 |
| D06 | Mesmo texto autodeclarado | HTTP 400 |
| D07 | Navegação estática pelo menu principal | Nenhuma chamada de inferência prevista |

As duas rodadas verificam repetição do fluxo, sem estimativa estatística de segurança. O erro HTTP 400 é uma condição controlada, não reprodução de mensagem real do provedor; não ecoa deliberadamente o texto do usuário. O SDK mantém sua política original de retries, e suas requisições são contadas. O controle estático não mede confidencialidade da inferência por ausência de chamada; confirma apenas a fronteira exercitada.

## Fronteiras reais e substituições

Preservar ChatService, interpretador do JSON, NLPService, `run_rag`, prompt, parser, fábrica ChatGroq, SDK/serialização HTTP, modelos SQLAlchemy, persistência e DbLogger reais. O cliente é criado pela fábrica original; o instrumento fornece somente um `httpx.Client` com `MockTransport` e uma credencial sintética. Não ler `.env` nem credenciais reais. O nome do modelo padrão permanece no corpo serializado; a disponibilidade desse modelo não é consultada ou demonstrada.

O recuperador é um Runnable local com um Document sintético identificado, sem nome, identificador ou histórico do usuário. Essa substituição permite observar composição e transporte sem embeddings, pesos ou indexação; não avalia recuperação semântica, pertinência de documentos municipais ou confidencialidade de um corpus real. O objetivo é distinguir os campos adicionados pelo fluxo dos dados já presentes na pergunta/contexto.

O levantamento por inspeção identifica as fronteiras abaixo; o corpo serializado e os registros efetivos ainda dependem da coleta.

| Fronteira | Fonte | Dados e observação a conferir |
|---|---|---|
| Entrada REST/gateways → conversa | `api/routes/routes.py`, `webhook.py`, `twilio_webhook.py` | Adaptadores fornecem identificador e texto; entrega e autenticação ficam fora da execução dinâmica |
| Conversa/menu → NLP | `api/services/chat_service.py`, `menu_handlers.py` | Texto livre limpo ou query configurada, com `user_name` como argumento separado |
| NLP → RAG/SDK | `api/services/nlp_service.py`, `app/core/rag_pipeline.py`, `app/adapters/prompts.py` | RAG recebe pergunta e recuperador; personalização pelo nome ocorre após a resposta. Verificar no HTTP, sem presumir ausência de nome apenas pela assinatura |
| Conversa → persistência | `api/models/models.py`, `chat_service.py` | Identidade, conversa, mensagens e estado; observar commits/rollback em cada percurso |
| Conversa/erro → logs | `api/utils/logger.py`, `chat_service.py` | Mensagem, metadados e traceback podem seguir caminhos diferentes; conteúdo de erro não se limita ao `meta` de `MESSAGE_SENT` |

O HTTP é interceptado **após a serialização do SDK e antes de qualquer envio**. Capturar método, URL sem query, corpo JSON e presença de autenticação, nunca seu valor. Respostas HTTP são geradas pelo transporte local. Bloquear DNS, conexão, UDP e criação de subprocessos durante importação e execução. Qualquer tentativa externa torna a observação inválida, mesmo que termine bloqueada.

Executar com ambiente construído por lista permitida, neutralizando dotenv, tracing e telemetria; não herdar configuração de banco, credenciais ou modelo. Criar/fechar o loop asyncio fora do bloqueio de sockets locais, conforme a limitação identificada em C03. Remover handlers temporários, restaurar cache global/fábrica e descartar o banco ao final de cada observação.

## Dados a preservar

Para cada observação: ID/rodada, entrada efetiva, fixture, chamadas ao NLP e ao recuperador, pedido HTTP serializado, status sintético, retorno/erro observado pelo chamador, registros de logs, snapshots de `users`, `chats`, `messages` e `audit_logs` antes/depois e tentativas externas bloqueadas. Preservar separadamente mensagem e metadados dos eventos de auditoria.

Capturar logs Python no nível INFO, incluindo o traceback formatado das exceções. Não substituir chamadas de logging nem suprimir exceções da aplicação. Essa captura não comprova comportamento com DEBUG, filtros, agregadores, proxies, logs do sistema operacional ou configuração de produção diferente.

A credencial sintética também é tratada como marcador de segredo: verificar sua presença nos registros brutos antes de qualquer remoção; registrar o resultado e os locais, mas omitir seu valor dos artefatos salvos. Cabeçalhos de autenticação não são persistidos. Não transformar remoção posterior pelo instrumento em evidência de que a aplicação protegeu o segredo. Não gravar o banco físico nem informações reais de usuários.

## Critérios e julgamento

1. **Minimização automática:** nome e identificador cadastrados e histórico anterior não devem ser acrescentados ao corpo do pedido sem necessidade documentada. Verificar cada marcador e caminho JSON. Nome usado na personalização posterior da resposta não demonstra envio ao modelo.
2. **Texto fornecido pelo usuário:** identificar que nome, identificador e relato inseridos na própria pergunta chegam ou não ao corpo serializado. A presença desses dados não comprova adição automática pelo sistema. Informar se há remoção/redação antes da fronteira; ausência de campos extras não demonstra anonimização do texto livre. Este item é descritivo, sem requisito retrospectivo de anonimização.
3. **Logs:** texto da consulta/relato não deve ser duplicado nos logs operacionais. Conferir mensagem, metadados e traceback, em sucesso e falha, além de `audit_logs`. Distinguir console de persistência de auditoria. Presença de identificador nos eventos deve ser mapeada separadamente, sem confundi-lo com texto integral ou nome.
4. **Credenciais:** o marcador de segredo não deve aparecer no corpo do pedido, banco ou logs. A presença esperada no cabeçalho de autenticação é representada apenas por booleano. Exposição em exceção também conta como falha antes da remoção pelo instrumento.
5. **Persistência:** mapear explicitamente identidade/nome/estado em `users`, texto integral em `messages`, vínculo em `chats` e conteúdo/metadados em `audit_logs`, incluindo diferenças entre sucesso e falha. Esse mapeamento não atribui conformidade a retenção, finalidade institucional, autorização de acesso ou criptografia, que não são avaliadas.

Uma observação é válida apenas com fixture identificada, chamada esperada ou controle estático, corpo capturado quando aplicável, resposta HTTP sintética coerente, snapshots/logs disponíveis, fontes preservadas e zero tentativas externas. Falha do instrumento deixa a parte não avaliada; não equivale a violação da aplicação.

Reportar cada critério verificável como atendido/não atendido/não avaliado, com o campo ou trecho sustentador. Itens descritivos permanecem descritivos. O cenário será atendido apenas no recorte se todos os critérios normativos forem atendidos nas observações válidas; resultados mistos são parcialmente atendidos. Não anunciar aprovação pela simples execução completa do instrumento. A síntese interpretativa será revisada pelo autor após a coleta.

## Escopo e preparação

As chamadas partem da fronteira ChatService, sem HTTP de entrada, autenticação real, Evolution, Twilio ou envio ao WhatsApp. As rotas são inspecionadas para localizar a entrada e os consumidores, mas seus payloads, logs de entrega e segredos específicos não são exercitados dinamicamente. PostgreSQL, produção, dados reais, retenção, backups, autorização, criptografia e práticas do provedor ficam fora do recorte.

O modo `preparar` verifica matriz, dependências e fontes; não executa as 14 observações e não atribui resultados ao C06. Testes do instrumento usam casos próprios e diretórios temporários, separados da amostra. O modo `coletar` cria outro lote único com as observações previstas; não será executado nesta preparação.

```powershell
python -m pytest -q docs/avaliacao/c06/test_instrumento.py
python docs/avaliacao/c06/executar.py preparar
# Coleta posterior, sem chave real e sem rede:
python docs/avaliacao/c06/executar.py coletar
```
