# Evidências do C03-B — Concorrência

Complemento solicitado pelo autor após a coleta sequencial de C03, denominada C03-A. O [protocolo](../C03-B-protocolo.md) foi fixado antes das rajadas. O [relatório](../C03-B-relatorio-execucao.md) distingue bloqueio do servidor, timeout do cliente e encerramento do processo.

**Resultado:** bloqueio reproduzido. Na rajada real de dez usuários, o menu de outro usuário levou 193,832 s, a saúde levou 139,729 s e um cliente excedeu o timeout de 180 s. Houve oito HTTP 429 absorvidos por retries; as dez gerações terminaram e o processo permaneceu vivo, com retomada após drenagem. Na série controlada, nove clientes excederam 1 s, mas o servidor continuou o processamento. Isso não estabelece capacidade de produção nem a causa exata do incidente anterior.

## Lotes

| Diretório/arquivo | Finalidade |
|---|---|
| [20261108-221810-controlado-22d87e](20261108-221810-controlado-22d87e/) | 21 rajadas, 104 mensagens de carga, inferência/envio com atrasos conhecidos e retries 429 sintéticos |
| [20261108-221907-real-af86f2](20261108-221907-real-af86f2/) | Base/índice reais, modelo adaptado, rajadas de 1 e 10 usuários com provedor real; saída WhatsApp interceptada |
| [preparacao-modelos.json](preparacao-modelos.json) | Listagem autenticada prévia: padrão ausente, alternativo presente; não contém chave |
| [verificacao-instrumento.txt](verificacao-instrumento.txt) | Testes do instrumento, regressão e lint; não integram a coleta |
| [validacao-evidencias.json](validacao-evidencias.json) | Conferência posterior de hashes, cópias, requisições, menus, auditoria e persistência |

Cada lote contém:

- `ambiente.json`: commit, versões, estado do Git e SHA-256 das fontes e instrumentos existentes antes da coleta.
- `config.json`, `boot.json` e `servidor.json`: condições da série, montagem, porta local e PID. `descartavel.db` é banco sintético local, se presente; os snapshots JSON permitem conferir os resultados sem reabri-lo.
- `Bxx-*.json`: requisições de uma rajada, respostas/erros, horários efetivos, sondas durante/depois e snapshot de estado, histórico e auditoria.
- `resumo.json`: contagens e medidas por rajada. HTTP 200 do webhook é separado de sucesso de inferência e de texto efetivamente preparado para entrega.
- `eventos.jsonl`: entrada/saída ASGI, início/fim do NLP, tentativas de provedor e status/cabeçalhos permitidos, saída Evolution interceptada e atrasos do loop. Relógio monotônico compartilhado pelo sistema operacional entre cliente e servidor.
- `servidor.log`: saída bruta Python/Uvicorn, preservada na codificação Windows do subprocesso (CP1252). Os JSONs e `eventos.jsonl` usam UTF-8. Os tempos HTTP até os cabeçalhos não devem ser confundidos com duração completa do NLP; o intervalo `nlp_inicio`/`nlp_fim` inclui o SDK e seus retries.
- `execucao.json`: completude, horários, PID e encerramento voluntário/forçado. O encerramento voluntário ao final do ensaio não conta como queda.
- Cópias do protocolo, executor e servidor: conteúdo usado naquele lote, preservado antes das rajadas.

Instrumentos: [executor HTTP](../c03b/executar.py), [servidor isolado](../c03b/servidor.py), [verificações prévias](../c03b/test_concorrencia.py) e [conferência posterior](../c03b/conferir_evidencias.py). O último foi produzido após as coletas e não altera os instrumentos preservados.

## Reprodução

Os comandos estão no protocolo. Cada execução cria lote novo e usa apenas loopback para a API. A série controlada bloqueia conexões externas; a série real usa a chave local sem gravá-la e exige o snapshot de embeddings já em cache. Não executa carga contra o WhatsApp nem contra o banco de produção. A aplicação funcional e as evidências de C03-A permanecem preservadas.

Conferir os lotes existentes sem repetir chamadas:

```powershell
.\.venv\Scripts\python.exe docs/avaliacao/c03b/conferir_evidencias.py
```

São observações locais com um worker, usuários distintos, uma passagem por configuração e ordem fixa. Não estabelecem um limite máximo de usuários em produção e não determinam a causa exata do incidente anterior relatado pelo autor.
