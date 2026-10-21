# C01 — Relatório de execução

Execução local em 19/10/2026, pelo autor com assistência de IA. Protocolo: [registro inicial](C01-modificabilidade-registro-inicial.md). Evidências: [índice explicativo](evidencias-c01/README.md). Estado: encerrado com ressalvas; síntese no [resumo da avaliação](README.md).

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
| Recuperação vetorial real, após instalar dependências, na primeira máquina | Índice reconstruído: 17 documentos, 39 chunks; documento C01 presente nos resultados da pergunta do menu | [registro histórico](evidencias-c01/rag-recuperacao-historico.json) |
| Retomada em novo ambiente local | 244 testes aprovados em 6,13 s | [testes-geracao.txt](evidencias-c01/testes-geracao.txt), [ambiente-geracao.json](evidencias-c01/ambiente-geracao.json) |
| Geração com modelo original | Requisição retornou HTTP 404; geração não concluída | [tentativa original](evidencias-c01/rag-tentativa-modelo-original.json) |
| Ensaio complementar com modelo disponível | Recuperação e geração reais; seis etapas pelo ChatService, incluindo consulta e retorno, verificadas | [rag-real.json](evidencias-c01/rag-real.json) |

Os percursos passaram pelo `ChatService` real, persistência em SQLite e interpretador real do JSON. Foram conferidos estados e textos: `principal → 4 → 17 → 0 → 0`, opção inválida `99`, `/menu` e `principal → 4 → 2 (CEMERF) → 0 → 0`. Na variante B foi conferida também a opção `1`, a resposta controlada e o retorno. O aumento de 240 para 244 testes decorre da parametrização existente para o novo estado, não de quatro novos testes escritos.

## Alterações e custos operacionais

- C01-A: apenas `api/services/menu_texts.json`: opção 17 e novo estado com descrição explicitamente fictícia e retorno. [Patch A](evidencias-c01/C01-A.patch).
- C01-B: opção de consulta no mesmo JSON e novo `data/servicos/servico_experimental_c01.txt`, com marcador `C01-DOC-TESTE-2026`. [Patch incremental B](evidencias-c01/C01-B-incremental.patch).
- Zero arquivos Python funcionais alterados. Os executores [de percursos](evidencias-c01/executar.py) e [de RAG](evidencias-c01/executar_rag.py) são instrumentos de avaliação, contabilizados separadamente dos dois arquivos funcionais. Demais arquivos novos são documentação e evidências.
- Cada variante foi executada em processo Python novo, carregando novamente o JSON. Não houve servidor persistente cujo reinício pudesse ser medido. A inspeção confirma carga do JSON na importação; atualização dinâmica em processo vivo não foi demonstrada.
- Na retomada, `langchain_groq` 1.1.3 e dependências foram instalados no ambiente experimental; os 244 testes voltaram a passar (3,61 s). Inventário atualizado em [dependencias-pos-rag.json](evidencias-c01/dependencias-pos-rag.json) e registro em [instalacao-rag.json](evidencias-c01/instalacao-rag.json). O arquivo `pre-requisitos-rag.json` preserva a inspeção anterior à instalação.
- O modelo de embeddings padrão foi preparado no cache local e o índice FAISS foi reconstruído pelo `setup_system()` real. A consulta real recuperou o documento sintético. Tempos: documentos 16,75 ms; chunking 4,28 ms; embeddings 52.703,91 ms; vetorização e indexação 6.697,64 ms; retriever 0,08 ms; total de montagem 59.422,79 ms. O intervalo completo do processo é maior, pois inclui importações e consulta. Esta primeira preparação não representa boot com cache aquecido.
- Na execução inicial, a geração externa não foi executada por ausência de `GROQ_API_KEY`. Na retomada descrita abaixo, o autor disponibilizou a chave em `.env` ignorado pelo Git, permitindo a tentativa real e o ensaio complementar. A credencial não integra as evidências.
- Durações dos testes estão nos respectivos arquivos. Os horários abrangem preparação, edição, espera e verificações; não houve cronometração separada de esforço humano, edição e assistência. Não usar o intervalo total como tempo de implementação independente do autor.

## Julgamento e limites

**C01-A: atendido no escopo local definido.** A inclusão estática exigiu somente JSON, e os percursos previstos passaram.

**C01-B: parcialmente atendido na configuração original; percurso completo demonstrado em ensaio complementar adaptado.** A alteração funcional permaneceu restrita a JSON e TXT. A geração com `llama-3.3-70b-versatile` falhou com HTTP 404. Com `openai/gpt-oss-120b`, selecionado somente no processo do executor experimental, recuperação, geração pelo `NLPService` real e retorno pelo `ChatService` passaram. Isso sustenta a integração com um modelo disponível, mas não comprova funcionamento da configuração original.

Não foram observadas regressões nos testes e percursos exercitados. Isso não comprova ausência de regressões em toda a aplicação, comportamento em produção ou qualidade clínica. A configuração genérica localiza a mudança, mas erros em dados ainda podem comprometer navegação; os testes estruturais e percursos reduzem esse risco. Carregar JSON e índice na inicialização implica custo operacional para incorporar mudanças, em troca de simplicidade. O conteúdo sintético deve permanecer restrito ao ambiente experimental.

## Retomada e análise da geração real

Na segunda máquina, foram instalados Python 3.12.10 e um `.venv` isolado, sem herança de pacotes. As dependências mínimas para o percurso e a suíte foram instaladas sem os pins de API do CI; versões e plataforma estão no [inventário desta retomada](evidencias-c01/ambiente-geracao.json). Não houve alteração em Python funcional nem no menu ou documento durante a retomada. O executor é instrumento de avaliação e foi ampliado para registrar o percurso real e permitir selecionar um modelo somente no processo experimental.

A primeira tentativa recuperou o documento, mas recebeu HTTP 404 ao chamar `llama-3.3-70b-versatile` (`NotFoundError`). A [listagem autenticada de modelos](evidencias-c01/modelos-groq.json) funcionou e não apresentou esse identificador. Não se conclui que ele foi descontinuado globalmente; a evidência mostra indisponibilidade para esta chamada e conta. Na primeira versão do instrumento, a exceção foi registrada e convertida em `None`, produzindo o fallback de informação ausente. Esse fallback no artefato da tentativa original decorre da instrumentação, não demonstra o tratamento nativo de falhas remotas da aplicação. O executor foi ajustado para propagar uma exceção sanitizada nas próximas falhas.

No ensaio complementar, o executor selecionou `openai/gpt-oss-120b`, presente na listagem, sem editar `app/core/rag_pipeline.py`. Foram verificados os estados do percurso `/menu → 4 → 17 → 1 → 0 → 0`, com usuário sintético e SQLite em memória. O índice manteve 17 documentos e 39 chunks, e o documento C01 foi recuperado na primeira posição. A montagem registrou 31.358,45 ms; esse tempo inclui embeddings e indexação, não mede isoladamente latência de geração. Não comparar diretamente com a primeira máquina como ganho de desempenho.

Resposta do NLP, preservada integralmente no artefato:

> A finalidade do Serviço Experimental C01 é **verificar a inclusão de um serviço no menu e o encaminhamento de consulta documental na avaliação arquitetural C01**.

| Critério de análise | Observação |
|---|---|
| Explicar a finalidade experimental | Atendido; resposta corresponde à finalidade do TXT |
| Explicitar que o serviço é fictício | Não explicitado na resposta gerada; o menu exibido imediatamente antes contém essa indicação |
| Não inventar atendimento, contato ou orientação clínica | Nenhuma dessas invenções foi observada nesta resposta |
| Preservar navegação após consulta real | Atendido nas duas etapas de retorno registradas |

A resposta foi fiel à pergunta sobre finalidade, com ressalva quanto à ausência de advertência explícita de ficção no texto gerado. Essa única observação não mede confiabilidade geral do modelo. A coleta do C01 é encerrada com esses limites registrados; adequar o modelo padrão da aplicação é uma manutenção posterior, fora da mudança funcional delimitada pelo ensaio. A [análise para o TCC](C01-analise-resultados.md) consolida a interpretação.

## Reprodução

Na raiz do projeto, executar com o Python do ambiente preparado:

```powershell
.\.venv\Scripts\python docs/avaliacao/evidencias-c01/executar.py B
# Configuração original: nesta retomada retornou 404
.\.venv\Scripts\python docs/avaliacao/evidencias-c01/executar_rag.py --gerar
# Ensaio complementar: modelo selecionado apenas neste processo
.\.venv\Scripts\python docs/avaliacao/evidencias-c01/executar_rag.py --gerar --modelo openai/gpt-oss-120b
```

Os executores sobrescrevem os arquivos de resultado da variante escolhida e `rag-real.json`; copiar as evidências antes de repetir. `baseline` deve ser executado sobre o commit inicial; `A`, sobre o estado do patch A; `B`, sobre a alteração completa. Usar a variante A sobre o JSON final não reproduz o artefato histórico de A. Os patches preservam os estágios sem exigir commits intermediários. O arquivo histórico de recuperação e a tentativa com modelo original foram preservados separadamente.
