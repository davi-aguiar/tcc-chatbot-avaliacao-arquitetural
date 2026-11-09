# C03-B — Concorrência e bloqueio: protocolo complementar

Registro em 08/11/2026, antes da coleta. Motivação: o autor relata que mensagens simultâneas fazem o assistente parar de responder. A coleta anterior de [C03](C03-relatorio-execucao.md), aqui denominada C03-A, tratou falhas imediatas sequenciais e permanece preservada. O adendo amplia o recorte; não reclassifica aqueles 12 casos.

## Perguntas e referência

1. Requisições de usuários distintos são atendidas em paralelo ou esperam a inferência de outro usuário?
2. Durante essa espera, menus estáticos e uma sonda de saúde HTTP conseguem responder?
3. O processo encerra, o cliente excede seu timeout, há erro HTTP/banco ou o serviço responde depois de acumular espera?
4. O SDK recebe HTTP 429/retries na série real? Isso explica toda a observação ou apenas parte dela?

Corte funcional `666b60175f8e16c6678ae3da3aca975ae2a4fa5e`, mesmo de C03-A e mesmo conteúdo de aplicação de C02. Branch `experimento/c03-disponibilidade`. Não corrigir rotas, NLP, persistência ou concorrência durante a coleta. RabbitMQ não será instalado nem avaliado nesta etapa.

## Ambiente e isolamento

- Servidor HTTP Uvicorn em subprocesso, um worker, sem reload, escutando somente `127.0.0.1` em porta efêmera. Cliente de carga em outro processo: evita que o bloqueio do servidor paralise o medidor.
- Importar a aplicação e rotas reais de `api.main`. Alterar somente recursos de avaliação em memória: banco SQLite em arquivo temporário com sessão por requisição, segredo sintético, transporte de saída Evolution interceptado. Sem acesso a banco real, WhatsApp ou envio a pessoas.
- Logs, eventos com relógio monotônico, estado/persistência/auditoria e respostas HTTP por lote. Conservar PID, vida do processo, códigos HTTP, erros de cliente, inícios/fins de inferência, tentativas HTTP do SDK, lag do loop e sondas antes/durante/depois.
- Desabilitar carregamento automático de `.env` e tracing externo na aplicação isolada. No modo real, carregar apenas a chave Groq explicitamente no subprocesso, sem gravá-la. Desabilitar downloads de pesos; usar snapshot local já existente.
- Endpoints de avaliação (`/__c03/*`) só existem no servidor local de ensaio. Permitem preparar usuários, consultar telemetria e saúde; não integram a aplicação funcional.

## Série controlada

Preservar ChatService, NLPService, prompts, composição LangChain, cliente ChatGroq e SDK Groq. Substituir a montagem do índice por retriever local com documento sintético. Substituir somente o transporte HTTP do provedor (`httpx.MockTransport`) e o transporte `requests.post` de saída Evolution. O SDK conserva retries e backoff reais. Bloquear conexões externas no subprocesso controlado; permitir somente loopback.

| Perfil | Mensagens da rajada | Fronteira controlada |
|---|---|---|
| `estatico` | `4`, menu principal → Serviços | Sem inferência e saída Evolution imediata |
| `rag_lento` | `1`, estado de informações de agendamento | HTTP de geração espera 0,5 s e devolve resposta sintética válida |
| `envio_lento` | `4`, menu principal → Serviços | Transporte de saída Evolution espera 0,5 s |
| `limite_429` | `1`, estado de informações de agendamento | Primeira tentativa HTTP 429 com `retry-after: 0.5`; retry responde HTTP 200 |
| `timeout_cliente` | Igual a `rag_lento` | Mesmo atraso de 0,5 s, mas timeout de leitura do cliente de 1 s |

Para `estatico` e `rag_lento`: rotas REST `/messages/receive` e Evolution `/evolution_webhook`, rajadas de **1, 2, 5 e 10** usuários. Para `envio_lento` e `limite_429`: Evolution, rajadas de **1 e 10**. Para `timeout_cliente`: Evolution, rajada de **10**. Uma passagem por combinação, ordem fixa conforme essa lista; não constitui estudo estatístico de capacidade.

Usuários distintos, nome `Teste C03B`, estados confirmados antes de cada rajada. Usar identificadores novos para evitar estado remanescente. Todas as requisições da rajada são liberadas juntas por barreira no cliente; guardar horários efetivos de despacho. Não usar `asyncio.gather` no mesmo processo da aplicação como único indicador de concorrência.

Em cada rajada, despachar sonda de saúde HTTP e uma requisição estática de outro usuário. Nos perfis de espera, aguardar o primeiro evento de transporte ativo antes de enviá-las, confirmando que foram lançadas durante a operação. Para `envio_lento`, o menu sonda também passa pela saída lenta e isso deve ser considerado.

Após o término dos clientes, aguardar drenagem da rajada pelo servidor, inclusive se houve timeout no cliente. Fazer nova sonda de saúde e `/menu`, verificar PID e consultar a persistência. Não confundir timeout do medidor com encerramento do processo ou perda definitiva de mensagem. Limite operacional de drenagem de 90 s no controlado e 360 s no real; excedê-lo é registrado, sem repetir seletivamente o caso.

## Série com provedor real

A preparação autenticada preservada em `preparacao-modelos.json` encontrou `openai/gpt-oss-120b` e não encontrou o modelo padrão `llama-3.3-70b-versatile`. Fixar o alternativo como **configuração adaptada**, mantendo temperatura 0,1, 500 tokens e `max_retries=2`. Timeout HTTP do SDK limitado a 35 s por operação de leitura nesta série; não alegar equivalência com prazo indefinido do corte.

Executar montagem real da base/índice com `setup_system()`, embeddings padrão no snapshot local `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` e recuperação `k=10`. Registrar métricas de boot fora das mensagens. Não enviar dados pessoais reais: pergunta fixa de agendamento, usuários fictícios, histórico sintético.

Série limitada pela cota: **Evolution, `rag_real`, rajadas de 1 e 10 usuários**, com sondas durante e depois, um processo mantido e sem pausa artificial entre as duas rajadas. Cliente de carga com timeout de leitura de 180 s; drenagem limitada a 360 s. Registrar tentativas HTTP, erros e cabeçalhos de quota/retry permitidos, sem autorização ou corpos de requisição. Não ocultar retries do SDK. Sem geração de aquecimento extra; a ordem e a janela de quota afetam os tempos.

Esta série pode demonstrar filas de espera e erros sob essa configuração, mas não reproduz o gateway, PostgreSQL, máquina/worker count ou condições exatas do incidente relatado. Se faltar chave/cache ou o boot falhar, registrar impedimento; não converter preparação incompleta em aprovação.

## Medidas e interpretação

- Duração de cada requisição, amplitude de despacho da rajada, códigos HTTP, respostas efetivas ou erros do cliente. HTTP 200 do webhook não comprova sucesso da inferência: consultar saída interceptada, SDK e auditoria.
- Quantidade máxima de inferências simultâneas e intervalos de início/fim; sobreposição temporal da sonda com a espera. Lag do loop medido por tarefa de 20 ms; a tarefa é observação local, não um health check de produção.
- Estado, contagem de mensagens, `MESSAGE_SENT`/`MESSAGE_FAILED`, erros de banco, respostas de saída capturadas e menus posteriores. Logs de aplicação preservados; tentativas externas no controlado invalidam seu isolamento.
- **Bloqueio reproduzido:** sonda despachada durante uma espera só chega ao endpoint após o término dessa espera, com lacuna do heartbeat/lag compatível e inferências serializadas. Durações agregadas isoladamente não bastam para atribuir causa.
- **Queda de processo:** PID encerra inesperadamente, com código de saída/log preservados. **Timeout de cliente:** erro de leitura no cliente com processo ainda vivo, acompanhado de verificação de drenagem e retorno posterior. **Falha operacional:** status HTTP ou resposta de erro, incluindo falha de inferência auditada mesmo com webhook 200.
- Análise descritiva por perfil, rota e tamanho. Não inferir um número máximo de usuários em produção nem SLA. O limite de 30 s mencionado pelo autor em C02 é referência posterior, sem converter este ensaio em requisito validado.

## Comandos e evidências

```powershell
.\.venv\Scripts\python.exe -m pytest -q docs/avaliacao/c03b/test_concorrencia.py
.\.venv\Scripts\python.exe docs/avaliacao/c03b/executar.py controlado
.\.venv\Scripts\python.exe docs/avaliacao/c03b/executar.py real
```

Cada comando cria lote próprio em `evidencias-c03-b/`, preservando tentativas. Manifesto guarda hash do protocolo, fontes e instrumentos, versões e estado do Git. Os limites, substituições e os resultados reais/controlados devem permanecer separados no relatório complementar. O resultado de C03-A continua válido apenas em seu escopo original.
