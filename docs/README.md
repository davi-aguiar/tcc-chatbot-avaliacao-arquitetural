# Documentação — Assistente Virtual PET Saúde

Chatbot de WhatsApp com RAG para a Secretaria Municipal de Saúde de Vitória da Conquista (BA).
Responde dúvidas sobre serviços de saúde municipais combinando um menu numérico guiado com
busca semântica sobre documentos oficiais.

## Índice

| Documento | Conteúdo |
|---|---|
| [01 — Visão Geral](01-visao-geral.md) | O que o sistema faz, atores, glossário |
| [02 — Arquitetura](02-arquitetura.md) | Componentes e fontes, camadas/dependências, decisões D01–D12, inicialização, sequência e implantação; revisão após C03 |
| [03 — Instalação e Execução](03-instalacao-e-execucao.md) | Dependências, variáveis de ambiente, como rodar |
| [04 — Referência da API](04-api-referencia.md) | Endpoints HTTP, payloads, respostas |
| [05 — Fluxo de Conversa](05-fluxo-conversa.md) | Máquina de estados, menus, comandos |
| [06 — Pipeline RAG](06-rag.md) | Ingestão, chunking, embeddings, FAISS, LLM, prompts |
| [07 — Banco de Dados](07-banco-de-dados.md) | Modelos, tabelas, migrações Alembic |
| [08 — Base de Conhecimento](08-base-de-conhecimento.md) | Documentos em `data/servicos`, formato, como adicionar |
| [09 — Configuração e Mídias](09-configuracao-e-midias.md) | `system_configs`, `flow_media`, imagens de fluxo |
| [10 — Problemas Conhecidos](10-problemas-conhecidos.md) | Limitações abertas de concorrência, inferência, persistência e ciclo de vida, com fontes e evidências |
| [11 — Integração Contínua](11-ci.md) | GitHub Actions, testes, cobertura, como rodar os checks localmente |
| [12 — Instrumentação e Medições](12-instrumentacao-e-medicoes.md) | Latência, cobertura e tempo de indexação: o que é medido, como coletar, o que fica de fora |

## Avaliação arquitetural

O objetivo de documentar a arquitetura atual está organizado em [02 — Arquitetura](02-arquitetura.md), com responsabilidades, dependências e decisões rastreáveis ao código. As fronteiras estão detalhadas em [13 — Interfaces e contratos atuais](13-interfaces-e-contratos.md), revisado após C01–C03 e usado como referência para C04–C06. A documentação distingue implementação, resultados observados e propostas de manutenção.

Comece pelo [resumo da avaliação](avaliacao/README.md), que reúne os resultados de C01, C02 e C03 e orienta a leitura. Os arquivos técnicos estão explicados nos índices de evidências de [C01](avaliacao/evidencias-c01/README.md), [C02](avaliacao/evidencias-c02/README.md), [C03-A](avaliacao/evidencias-c03/README.md) e [C03-B](avaliacao/evidencias-c03-b/README.md).

O escopo dos próximos cenários está na [árvore de utilidade refinada](avaliacao/arvore-de-utilidade.md), alinhada aos seis atributos previstos no projeto de pesquisa.

| Documento | Conteúdo |
|---|---|
| [C01 — Registro inicial](avaliacao/C01-modificabilidade-registro-inicial.md) | Cenário de modificabilidade, hipótese e procedimento |
| [C01 — Relatório de execução](avaliacao/C01-relatorio-execucao.md) | C01-A atendido; C01-B parcial na configuração original e percurso completo com modelo alternativo |
| [C01 — Análise para o TCC](avaliacao/C01-analise-resultados.md) | Interpretação arquitetural, limitações e fechamento com ressalvas |
| [C02 — Protocolo](avaliacao/C02-protocolo.md) | Entradas, medições de processamento/inicialização e critérios descritivos |
| [C02 — Relatório de execução](avaliacao/C02-relatorio-execucao.md) | Resultados de desempenho, limite de uso do provedor e limitações |
| [C03-A — Protocolo](avaliacao/C03-protocolo.md) | Falhas imediatas controladas no SDK, dois percursos e retomada estática |
| [C03-A — Relatório de execução](avaliacao/C03-relatorio-execucao.md) | Continuidade em 12/12 casos sequenciais, com ressalvas de resposta, auditoria e persistência |
| [C03-B — Protocolo](avaliacao/C03-B-protocolo.md) | Concorrência HTTP, esperas controladas e série com provedor real |
| [C03-B — Relatório de execução](avaliacao/C03-B-relatorio-execucao.md) | Bloqueio de outras conversas, menu em 194 s e timeout de cliente; sem queda do processo no ensaio |

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
