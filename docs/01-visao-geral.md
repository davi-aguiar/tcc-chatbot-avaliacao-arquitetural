# 01 — Visão Geral

## O que é

Assistente virtual de WhatsApp da Secretaria Municipal de Saúde de Vitória da Conquista.
O cidadão manda mensagem para o número do serviço e recebe:

- um **menu numérico** hierárquico com os principais serviços de saúde do município; e
- respostas em **linguagem natural** geradas por RAG (Retrieval-Augmented Generation)
  sobre os documentos oficiais em `data/servicos/`.

O projeto nasceu no contexto do PET-Saúde (Programa de Educação pelo Trabalho para a Saúde).

## Para que serve

Reduzir a demanda por telefone/presencial para dúvidas repetitivas:

- Onde e como agendar consultas e exames
- Documentos exigidos em cada serviço
- Endereços, telefones e horários de CEMERF, CEMAE, CEO, CAPS II, CAPS AD III,
  Ambulatório de Saúde Mental, Secretaria Municipal de Saúde
- Acesso a medicamentos, fraldas, fitas/lancetas, órteses, próteses, aparelhos
  auditivos, bolsas de ostomia, meios auxiliares de locomoção
- Programas: Oxigenoterapia Domiciliar, Asma Grave, Espirometria, Eletrocardiograma
- Orientações de emergência (AVC, engasgo, quedas, sangramento, surtos, violência)

## Atores

| Ator | Papel |
|---|---|
| Cidadão | Envia mensagens pelo WhatsApp |
| Gateway WhatsApp | Evolution API (self-hosted) **ou** Twilio WhatsApp — ambos suportados |
| Backend | FastAPI: estado da conversa, menus, persistência, auditoria |
| LLM | Inferência externa via Groq; padrão no código: `llama-3.3-70b-versatile`. C02/C03-B usaram modelo alternativo identificado em seus relatórios |
| Vetores | FAISS em memória, embeddings HuggingFace `paraphrase-multilingual-MiniLM-L12-v2` |
| Banco | Banco relacional definido por `DATABASE_URL`, acessado por SQLAlchemy e versionado por Alembic; instalação documentada com PostgreSQL e ensaios locais com SQLite |

A implementação combina `api/` e `app/` no mesmo backend; o Gradio é uma entrada separada para o núcleo RAG. A [documentação de arquitetura](02-arquitetura.md) detalha componentes, camadas lógicas, dependências e decisões. Os resultados de concorrência de [C03-B](avaliacao/C03-B-relatorio-execucao.md) mostram bloqueio em um worker; esta visão funcional não implica garantia de disponibilidade ou de capacidade simultânea.

## Glossário

| Termo | Significado |
|---|---|
| **RAG** | Retrieval-Augmented Generation: busca trechos relevantes e injeta no prompt do LLM |
| **retriever** | Objeto LangChain que devolve os *k* chunks mais similares a uma pergunta |
| **estado (`state`)** | Nó atual do usuário na máquina de estados do menu (ex.: `WAITING_4_2_CEMERF`) |
| **`id_wpp`** | Identificador do usuário no WhatsApp (número, ou `whatsapp:+55...` no Twilio) |
| **flow_key / image_key** | Chave que associa um item de menu a uma imagem (ex.: `CALENDARIO`) |
| **Evolution API** | Gateway open-source de WhatsApp rodando em Docker |

## Idioma

Todo o conteúdo de usuário, prompts e base de conhecimento está em **português brasileiro**.
