# C04 — Testabilidade do núcleo RAG: relatório de execução

**Encerrado com ressalvas em 09/11/2026. Critério atendido no recorte: 16/16 casos aprovados, sem credenciais, rede, pesos de modelos ou alteração de Python funcional.** O [protocolo](C04-protocolo.md) e os casos foram fixados antes da coleta. O resultado demonstra isolamento dos componentes exercitados com substitutos externos; não comprova qualidade semântica da recuperação nem fidelidade de respostas de um modelo real.

## Procedimento e referência

Avaliação conduzida pelo autor com assistência de IA, na branch `experimento/c04-testabilidade`, sobre o conteúdo funcional de `77348fbf3294714bdd336432d0c88b225ed6a001`. Novos arquivos são protocolo, instrumentos, relatório e evidências. O código em `app/`, `api/`, a base em `data/` e os testes existentes permanecem preservados. Os manifestos identificam arquivos ainda sem commit; hashes e cópias fixam o que foi executado.

Lote único [20261109-161456-offline-af50da](evidencias-c04/20261109-161456-offline-af50da/), iniciado às 16:14:56 em America/Sao_Paulo (19:14:56 UTC). Windows 11, Python 3.12.10, LangChain Core 1.7.3, LangChain Community 0.4.2, LangChain Groq 1.1.3, FAISS CPU 1.15.1 e coverage 7.17.0; inventário completo em [ambiente.json](evidencias-c04/20261109-161456-offline-af50da/ambiente.json). Pacotes já instalados, sem instalação durante a coleta e sem alteração do CI.

O executor abriu um processo novo com ambiente construído por lista permitida de variáveis essenciais do Windows, sem herdar chaves/tokens, configuração de modelo ou banco. O `.env` foi neutralizado antes das importações da aplicação. Cinco diretórios de cache novos estavam vazios antes e depois. Socket/DNS/UDP e criação de subprocessos/comandos foram bloqueados no processo medido. Houve **zero tentativas externas**, **zero credenciais presentes** e uma chamada a `load_dotenv` suprimida. Esses registros estão em [isolamento.json](evidencias-c04/20261109-161456-offline-af50da/isolamento.json); não houve inferência nem download de pesos.

## Resultados por componente

| Componente/casos | Execução observada | Resultado |
|---|---|---|
| Ingestão — I01/I02 | DirectoryLoader/TextLoader reais leram dois TXT UTF-8 com origem/conteúdo conferidos; ignoraram MD; diretório ausente produziu FileNotFoundError | 2/2 |
| Chunking — D01 | Dois documentos geraram dez chunks, todos até 1000 caracteres, com conteúdo/origem preservados; sobreposições observadas de 115 e 121 caracteres | 1/1 |
| Indexação e recuperação — R01/R02 | FAISS real com dez vetores; buscas Aurora e Horizonte devolveram primeiro o respectivo documento | 2/2 |
| Montagem e configuração — B01/B02 | `setup_system()` executou todas as etapas, produziu `servicos`, métricas e retriever utilizável; adaptador encaminhou configuração padrão e explícita ao construtor substituto | 2/2 |
| Prompt, parser e ausência — P01/P02/P03 | Pergunta e contexto recuperado chegaram ao prompt real; AIMessage sintética virou string; contexto vazio e resposta vazia foram processados pelo NLP real como None | 3/3 |
| Exceções — E01/E02 | Mesmo objeto de erro do gerador atravessou chain/NLP; erro de `embed_query` atravessou FAISS/chain/NLP sem chamar o gerador | 2/2 |
| Fábrica e entrada vazia — L01/L02 | Sem chave/cache, fábrica original produziu ValueError local; entrada vazia retornou localmente, sem consulta vetorial ou geração | 2/2 |
| Saudação e personalização — N01/N02 | Prompt de saudação, parser e personalização institucional/genérica reais; saudação não consultou o índice | 2/2 |
| **Total** | Uma passagem, ordem fixa, sem repetição seletiva | **16/16** |

O corpus contém somente os serviços fictícios Aurora e Horizonte, com parágrafos numerados e marcadores próprios. Os embeddings locais contam ocorrências dos nomes dos serviços e normalizam os vetores. Isso torna verificável o caminho pelo índice, sem representar embeddings semânticos de produção. As buscas discriminantes usam `k=1`; a montagem conserva o padrão `k=10`. Um filtro de metadados sem correspondência produz recuperação vazia pelo FAISS real.

O gerador local captura o prompt e retorna uma AIMessage fixada ou lança a exceção definida. `run_rag`, `build_rag_chain`, prompts, StrOutputParser, `NLPService`, reconhecimento da frase de ausência e personalização não foram substituídos. A saída de ausência é imposta pelo instrumento: seu reconhecimento não demonstra que um modelo real escolheria abster-se. Os registros completos estão em [casos-executados.json](evidencias-c04/20261109-161456-offline-af50da/casos-executados.json).

## Esforço de isolamento e interpretação arquitetural

| Fronteira | Ajuste necessário no teste | Implicação |
|---|---|---|
| Origem dos documentos | Atribuir temporariamente a `ingestion.__file__` um caminho na raiz sintética | O loader é real, mas o diretório não é parâmetro público; o teste conhece a resolução interna de caminho |
| Embeddings | Substituir o construtor `HuggingFaceEmbeddings` por embeddings locais | A configuração do adaptador e a montagem continuam reais; carregamento/tokenização/inferência do modelo treinado ficam fora |
| Gerador | Preencher temporariamente `rag_pipeline.CACHED_LLM` com Runnable local | Permite testar composição/parser sem chave, mas depende de estado global interno e restauração entre casos |
| Erro de recuperação | Fazer o substituto de embeddings lançar em `embed_query` | Busca FAISS, chain e propagação de exceção permanecem reais |

Esses ajustes alteram objetos somente no processo de teste, com restauração por fixture; não editam os fontes funcionais. A fábrica original sem chave não se torna utilizável por si só: o caso L01 demonstra esse limite. O sucesso dos demais casos depende da atribuição ao cache global, que `get_llm()` consulta antes de exigir credencial. Não há interface pública de injeção do gerador implementada por este ensaio.

A arquitetura permite exercitar o núcleo além da navegação com NLP totalmente falso, atendendo ao critério definido. O custo é conhecimento de detalhes internos e disciplina de isolamento. Como melhorias posteriores, pode-se receber o diretório de documentos explicitamente e permitir fornecer cliente/fábrica geradora, mantendo os padrões de operação. Também se pode incorporar uma suíte offline ao CI com dependências identificadas. Nenhuma dessas mudanças foi aplicada ou comparada, e não houve medição separada de esforço humano.

## Cobertura do lote

Cobertura de linhas e ramos medida somente nos 16 casos, com importações da aplicação dentro da medição. Denominadores incluem módulos não exercitados de ambos os pacotes; migrações são omitidas como no projeto. Os 244 testes existentes foram executados separadamente e não estão somados a esses números.

| Escopo | Linhas executadas/executáveis | Cobertura de linhas | Ramos executados/possíveis | Cobertura de ramos |
|---|---:|---:|---:|---:|
| `app/` completo | 105/110 | 95,45% | 15/18 | 83,33% |
| `api/` completo | 21/520 | 4,04% | 9/114 | 7,89% |
| `app/core/rag_pipeline.py` | 31/34 | 91,18% | 7/8 | 87,50% |
| `api/services/nlp_service.py` | 21/22 | 95,45% | 9/10 | 90,00% |

Ingestão, splitter, vector store, adaptador de embeddings e montagem tiveram todas as suas linhas executáveis cobertas, incluindo chamadas aos substitutos nas fronteiras. Essa cobertura não significa exercício do código externo do modelo/SDK. O corpo que constrói o ChatGroq real ficou sem cobertura; também restaram dois caminhos de intenção e o retorno sem personalização de `_personalizar`. Não foi ampliada a matriz depois da coleta para elevar o percentual.

A baixa cobertura global de `api/` reflete o escopo concentrado em `NLPService`: rotas, ChatService, banco e auditoria não fazem parte destes casos. Não indica regressão de cobertura da suíte existente. O relatório textual de coverage combina linhas e ramos na coluna `Cover`; por isso seus percentuais diferem dos percentuais de linhas acima. Dados individuais e agregados em [cobertura.json](evidencias-c04/20261109-161456-offline-af50da/cobertura.json), [resumo por pacote](evidencias-c04/20261109-161456-offline-af50da/cobertura-por-pacote.json) e [relatório textual](evidencias-c04/20261109-161456-offline-af50da/cobertura.txt).

## Verificações, limites e fechamento

Antes da coleta, **13 verificações do instrumento** e **244 testes existentes** passaram; lint e compilação dos instrumentos foram concluídos ([registro](evidencias-c04/verificacao-previa.txt)). As verificações do instrumento conferem bloqueio de DNS/conexão/UDP/subprocesso/comando, limpeza do ambiente, ciclo isolado e rejeição de evidências incompletas. Esse ciclo prévio ocorreu em diretório temporário e não foi somado à amostra. O pytest do lote registrou 16 aprovados e um DeprecationWarning no import de `HuggingFaceEmbeddings` ([saída](evidencias-c04/20261109-161456-offline-af50da/pytest.txt)); o aviso não impediu a execução.

A [conferência posterior](evidencias-c04/validacao-evidencias.json) verifica hashes/cópias, corpus, ordem e resultados dos casos, isolamento, contagens de cobertura e fontes preservadas, sem repetir a coleta. O [índice de evidências](evidencias-c04/README.md) localiza os artefatos. As fontes/instrumentos usados na coleta são preservados no lote; o conferidor foi criado depois e não integra o manifesto prévio.

Uma execução local, corpus pequeno, embeddings lexicais e respostas impostas pelo instrumento não avaliam relevância semântica geral, fidelidade documental, qualidade clínica, SDK/HTTP/retries, entrega WhatsApp, banco, concorrência, boot da API ou ambiente do CI. O bloqueio é realizado dentro do processo Python para os caminhos exercitados, não por firewall de sistema nem como garantia de segurança contra código nativo arbitrário. Caches de pesos vazios não significam ausência de bibliotecas instaladas. Tempos do pytest ou da montagem com substitutos não devem ser apresentados como desempenho do chatbot real.

**C04 está concluído, atendido no recorte e com ressalvas de acoplamento e alcance.** O núcleo selecionado pôde ser testado sem alterar Python funcional e sem depender de credenciais/rede/pesos durante a execução. C05 pode partir da referência preservada para avaliar recuperação e respostas de um modelo real, com corpus, perguntas e critérios próprios definidos antes de sua coleta.
