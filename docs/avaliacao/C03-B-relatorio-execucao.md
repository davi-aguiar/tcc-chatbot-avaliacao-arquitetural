# C03-B — Disponibilidade sob concorrência

**O ensaio reproduziu bloqueio de outras requisições durante inferência e envio síncronos. Não houve encerramento inesperado do processo na configuração local de um worker.** O [protocolo complementar](C03-B-protocolo.md) foi registrado antes das rajadas. A coleta anterior, aqui denominada C03-A, permanece preservada e seu resultado de continuidade após falhas imediatas não se estende a concorrência.

## O que foi verificado

O autor relata que o assistente para de responder quando recebe mensagens simultâneas. Foram exercitadas as rotas HTTP reais com clientes em processo separado e usuários distintos, monitorando resposta, persistência, vida do processo e uma tarefa de heartbeat do loop. A saída para WhatsApp foi interceptada: nenhuma mensagem foi enviada a pessoas ou ao gateway real.

Houve duas séries separadas: controlada, com esperas conhecidas nas fronteiras externas, e com provedor real, base/índice reais e modelo adaptado. A máquina, banco SQLite descartável e quantidade de workers não representam necessariamente o incidente anterior; a causa exata daquele incidente continua não demonstrada.

## Série controlada — isolamento das causas

Lote [20261108-221810-controlado-22d87e](evidencias-c03-b/20261108-221810-controlado-22d87e/): **21 rajadas, 104 mensagens de carga**, mais duas mensagens de menu e duas sondas de saúde por rajada. Total de 146 mensagens processadas pelo ChatService e 42 requisições de saúde durante/depois; preparação e consultas de evidências são adicionais.

REST e Evolution receberam rajadas de 1, 2, 5 e 10 usuários com menu estático e com consulta RAG cuja resposta HTTP sintética esperava 0,5 s. Evolution também recebeu espera no envio, retry 429 e teste de timeout do cliente. Provedor, SDK, NLP e rotas têm as substituições explicitadas no protocolo; o modo controlado não usa a internet.

| Rota/perfil | Usuários | Maior duração de carga | Menu enviado durante a rajada | Inferências simultâneas, máximo |
|---|---:|---:|---:|---:|
| REST, estático | 10 | 0,291 s | 0,235 s | 0 |
| REST, RAG com espera de 0,5 s | 10 | 5,360 s | 4,274 s | 1 |
| Evolution, estático | 10 | 0,278 s | 0,277 s | 0 |
| Evolution, RAG com espera de 0,5 s | 1 | 0,540 s | 0,519 s | 1 |
| Evolution, RAG com espera de 0,5 s | 2 | 1,073 s | 1,079 s | 1 |
| Evolution, RAG com espera de 0,5 s | 5 | 2,704 s | 2,671 s | 1 |
| Evolution, RAG com espera de 0,5 s | 10 | 5,425 s | 4,864 s | 1 |
| Evolution, envio com espera de 0,5 s | 10 | 5,828 s | 5,777 s | 0 |
| Evolution, 429 + retry após 0,5 s | 10 | 5,384 s | 2,148 s | 1 |

O menu sonda é `/menu`, de outro usuário. No perfil de envio lento, ele próprio também sofre os 0,5 s da saída interceptada; esse valor não isola apenas a espera pela rajada. Na tabela, maior duração de carga representa requisições concluídas, sem incluir o teste de timeout descrito abaixo.

As rajadas de 10 foram despachadas em aproximadamente 2–3 ms, mas as consultas foram executadas uma por vez. Nas **13 rajadas com espera**, a sonda de saúde foi efetivamente despachada enquanto havia inferência/envio ativo e só entrou na aplicação depois do fim dessa espera. O heartbeat confirmou lacunas compatíveis: máximo de 4,324 s em RAG lento com Evolution e 5,270 s no envio lento. A saúde simples pôde executar entre operações, enquanto o menu, que também passa por dependências/persistência, acumulou mais espera. Não se presume indisponibilidade contínua de todos os endpoints durante a rajada inteira.

O perfil de limite de uso preservou o SDK real: houve 11 respostas HTTP 429 sintéticas e 11 retries HTTP 200 nas rajadas de 1 e 10. Assim, a espera de backoff síncrona também bloqueia o loop, mesmo com resposta HTTP posterior bem-sucedida. Não se atribui o atraso do perfil de envio ao provedor de inferência: ali não houve NLP.

## Timeout do cliente e aparente queda

No perfil `timeout_cliente`, Evolution recebeu 10 consultas com a mesma espera sintética de 0,5 s, mas o cliente desistia após 1 s sem leitura. **Uma requisição recebeu HTTP 200 e nove terminaram em `ReadTimeout`.**

O servidor continuou vivo e executou as 10 inferências, todas HTTP 200 na fronteira sintética. As 10 respostas passaram pela saída Evolution interceptada e foram persistidas/auditadas. O menu sonda levou 4,806 s; depois da drenagem, saúde e `/menu` voltaram a responder. Portanto, esse caso reproduz timeout de quem espera a resposta sem reproduzir morte de processo ou perda definitiva de processamento.

Não se deve somar esses nove timeouts a nove erros de geração. Tampouco um HTTP 200 do webhook demonstra entrega ao cidadão, pois o gateway foi interceptado. Reenvio de webhook após timeout e duplicação de mensagens não foram exercitados.

## Série com provedor real

A série real usa o lote [20261108-221907-real-af86f2](evidencias-c03-b/20261108-221907-real-af86f2/). A listagem autenticada anterior não incluía o modelo padrão e incluía `openai/gpt-oss-120b`: essa é uma configuração adaptada, temperatura 0,1, até 500 tokens, dois retries e timeout de leitura do SDK de 35 s. O cliente HTTP de carga tem prazo de leitura de 180 s. A disponibilidade de modelos foi verificada naquela conta/data, sem presumir descontinuação global do padrão.

A montagem real carregou 17 documentos e produziu 39 chunks, usando embeddings do snapshot local e recuperação `k=10`. A montagem instrumentada levou 53,479 s; esse boot foi excluído das durações das mensagens. Não houve download de pesos. Não se compara esse valor diretamente com C02, pois o estado de cache e a execução são distintos.

| Medida | Rajada de 1 | Rajada de 10 |
|---|---:|---:|
| Consultas concluídas pelo servidor | 1/1 | 10/10 |
| Respostas HTTP 200 recebidas pelos clientes de carga | 1/1 | 9/10 |
| Timeout do cliente | 0 | 1, após 180,039 s |
| Durações das requisições que receberam resposta | 1,744 s | 1,000 a 167,288 s |
| Menu de outro usuário, enviado durante a inferência | 1,583 s | **193,832 s** |
| Sonda de saúde enviada durante a inferência | 1,554 s | **139,729 s** |
| Maior atraso observado no heartbeat do loop | 1,695 s | **81,516 s** |
| Máximo de inferências simultâneas | 1 | 1 |
| Tentativas do provedor | 1 HTTP 200 | 10 HTTP 200 e 8 HTTP 429 |

Na rajada de 10, o provedor informou limite de **8.000 tokens por minuto** e `retry-after` entre 10 e 26 s. Os retries do SDK absorveram os oito 429, e nenhuma geração terminou em exceção. A quota é da conta/configuração observada nesta data; não é característica fixa do modelo. O acúmulo da rajada anterior também afeta a janela de consumo.

As dez requisições foram liberadas em uma janela de aproximadamente 2 ms. Uma excedeu o timeout de 180 s no cliente; sua inferência terminou depois, e a resposta passou pela saída interceptada. A rajada e as verificações posteriores terminaram em 193,969 s. O timeout não foi contado como resposta rápida nem como falha de geração. Os 12 pares da rajada (dez consultas e dois menus de sonda) foram persistidos: 24 mensagens, 12 `MESSAGE_RECEIVED` e 12 `MESSAGE_SENT`, sem `MESSAGE_FAILED`.

Após drenagem, a saúde respondeu em 0,002 s e `/menu` em 0,034 s, com PID preservado. Não houve encerramento inesperado nem erro de banco registrado. O processo só foi encerrado pelo comando explícito do instrumento ao final, com código 0. Os dois lotes concluíram sem encerramento forçado.

Os intervalos de inferência, retries, sondas e heartbeat confirmam bloqueio no servidor local, além da pressão de quota. O tempo de 194 s do menu é uma observação real desta configuração adaptada, não uma estimativa derivada das esperas sintéticas. Ele mostra que a navegação estática pode ficar sem resposta por vários minutos enquanto outras conversas aguardam geração/retry.

Registros individuais e auditoria na [rajada de dez usuários](evidencias-c03-b/20261108-221907-real-af86f2/B02-evolution-rag_real-10.json); tentativas e cabeçalhos permitidos em [eventos.jsonl](evidencias-c03-b/20261108-221907-real-af86f2/eventos.jsonl). O recebimento de HTTP 200 e a persistência comprovam conclusão local, sem avaliação da fidelidade documental ou entrega pelo WhatsApp.

## Diagnóstico sustentado pela execução

O caminho real de entrada aguarda `ChatService.process_message`, que chama o NLP e o SDK de modo síncrono. Essas operações não cedem o loop durante a espera. Evolution ainda executa `requests.post` de modo síncrono para entregar a resposta. As capturas de início/fim, as sondas e as lacunas do heartbeat reproduziram o bloqueio nos dois pontos separadamente.

Isso não equivale a um limite fixo de dez conversas: uma única consulta em espera já atrasou uma sonda de outro usuário. A quantidade de usuários amplia o acúmulo; duração da inferência, backoff do SDK e envio afetam diretamente o tempo em que outras requisições podem ficar sem atendimento.

Os menus não chamam o modelo, mas compartilham o processo/loop com essas operações. Assim, a independência funcional demonstrada em C03-A não garante resposta de menu durante uma inferência em andamento.

## Implicações e próximos passos

| Evidência | Implicação |
|---|---|
| Espera de inferência bloqueia sondas/menu, com máximo de uma inferência ativa | O caminho atual não isola o trabalho demorado das demais requisições na configuração de um worker |
| Espera de envio também bloqueia, sem NLP | Tratar apenas o acesso ao modelo não cobre toda a rota Evolution |
| SDK pode aguardar quota por backoff síncrono | A política de cota/retry precisa integrar o diagnóstico de acúmulo |
| Cliente desiste, servidor continua e prepara a resposta | Diferenciar aceitação, processamento e entrega; verificar comportamento de reenvio/idempotência em ensaio próprio |
| Processo permanece vivo e menus voltam após drenagem | Nesta configuração, houve bloqueio/espera; o encerramento inesperado relatado não foi reproduzido |

RabbitMQ permanece uma hipótese de manutenção, sem instalação ou comparação neste ensaio. Uma eventual fila deve ser avaliada junto de consumidores, limites de processamento, quota do provedor, ordenação por conversa e política de erro/retry. Estes resultados não demonstram que apenas adicionar um broker resolveria o incidente relatado.

## Validade e limites

Corte funcional igual a C03-A, sem mudanças em `api/`, `app/`, menus, documentos ou testes existentes. Windows 11, Python 3.12.10, FastAPI 0.140.13, Uvicorn 0.51.0, SQLAlchemy 2.0.51 e SDK Groq 0.37.1; inventários completos por lote. Fontes/instrumentos identificados por hash e copiados antes de cada série. Arquivos de avaliação ainda sem commit, conforme os manifestos. A conferência posterior não integra a coleta.

Servidor de um worker, clientes em processo separado, sem reload; banco SQLite em arquivo descartável e sessão por requisição. O processo não foi reiniciado entre rajadas da mesma série, e o histórico/auditoria cresceram. Uma passagem por combinação e ordem fixa; sem percentis ou estimativa estatística de capacidade. O tratamento de uma mesma conversa com mensagens sobrepostas não foi avaliado.

Gateway e entrega real, PostgreSQL, proxy/túnel, política de retry do gateway, múltiplos workers, carga prolongada, memória sob carga extensa e causa exata do incidente anterior ficam fora do recorte. As sondas e logs acrescentam trabalho ao servidor. A série real muda modelo e timeout, portanto não equivale à configuração original. Falha de boot também não foi o estímulo desta coleta.

As duas verificações do instrumento e os 244 testes do projeto passaram; lint e compilação foram concluídos. A [conferência de evidências](evidencias-c03-b/validacao-evidencias.json) registra contagens, hashes, menus e persistência. A aplicação e os instrumentos/protocolo originais de C03-A permanecem preservados.

## Fechamento do adendo

Coleta concluída em 08/11/2026. C03-A atende ao critério original de retomada após falhas imediatas. C03-B demonstra bloqueio sob concorrência, agravado pela quota do provedor, sem reproduzir morte do processo. O conjunto deve ser apresentado com ambas as conclusões: a arquitetura permite retomar menus depois da falha/espera, mas não garante que outras conversas recebam resposta enquanto operações síncronas estão em curso. Não atribuir aprovação geral de disponibilidade ou capacidade simultânea ao C03.
