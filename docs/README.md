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

## Avaliação arquitetural

As fronteiras entre componentes estão descritas em [13 — Interfaces e contratos atuais](13-interfaces-e-contratos.md), como preparação para os próximos cenários.

Comece pelo [resumo da avaliação](avaliacao/README.md), que reúne o resultado do C01 e orienta a leitura. Os arquivos técnicos estão explicados no [índice das evidências](avaliacao/evidencias-c01/README.md).

O escopo dos próximos cenários está na [árvore de utilidade refinada](avaliacao/arvore-de-utilidade.md), alinhada aos seis atributos previstos no projeto de pesquisa.

| Documento | Conteúdo |
|---|---|
| [C01 — Registro inicial](avaliacao/C01-modificabilidade-registro-inicial.md) | Cenário de modificabilidade, hipótese e procedimento |
| [C01 — Relatório de execução](avaliacao/C01-relatorio-execucao.md) | C01-A atendido; C01-B parcial na configuração original e percurso completo com modelo alternativo |
| [C01 — Análise para o TCC](avaliacao/C01-analise-resultados.md) | Interpretação arquitetural, limitações e fechamento com ressalvas |

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
