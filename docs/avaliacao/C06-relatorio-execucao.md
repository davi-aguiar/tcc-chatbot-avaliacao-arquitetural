# C06 — Execução e julgamento de confidencialidade

**Estado: encerrado com ressalvas; parcialmente atendido no recorte, com revisão interpretativa do autor concluída.** As 14 observações foram válidas, com 12 pedidos serializados para transporte local, dois controles sem inferência, zero tentativas externas e nenhuma alteração funcional. O critério de logs falhou em quatro observações: a aplicação registrou o texto livre integral quando o NLP lançou exceção.

## Referência e integridade

O [protocolo v1](C06-protocolo.md) e a [matriz](c06/casos.json) foram fixados antes da coleta. O lote [20261114-231108-coletar-7b9bcf](evidencias-c06/20261114-231108-coletar-7b9bcf/execucao.json) começou em 14/11/2026 às 23:11:08 e terminou às 23:11:30, horário de Brasília; os JSON registram 15/11 em UTC. A referência de execução é `d5aa47767cd950cb13b63fdd2acc45353f969f2f`, com árvore Git limpa. Esse commit acrescenta a preparação de C06 após `92e48ab`; o conteúdo funcional permanece no corte `ffcd30fe07cbf281a030a14d481d3eee5533db5c`.

O [manifesto](evidencias-c06/20261114-231108-coletar-7b9bcf/ambiente.json) registra Python 3.12.10, Windows, dependências e 68 hashes SHA-256. O lote contém cópias dessas fontes. A [conferência posterior](evidencias-c06/validacao-evidencias.json) aprovou 381 verificações, incluindo hashes das cópias e fontes atuais, ordem/fixture das 14 observações, reconstrução integral do corpo HTTP, persistência e recálculo independente dos caminhos dos marcadores.

O [verificador](c06/conferir_evidencias.py) e suas [contraprovas](c06/test_conferencia.py) foram escritos após a coleta e não integram o manifesto anterior. Quatro testes passaram: lote original válido e rejeição de cópia de fonte alterada, pedido alterado e diagnóstico de localização alterado, sempre em diretórios temporários. Lint dos dois módulos passou. Esses testes não são observações adicionais do cenário. As 13 verificações do instrumento e os 244 testes existentes haviam passado na [preparação](evidencias-c06/verificacao-instrumento.json); a aplicação e os testes existentes não foram modificados nesta etapa.

## Fronteiras exercitadas

ChatService, interpretação do menu, NLPService, composição RAG/prompt/parser, fábrica original ChatGroq, SDK, modelos SQLAlchemy, persistência e DbLogger permaneceram reais. O recuperador devolveu um único Document sintético, sem identidade/histórico; não houve embeddings ou recuperação de corpus municipal. O SDK serializou os pedidos reais, interceptados por `httpx.MockTransport` antes da rede, com respostas HTTP 200/400 sintéticas. Não houve geração pelo modelo externo.

O corpo preservou a configuração padrão: `llama-3.3-70b-versatile`, temperatura 0,1, limite de 500 tokens, `stream=false` e uma mensagem de papel `user` contendo contexto e pergunta. A disponibilidade desse modelo não foi consultada. Cada observação usou banco SQLite em memória novo, ambiente isolado e credencial sintética; dotenv e credenciais reais não foram lidos. DNS, conexão, UDP e subprocessos ficaram bloqueados durante importação/execução; nenhuma tentativa foi registrada. Os 12 pedidos locais dividiram-se em seis HTTP 200 e seis HTTP 400, sem repetição de transporte nesta condição.

## Resultados por perfil

Cada linha resume duas observações, uma por rodada. As duas rodadas reproduziram o mesmo padrão de campos, persistência e exposição; tempos variam e não são medida de desempenho.

| Perfil | Pedido local por observação | Consulta integral em log operacional | Mensagens após execução | Auditoria final |
|---|---|---|---|---|
| D01 — menu, sucesso | 1 × 200 | Não observada | 2 históricas + entrada e resposta | MESSAGE_SENT |
| D02 — menu, erro | 1 × 400 | Não observada | Apenas as 2 históricas, após rollback | MESSAGE_FAILED |
| D03 — livre, sucesso | 1 × 200 | Não observada | 2 históricas + entrada e resposta | MESSAGE_SENT |
| D04 — livre, erro | 1 × 400 | **Presente, com relato** | 2 históricas + entrada e fallback | MESSAGE_SENT |
| D05 — autodeclarado, sucesso | 1 × 200 | Não observada | 2 históricas + entrada e resposta | MESSAGE_SENT |
| D06 — autodeclarado, erro | 1 × 400 | **Presente, com relato, nome e identificador digitados** | 2 históricas + entrada e fallback | MESSAGE_SENT |
| D07 — controle estático | 0 | Não observada | 2 históricas + entrada e menu | MESSAGE_SENT |

São 46 emissões de log operacional, 28 eventos de auditoria e 52 mensagens somadas nos snapshots finais dos 14 bancos isolados. D07 muda o estado para `WAITING_4_SERVICOS`; os demais mantêm o estado de entrada.

## Critérios do protocolo

| Critério | Resultado confirmado na revisão da síntese | Evidência e alcance |
|---|---|---|
| 1. Minimização automática | Atendido nos 12 pedidos | Nome/identificador cadastrados e histórico anterior ausentes do corpo; D07 sem pedido para avaliar |
| 2. Texto fornecido pelo usuário | Descritivo: preservado | Relato em oito pedidos D03–D06; nome/identificador autodeclarados em quatro D05/D06; sem remoção desses marcadores |
| 3. Não duplicação da consulta nos logs | **Não atendido** | Texto integral em D04-R1/R2 e D06-R1/R2, em uma emissão de erro por observação |
| 4. Credenciais | Atendido no recorte instrumentado | Diagnóstico bruto sem ocorrência em 14 registros; autenticação presente nos 12 pedidos e cabeçalhos não salvos |
| 5. Persistência | Descritivo: mapeada | Identidade em users; histórico e, salvo D02, par atual em messages; vínculo em chats; eventos/metadados em audit_logs |

A [análise por critério](evidencias-c06/analise-preliminar.json) preserva contagens, caminhos e limitações. Os itens descritivos não recebem aprovação por requisito de anonimização ou retenção que não foi fixado no protocolo.

### Nome cadastrado e nome autodeclarado

Em [D05-R1](evidencias-c06/20261114-231108-coletar-7b9bcf/D05-R1.json), `http[0].corpo.messages[0].content` contém `Nome Declarado Cseis` e `000000009999`, provenientes da pergunta. Não contém `Pessoa Sintetica Cseis` nem `000000006060`, mantidos em `depois.users[0]`. Os marcadores do histórico também não constam no corpo, embora permaneçam no banco.

`nlp[0].user_name_recebido` contém o nome cadastrado; o NLPService usa esse argumento depois de `run_rag`, na personalização. Por isso `nlp[0].resposta` começa com `Oi, Pessoa Sintetica Cseis!`, enquanto a resposta sintética do transporte era `Olá! RESPOSTA_C06_SINTETICA.`. A presença do nome na resposta final não demonstra envio desse campo ao modelo ou geração desse nome pelo modelo.

### Exposição em logs de falha

Em [D04-R1](evidencias-c06/20261114-231108-coletar-7b9bcf/D04-R1.json), `logs[2].mensagem` registra:

```text
NLPService falhou para: 'PERGUNTA_C06_LIVRE RELATO_C06_FICTICIO tosse inventada. Como acessar a espirometria municipal?'
```

Em [D06-R1](evidencias-c06/20261114-231108-coletar-7b9bcf/D06-R1.json), a mesma emissão também inclui o nome e identificador autodeclarados. O comportamento repete-se em R2. A origem está em [chat_service.py](../../api/services/chat_service.py#L316), `logger.exception("NLPService falhou para: %r", texto)`. O erro HTTP sintético é genérico e não ecoa a pergunta; o texto é inserido pela própria aplicação.

`mensagem` e `formatado` representam a mesma emissão, com o segundo campo incluindo traceback. São quatro emissões com relato, não oito exposições distintas. Os 28 eventos `audit_logs`, incluindo mensagens e metadados, não contêm a pergunta/relato nesta amostra; eles contêm o identificador cadastrado nas mensagens operacionais. A ausência de texto em metadados não basta para concluir ausência nos demais destinos.

### Persistência e indicação de sucesso

Em D02 o erro alcança o tratamento externo, o par atual de mensagens sofre rollback e ficam `MESSAGE_RECEIVED` e `MESSAGE_FAILED`; o chamador recebe erro interno genérico. Em D04/D06 a exceção do NLP é tratada internamente e convertida em ausência de resposta. A aplicação devolve o menu com indicação de opção inválida, persiste entrada/fallback e registra `MESSAGE_SENT`, apesar de `nlp[0].erro_tipo` ser `BadRequestError`.

Assim, `MESSAGE_SENT` comprova o retorno produzido pelo fluxo de conversa, sem demonstrar sucesso da inferência. O resultado reproduz a assimetria de tratamento observada no C03; não é uma auditoria completa de atomicidade transacional.

## Limites e fechamento

O diagnóstico de credencial foi calculado antes da omissão pelo instrumento. Como o segredo sintético foi descartado, a conferência posterior não pode refazer essa busca bruta; ela confere os diagnósticos e a ausência do marcador de omissão, além dos testes do instrumento. A remoção pelo instrumento não foi contada como proteção da aplicação.

O cenário observa a fronteira ChatService com SQLite em memória e captura INFO/exceções. Não avalia gateways, HTTP de entrada, autenticação real, WhatsApp, PostgreSQL, DEBUG, agregadores, produção, backups, retenção, autorização, criptografia ou práticas internas do provedor. O erro controlado não cobre respostas de provedor que ecoem dados de entrada. Duas rodadas demonstram repetição dos percursos, sem estimativa estatística de segurança.

O [julgamento final](evidencias-c06/julgamento-final.json) registra **C06 encerrado com ressalvas; parcialmente atendido no recorte**. O autor confirmou explicitamente a síntese e os limites apresentados na conversa, respondendo “Sim” após a exposição dos resultados e da proposta de classificação. A revisão foi assistida, sem avaliação cega ou revisor independente; não equivale a revisão individual dos 14 registros brutos. Não há revisão interpretativa obrigatória pendente.

O `execucao.json` original e a `analise-preliminar.json` preservam seus estados históricos anteriores ao fechamento; o julgamento final registra a confirmação posterior e os hashes desses artefatos. As fontes coletadas permanecem preservadas, e nenhuma correção de logging ou mudança funcional foi aplicada ao corte avaliado. A falha observada continua documentada; eventual correção e nova medição constituem manutenção posterior.
