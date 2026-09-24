# 12 — Instrumentação e Medições

De onde saem os números que o sistema consegue reportar sobre si mesmo: latência de
resposta, cobertura de testes e tempo de indexação na subida.

Nenhum dos três existia de forma utilizável antes. Esta página descreve o que foi
instrumentado, como coletar e — importante para quem for usar isso como evidência — o que
cada medida **não** cobre.

---

## 1. Latência de resposta

### O que havia

`audit_logs` registrava apenas dois eventos, `MESSAGE_RECEIVED` e `MESSAGE_FAILED`, ambos
emitidos em `chat_service.py`. Com um único timestamp por mensagem não há intervalo a
calcular: falta o instante final.

O caminho alternativo óbvio — subtrair `messages.created_at` da mensagem do bot pela do
usuário — não funcionava por um defeito nos modelos:

```python
created_at = Column(DateTime, default=datetime.now(timezone.utc))   # antes
```

Isso passa um **valor**, não uma função. `datetime.now()` é avaliado uma vez, no import do
módulo, e toda linha gravada por aquele processo recebe a hora em que a aplicação subiu.
Valia para `users`, `chats`, `messages` e `audit_logs`, e também para os `onupdate` de
`system_configs` e `flow_media`.

O sintoma é o pior possível: não há erro, e o valor gravado é uma data plausível. A falha
só aparece quando alguém tenta calcular um intervalo e encontra zero.

### O que existe agora

**`api/models/models.py`** — `default=agora_utc`, passando a função em vez do resultado.

Não se usa `server_default=func.now()` no lugar: no PostgreSQL, `now()` devolve o horário
de início da **transação**, e `process_message` grava a mensagem do usuário e a do bot na
mesma transação — as duas voltariam a ter timestamps idênticos, que é exatamente o que se
quer evitar. O equivalente correto no banco seria `clock_timestamp()`, mas aí a hora passa
a vir do relógio do servidor de banco, e não do processo que atendeu a requisição.

**`api/services/chat_service.py`** — novo evento `MESSAGE_SENT`, emitido depois do commit,
fechando o par com `MESSAGE_RECEIVED`.

| Campo do `metadata_info` | Significado |
|---|---|
| `duracao_total_ms` | Recepção → resposta persistida e commitada |
| `duracao_rag_ms` | Soma das chamadas ao RAG. **Ausente** quando não houve |
| `chamou_rag` / `chamadas_rag` | Se e quantas vezes o RAG foi acionado |
| `estado_entrada` / `estado_saida` | Nó da máquina de estados antes e depois |
| `tem_imagem` | Se a resposta anexou mídia |
| `tamanho_resposta` | Caracteres do texto devolvido |

`MESSAGE_FAILED` recebeu os mesmos dois campos de duração — o caso lento é justamente o
que mais interessa medir, e antes ele não era medido.

### Três decisões que afetam como o número deve ser lido

**A medição usa `time.perf_counter()`, não o relógio de parede.** É monotônico: ajuste de
horário por NTP no meio da requisição não produz duração negativa nem inflada. Os
`created_at` de `audit_logs` continuam servindo para ordenar e datar; a **duração** vem do
contador monotônico, que é o instrumento correto para medir intervalo.

**O RAG é cronometrado por um envelope, não no ponto de chamada.** Há dois caminhos até o
`NLPService`: texto livre passa por `_perguntar_ao_rag`, mas opção de menu com `query`
chama o serviço direto, de dentro de `handle_dynamic_menu`. Medir só o primeiro deixaria
de fora a maior parte do tráfego — quase todo o menu responde por query de RAG. A classe
`_NLPCronometrado` envolve o serviço no construtor do `ChatService`, então os dois
caminhos passam pelo mesmo cronômetro.

**O `meta` não carrega o texto da conversa.** Só grandezas: duração, estado, tamanho. A
conversa já está inteira em `messages`; repeti-la em `audit_logs` espalharia dado de saúde
por mais uma tabela sem finalidade própria, contra o princípio de minimização da LGPD
(ver [doc 10](10-problemas-conhecidos.md), item 3). `test_log_nao_carrega_o_texto_da_conversa`
trava essa decisão.

### Como coletar

```sql
-- Latência por mensagem, do mais lento para o mais rápido
SELECT
    created_at,
    user_id,
    (metadata_info->>'duracao_total_ms')::numeric  AS total_ms,
    (metadata_info->>'duracao_rag_ms')::numeric    AS rag_ms,
    metadata_info->>'estado_entrada'               AS estado
FROM audit_logs
WHERE event_type = 'MESSAGE_SENT'
ORDER BY total_ms DESC;
```

```sql
-- Distribuição, separando quem passou pelo RAG de quem não passou
SELECT
    metadata_info->>'chamou_rag' AS chamou_rag,
    count(*)                                                   AS n,
    round(avg((metadata_info->>'duracao_total_ms')::numeric), 1) AS media_ms,
    round(percentile_cont(0.5)  WITHIN GROUP (
        ORDER BY (metadata_info->>'duracao_total_ms')::numeric), 1) AS p50_ms,
    round(percentile_cont(0.95) WITHIN GROUP (
        ORDER BY (metadata_info->>'duracao_total_ms')::numeric), 1) AS p95_ms
FROM audit_logs
WHERE event_type = 'MESSAGE_SENT'
GROUP BY 1;
```

Separar por `chamou_rag` não é detalhe: misturar navegação de menu (sem chamada externa)
com pergunta em texto livre numa média só produz um número que não descreve nenhum dos
dois casos.

### O que esta medida não cobre

Mede o trecho sob responsabilidade da aplicação: recepção no webhook → resposta persistida.
**Fica de fora** o tempo de rede entre o WhatsApp e o gateway, o processamento do gateway
(Evolution API ou Twilio) e a entrega de volta ao aparelho do cidadão. A latência
percebida por quem manda a mensagem é maior que a medida aqui, e a diferença não é
observável de dentro do sistema.

---

## 2. Cobertura de testes

`--cov=api` no CI, configuração em `pyproject.toml`, relatório guardado como artefato
`cobertura-api` a cada execução. Detalhes, incluindo por que os `__init__.py` vazios
mudaram o número de 82% para 57%, em [doc 11](11-ci.md#cobertura).

Resumo do que o número significa: cobertura de `api/`, com `api/alembic/` omitido. `app/`
não entra no CI porque suas dependências não são instaladas lá — para incluir o núcleo
RAG é preciso rodar localmente com o stack completo.

---

## 3. Tempo de indexação na subida

`app/main.py` cronometra cada etapa de `setup_system()` e deixa o resultado em
`METRICAS_INDEXACAO`, além de emitir no log:

```
INFO:AppLogger:INDEXACAO_CONCLUIDA {'carregamento_documentos_ms': 12.4,
 'chunking_ms': 3.1, 'carregamento_embeddings_ms': 4210.7,
 'vetorizacao_e_indexacao_ms': 388.2, 'criacao_retriever_ms': 0.1,
 'total_ms': 4614.5, 'n_documentos': 16, 'n_chunks': 47}
```

(valores ilustrativos — o número real depende da máquina e de o modelo já estar em cache)

A quebra por etapa existe por um motivo específico. A [doc 10](10-problemas-conhecidos.md)
justifica não persistir o índice FAISS afirmando que *"o boot gasta o tempo carregando o
modelo de embeddings, não vetorizando"*. A afirmação é plausível e nunca foi medida — e
ela é o argumento inteiro para uma decisão arquitetural. `carregamento_embeddings_ms`
contra `vetorizacao_e_indexacao_ms` decide a questão.

Para ler o valor de dentro da aplicação:

```python
from app.main import METRICAS_INDEXACAO   # preenchido após setup_system()
```

O dicionário é mutado no lugar, nunca reatribuído, então quem importou o nome antes da
montagem continua enxergando o conteúdo depois dela.

**Atenção na primeira execução:** `carregamento_embeddings_ms` inclui o download do modelo
do Hugging Face Hub se ele ainda não estiver em `~/.cache/huggingface`. Para medir o boot
em regime, descarte a primeira execução após uma limpeza de cache.
