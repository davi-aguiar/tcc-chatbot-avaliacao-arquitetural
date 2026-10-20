# 02 — Arquitetura

Complemento: [interfaces e contratos atuais](13-interfaces-e-contratos.md), com entradas, saídas, efeitos colaterais, falhas e lacunas identificadas por inspeção antes dos próximos cenários.

## Visão de componentes

```mermaid
flowchart TD
    U[Cidadão no WhatsApp] --> GW{Gateway}
    GW -->|Evolution API| WH[POST /evolution_webhook]
    GW -->|Twilio| TW[POST /twilio/webhook]
    UI[Gradio / testes] --> REST[POST /messages/receive]

    WH --> CS[ChatService]
    TW --> CS
    REST --> CS

    CS --> MH[menu_handlers + menu_texts.json]
    CS --> NLP[NLPService]
    CS --> DB[(PostgreSQL)]
    CS --> LOG[DbLogger / audit_logs]

    MH --> FMS[FlowMediaService]
    MH --> CFG[ConfigService]
    FMS --> DB
    CFG --> DB

    NLP --> RAG[run_rag]
    RAG --> RET[FAISS retriever]
    RAG --> LLM[(Groq llama-3.3-70b-versatile)]
    RET --> DATA[data/servicos/*.txt]
```

## Duas aplicações no mesmo processo

O projeto tem dois pacotes Python que rodam juntos:

| Pacote | Responsabilidade | Depende de |
|---|---|---|
| `app/` | Núcleo RAG, separado das rotas HTTP, persistência de conversas e WhatsApp. Inclui acesso ao provedor e carga de modelos/documentos. | LangChain, FAISS, HuggingFace, Groq |
| `api/` | Backend FastAPI. Estado da conversa, menus, persistência, webhooks. | FastAPI, SQLAlchemy, Alembic, `app/` |

`api/main.py` amarra os dois:

```python
pln_resources = setup_system()                       # app/ constrói o índice FAISS
app.state.nlp_service = NLPService(retriever=pln_resources["servicos"])
```

O índice é construído **uma vez, na subida do processo**, e fica em memória
(`app.state`). Não há persistência do índice em disco.

## Camadas do `api/`

```
security.py   Autenticação das rotas de entrada. Sem import de app/ nem services.
routes/       Adaptadores HTTP (Evolution, Twilio, REST). Sem regra de negócio.
services/     Regra de negócio:
                chat_service.py     máquina de estados + orquestração
                menu_handlers.py    navegação do menu dinâmico (JSON)
                nlp_service.py      ponte para o RAG do app/
                config_service.py   leitura/escrita de system_configs
                flow_media_service.py  resolução de URL de imagem
schemas/      Pydantic: MessageSchema (entrada), MessageOut / ChatResponse (saída)
models/       SQLAlchemy: User, Chat, Message, SystemConfig, FlowMedia, AuditLog
db/           Engine, SessionLocal, get_db
dependencies/ exigir_token — dependência FastAPI de autenticação
utils/        DbLogger (log em console + tabela audit_logs)
alembic/      Migrações
```

## Camadas do `app/`

```
core/ingestion.py    DirectoryLoader sobre data/servicos/*.txt
core/intencao.py     e_saudacao() — sem imports, sem LLM
core/rag_pipeline.py get_llm (cache global), run_rag
core/conversation.py generate_response — usada apenas pelo Gradio
adapters/splitter.py RecursiveCharacterTextSplitter (1000/200)
adapters/embeddings.py  HuggingFaceEmbeddings, modelo multilíngue
adapters/vector_store.py FAISS.from_documents + as_retriever(k=10)
adapters/prompts.py  greeting_prompt, rag_prompt
adapters/respostas.py RESPOSTA_SEM_CONTEXTO, sem_contexto() — sem imports
main.py              setup_system() → {"servicos": retriever}
```

Os dois módulos "sem imports" (`intencao.py`, `respostas.py`) são deliberados: são a
lógica que o `api/` precisa consultar, e mantê-los livres de LangChain é o que permite
testá-los — e testar quem os usa — sem baixar o modelo de embeddings no CI.

## Ciclo de vida de uma mensagem

1. Gateway entrega a mensagem no webhook correspondente.
2. A rota autentica a requisição via `api/security.py` — assinatura Twilio ou segredo
   compartilhado. Falhou, responde 403 e nada mais acontece.
3. A rota extrai `id_wpp` e `text` e instancia `ChatService(db, nlp_service)`.
4. `ChatService.process_message`:
   1. normaliza o texto (`_clean_text`);
   2. busca/cria `User` e `Chat`;
   3. grava log em `audit_logs` (`MESSAGE_RECEIVED`);
   4. persiste a mensagem do usuário;
   5. decide a resposta pela máquina de estados (ver [doc 05](05-fluxo-conversa.md));
   6. persiste a resposta do bot e faz `commit`.
5. A rota converte `ChatResponse` no formato do gateway:
   - Evolution: chama `send_image` ou `send_text` via HTTP;
   - Twilio: devolve TwiML XML com `<Body>` e opcional `<Media>`;
   - REST: devolve JSON `MessageOut`.

O tratamento geral de erros em `process_message` tenta fazer `rollback` e devolver
`"Desculpe, ocorreu um erro interno."`. Isso não garante recuperação diante de toda falha
de infraestrutura. O caminho de texto livre contém ainda uma captura própria de falhas do
NLP, diferente da consulta pelo menu. A auditoria usa a mesma sessão e também realiza
commits; portanto, não se deve presumir uma única transação atômica para toda a mensagem.
Ver as interfaces I03 e I06 no [levantamento de contratos](13-interfaces-e-contratos.md).

## Decisões de projeto relevantes

- **Índice em memória, reconstruído a cada boot.** Simples, mas o startup paga o custo
  de baixar o modelo de embeddings e vetorizar ~16 arquivos. Aceitável nesse volume.
- **LLM em cache global** (`CACHED_LLM` em `rag_pipeline.py`): evita recriar o cliente
  Groq a cada requisição.
- **Menu como dado, não como código**: `menu_texts.json` descreve estados, textos,
  próximos estados e queries de RAG. Adicionar um menu não exige mudar Python.
- **Resolução de imagem em cascata**: `flow_media` (BD) → `system_configs` (BD) →
  variável de ambiente → fallback no JSON.
