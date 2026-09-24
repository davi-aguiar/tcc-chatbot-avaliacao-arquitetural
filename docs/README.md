# Documentação — Assistente Virtual PET Saúde

Chatbot de WhatsApp com RAG para a Secretaria Municipal de Saúde de Vitória da Conquista (BA).
Responde dúvidas sobre serviços de saúde municipais combinando um menu numérico guiado com
busca semântica sobre documentos oficiais.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 — Visão Geral](01-visao-geral.md) | O que o sistema faz, atores, glossário |
| [02 — Arquitetura](02-arquitetura.md) | Componentes, camadas, fluxo de uma mensagem |
| [03 — Instalação e Execução](03-instalacao-e-execucao.md) | Dependências, variáveis de ambiente, como rodar |
| [04 — Referência da API](04-api-referencia.md) | Endpoints HTTP, payloads, respostas |
| [05 — Fluxo de Conversa](05-fluxo-conversa.md) | Máquina de estados, menus, comandos |
| [06 — Pipeline RAG](06-rag.md) | Ingestão, chunking, embeddings, FAISS, LLM, prompts |
| [07 — Banco de Dados](07-banco-de-dados.md) | Modelos, tabelas, migrações Alembic |
| [08 — Base de Conhecimento](08-base-de-conhecimento.md) | Documentos em `data/servicos`, formato, como adicionar |
| [09 — Configuração e Mídias](09-configuracao-e-midias.md) | `system_configs`, `flow_media`, imagens de fluxo |
| [10 — Problemas Conhecidos](10-problemas-conhecidos.md) | O que continua aberto e por quê |
| [11 — Integração Contínua](11-ci.md) | GitHub Actions, testes, cobertura, como rodar os checks localmente |
| [12 — Instrumentação e Medições](12-instrumentacao-e-medicoes.md) | Latência, cobertura e tempo de indexação: o que é medido, como coletar, o que fica de fora |

## Início rápido

```powershell
pip install -r api/requirements.txt
pip install -r app/requirements.txt
# criar .env na raiz (ver doc 03)
uvicorn api.main:app --reload
```

Interface de teste local sem WhatsApp:

```powershell
python frontend/gradio_app.py
```

## Estrutura do repositório

```
api/          Backend FastAPI: rotas, serviços, modelos, migrações
app/          Núcleo RAG: ingestão, splitter, embeddings, vector store, pipeline
data/servicos Base de conhecimento (.txt) usada pelo RAG
frontend/     App Gradio para teste local do RAG
tests/        Testes automatizados (pytest)
docs/         Esta documentação
.github/workflows/ci.yml  Pipeline de CI
docker-compose.yaml       Evolution API + Postgres + Redis (gateway WhatsApp)
```
