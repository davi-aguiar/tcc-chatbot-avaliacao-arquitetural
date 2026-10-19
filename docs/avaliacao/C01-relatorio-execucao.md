# C01 — Relatório de execução

Execução local em 19/10/2026, pelo autor com assistência de IA. Protocolo: [registro inicial](C01-modificabilidade-registro-inicial.md). Evidências: [diretório](evidencias-c01/).

## Referência e ambiente

- Branch: `experimento/c01-modificabilidade`.
- Commit inicial: `46b6da2213733a809adfefffecb5336023f4d401`, árvore limpa antes do ensaio. Difere da referência histórica do protocolo; os testes iniciais foram repetidos nesta versão.
- Windows, Python 3.12.6, ambiente `.venv-c01` com dependências herdadas do Python instalado (`--system-site-packages`). Não equivale ao ambiente do CI, que usa Python 3.11 e versões fixadas.
- Instalados no ambiente local: pytest 9.1.1, alembic 1.18.5 e twilio 9.10.9 e suas dependências. Inventário em [dependencias.json](evidencias-c01/dependencias.json); horários e plataforma em [ambiente.json](evidencias-c01/ambiente.json).
- Banco SQLite em memória, identidade e nome sintéticos; sem gateway WhatsApp e sem publicação.

## Resultados

| Etapa | Resultado | Evidência |
|---|---|---|
| Primeira tentativa inicial | Coleta interrompida: alembic e twilio ausentes. Falha de preparação do ambiente, anterior à mudança funcional | [baseline.txt](evidencias-c01/baseline.txt) |
| Inicial após preparar dependências | 240 testes aprovados | [testes-baseline.txt](evidencias-c01/testes-baseline.txt) |
| C01-A | 244 testes aprovados; 13 etapas de conversa verificadas; nenhuma chamada NLP | [testes-A.txt](evidencias-c01/testes-A.txt), [percursos-A.json](evidencias-c01/percursos-A.json) |
| C01-B com NLP substituto | 244 testes aprovados; 18 etapas de conversa verificadas; uma consulta exata encaminhada com nome sintético | [testes-B.txt](evidencias-c01/testes-B.txt), [percursos-B.json](evidencias-c01/percursos-B.json) |
| Ingestão documental real | 17 documentos carregados; exatamente um contém o marcador sintético C01 | [ingestao.json](evidencias-c01/ingestao.json) |
| Recuperação vetorial real, após instalar dependências | Índice reconstruído: 17 documentos, 39 chunks; documento C01 presente nos resultados da pergunta do menu | [rag-real.json](evidencias-c01/rag-real.json) |

Os percursos passaram pelo `ChatService` real, persistência em SQLite e interpretador real do JSON. Foram conferidos estados e textos: `principal → 4 → 17 → 0 → 0`, opção inválida `99`, `/menu` e `principal → 4 → 2 (CEMERF) → 0 → 0`. Na variante B foi conferida também a opção `1`, a resposta controlada e o retorno. O aumento de 240 para 244 testes decorre da parametrização existente para o novo estado, não de quatro novos testes escritos.

## Alterações e custos operacionais

- C01-A: apenas `api/services/menu_texts.json`: opção 17 e novo estado com descrição explicitamente fictícia e retorno. [Patch A](evidencias-c01/C01-A.patch).
- C01-B: opção de consulta no mesmo JSON e novo `data/servicos/servico_experimental_c01.txt`, com marcador `C01-DOC-TESTE-2026`. [Patch incremental B](evidencias-c01/C01-B-incremental.patch).
- Zero arquivos Python funcionais alterados. O [executor](evidencias-c01/executar.py) é instrumento de avaliação, contabilizado separadamente dos dois arquivos funcionais. Demais arquivos novos são relatório e evidências.
- Cada variante foi executada em processo Python novo, carregando novamente o JSON. Não houve servidor persistente cujo reinício pudesse ser medido. A inspeção confirma carga do JSON na importação; atualização dinâmica em processo vivo não foi demonstrada.
- Na retomada, `langchain_groq` 1.1.3 e dependências foram instalados no ambiente experimental; os 244 testes voltaram a passar (3,61 s). Inventário atualizado em [dependencias-pos-rag.json](evidencias-c01/dependencias-pos-rag.json) e registro em [instalacao-rag.json](evidencias-c01/instalacao-rag.json). O arquivo `pre-requisitos-rag.json` preserva a inspeção anterior à instalação.
- O modelo de embeddings padrão foi preparado no cache local e o índice FAISS foi reconstruído pelo `setup_system()` real. A consulta real recuperou o documento sintético. Tempos: documentos 16,75 ms; chunking 4,28 ms; embeddings 52.703,91 ms; vetorização e indexação 6.697,64 ms; retriever 0,08 ms; total de montagem 59.422,79 ms. O intervalo completo do processo é maior, pois inclui importações e consulta. Esta primeira preparação não representa boot com cache aquecido.
- Geração externa ainda não executada: `GROQ_API_KEY` ausente no processo e nas variáveis de usuário/máquina do Windows, sem `.env` em raiz, `api` ou `app`. O pacote necessário já está instalado. Encaminhamento e recuperação reais têm evidências separadas; não foi demonstrado o percurso completo com geração real.
- Durações dos testes estão nos respectivos arquivos. Os horários abrangem preparação, edição, espera e verificações; não houve cronometração separada de esforço humano, edição e assistência. Não usar o intervalo total como tempo de implementação independente do autor.

## Julgamento e limites

**C01-A: atendido no escopo local definido.** A inclusão estática exigiu somente JSON, e os percursos previstos passaram.

**C01-B: parcialmente atendido.** A alteração permaneceu restrita a JSON e TXT; encaminhamento com substituto, ingestão, reconstrução do índice e recuperação vetorial reais passaram. Falta executar e analisar a geração pelo `NLPService` real com chave válida; a hipótese da integração completa continua em aberto.

Não foram observadas regressões nos testes e percursos exercitados. Isso não comprova ausência de regressões em toda a aplicação, comportamento em produção ou qualidade clínica. A configuração genérica localiza a mudança, mas erros em dados ainda podem comprometer navegação; os testes estruturais e percursos reduzem esse risco. Carregar JSON e índice na inicialização implica custo operacional para incorporar mudanças, em troca de simplicidade. O conteúdo sintético deve permanecer restrito ao ambiente experimental.

Para concluir a integração B, configurar `GROQ_API_KEY` localmente e executar a consulta pelo `NLPService` real, guardando e analisando a resposta em relação ao documento fictício. Só então atualizar o julgamento dessa parte. O [executor de RAG](evidencias-c01/executar_rag.py) reconstrói o índice e recupera documentos; com `--gerar` e chave configurada também chama a geração. A ausência de chave é registrada sem impedir a verificação local.

## Reprodução

Na raiz do projeto, executar com o Python do ambiente preparado:

```powershell
.\.venv-c01\Scripts\python docs/avaliacao/evidencias-c01/executar.py B
.\.venv-c01\Scripts\python docs/avaliacao/evidencias-c01/executar_rag.py --gerar
```

O executor sobrescreve os arquivos de resultado da variante escolhida. `baseline` deve ser executado sobre o commit inicial; `A`, sobre o estado do patch A; `B`, sobre a alteração completa. Usar a variante A sobre o JSON final não reproduz o artefato histórico de A. Os patches preservam os estágios sem exigir commits intermediários.
