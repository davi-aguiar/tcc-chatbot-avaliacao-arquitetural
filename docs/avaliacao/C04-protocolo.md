# C04 — Testabilidade do núcleo RAG sem rede

Protocolo fixado em 09/11/2026, antes da coleta. Condução pelo autor com assistência de IA. Plano: [árvore de utilidade](arvore-de-utilidade.md#c04--testabilidade-rag-sem-dependências-externas-em-execução).

## Corte e pergunta

Referência funcional: `77348fbf3294714bdd336432d0c88b225ed6a001`; branch `experimento/c04-testabilidade`. C01–C03 estão encerrados com ressalvas. Não corrigir Python funcional, menus, documentos da base ou testes existentes durante C04. Instrumentos e documentos de avaliação são contabilizados separadamente. Registrar hashes, versões, estado do Git e cópias dos instrumentos antes de executar a série.

É possível exercitar ingestão, chunking, índice/recuperação, prompt e adaptação da resposta reais sem rede, credenciais ou pesos de modelos, apenas substituindo as dependências externas e ajustando o diretório de entrada no processo de teste?

## Ambiente e isolamento

- Windows local e `.venv` já preparado. Não instalar pacotes durante a coleta. Inventário efetivo em cada lote, sem alegar equivalência ao CI.
- Novo processo Python, com ambiente construído por lista de variáveis essenciais do Windows. Não herdar chaves, tokens, `DATABASE_URL`, configuração de modelo, tracing ou caminhos de cache do processo pai. Não registrar valores de credenciais.
- `.env` desabilitado por `PYTHON_DOTENV_DISABLED=1` e por substituição de `dotenv.load_dotenv` antes de importar a aplicação. Tracing e telemetria externos desabilitados; plugins automáticos do pytest desabilitados.
- Caches Hugging Face, Sentence Transformers, Torch e XDG apontam para diretórios novos e inicialmente vazios no lote. Modos offline do Hub/Transformers ativos. Inventariar os arquivos desses caches antes e depois; nenhum peso preexistente pode participar.
- Bloquear conexões, resolução DNS e envio UDP por socket durante importação da aplicação e execução dos casos. Bloquear subprocessos/comandos nesse intervalo para impedir escape desse bloqueio. Guardar tentativas sem argumentos sensíveis; qualquer tentativa invalida o isolamento, ainda que o erro seja capturado por alguma biblioteca.
- Sem HTTP, gateway, banco de produção ou inferência real. A coleta não mede desempenho nem disponibilidade.

## Componentes e substituições

| Componente | Execução real | Substituição/ajuste no processo |
|---|---|---|
| Ingestão | `load_servicos`, DirectoryLoader e TextLoader | Dois TXT sintéticos em diretório de ensaio; `ingestion.__file__` aponta para a raiz sintética, pois o diretório é calculado a partir do módulo |
| Chunking | `split_docs` e RecursiveCharacterTextSplitter, 1000/200 caracteres | Nenhuma |
| Embeddings | `get_embeddings` e leitura de configuração | Construtor `HuggingFaceEmbeddings` devolve embeddings lexicais determinísticos locais, sem pesos |
| Índice e recuperação | `create_vector_store`, FAISS, `create_retriever` e busca | Vetores locais; `k=1` para discriminar documentos; filtro de metadados impossível para obter contexto vazio |
| Montagem | `setup_system` e todas as etapas internas | Os mesmos ajustes de diretório e construtor de embeddings; não substituir etapas de montagem |
| Geração | `get_llm`, `build_rag_chain`, `run_rag`, prompts e StrOutputParser | `CACHED_LLM` recebe Runnable local que captura prompt e devolve AIMessage sintética ou lança a exceção fixada |
| Adaptação | `NLPService.process`, reconhecimento de ausência e personalização | Nenhuma substituição do NLP ou de `run_rag` |

O ajuste de `__file__` e a atribuição ao cache global não são interfaces públicas de injeção. Registrar esse acoplamento como custo do isolamento. Não confundir alteração temporária de objetos no teste com edição do Python funcional. O gerador falso não exercita ChatGroq/SDK/HTTP/retries nem avalia fidelidade de um modelo real. Os vetores lexicais não representam qualidade semântica dos embeddings de produção.

## Casos e resultados esperados, definidos antes da coleta

A matriz legível por máquina está em [casos.json](c04/casos.json). Uma passagem, ordem fixa, **16 casos**, sem aquecimento ou repetição seletiva:

| ID | Caso | Resultado esperado |
|---|---|---|
| I01 | Dois TXT e arquivo de outro tipo | Dois documentos UTF-8, conteúdo e metadados corretos; outro tipo ignorado |
| I02 | Diretório ausente | FileNotFoundError real |
| D01 | Divisão dos documentos longos | Mais chunks que documentos, até 1000 caracteres, origem preservada e sobreposição observada |
| R01 | Busca Aurora | FAISS real devolve documento Aurora em primeiro lugar |
| R02 | Busca Horizonte | FAISS real devolve documento Horizonte em primeiro lugar |
| B01 | Montagem com configuração padrão | Etapas reais, chave `servicos`, métricas e recuperação utilizáveis; construtor externo substituído |
| B02 | Configuração explícita de embeddings | Valor encaminhado pelo adaptador real ao construtor substituto |
| P01 | Resposta com contexto | Pergunta e documento recuperado chegam ao prompt; AIMessage vira string e NLP preserva resposta |
| P02 | Recuperação vazia | Contexto vazio chega ao gerador; frase sintética de ausência vira None no NLP |
| P03 | Resposta vazia do gerador | NLP devolve None |
| E01 | Exceção do gerador | Mesmo objeto de exceção atravessa pipeline e NLP |
| E02 | Exceção dos embeddings na busca | FAISS/chain/NLP propagam o mesmo erro; gerador não é chamado |
| L01 | Fábrica original sem chave e sem cache | ValueError local esperado, sem rede; documentar que a construção original exige credencial |
| L02 | Entrada vazia | Retornos locais previstos, sem embeddings de consulta nem geração |
| N01 | Saudação institucional sintética | Prompt de saudação real; parser e personalização institucional reais |
| N02 | Resposta com saudação genérica | Personalização por substituição de `Olá!`, preservando o restante |

Corpus fictício: serviços Aurora e Horizonte, sem dados pessoais ou instruções clínicas, com marcadores distintos e parágrafos numerados que forçam chunking. A saída dos geradores é fixada no instrumento antes da coleta. Asserções verificam passagem pelas fronteiras, além do texto final. A frase de ausência é imposta pelo substituto: seu reconhecimento comprova adaptação, não abstenção espontânea de um modelo.

## Critérios e evidências

Coleta válida exige os 16 casos identificados, resultados de teste completos, observações por caso, fontes funcionais preservadas, ausência de credenciais, caches inicialmente vazios e sem arquivos ao fim, zero tentativas de rede/subprocessos e cobertura produzida. Impedimento de importação ou falha do instrumento é **não avaliado**, não reprovação arquitetural.

Em coleta válida: **atendido no recorte** se todos os casos passarem sem alterar Python funcional; **parcialmente atendido** se houver resultados mistos; **não atendido** se nenhum passar. Uma exceção prevista corretamente observada é sucesso do respectivo caso. Código de saída 0 significa coleta válida e completa, mesmo com julgamento parcial; 1 significa impedimento/instrumentação inválida.

Preservar matriz componente/teste/substituto, corpus, prompts/respostas sintéticas, exceções, contagens de chamadas, resultados pytest, inventário do ambiente, isolamento e hashes. Medir cobertura de linhas e ramos separadamente para `app/` e `api/`, omitindo migrações como no projeto e sem meta arbitrária. Incluir módulos não exercitados no denominador e distinguir importação de exercício de operações. A cobertura do C04 não equivale à suíte de navegação nem comprova qualidade das respostas. Não misturar verificações do instrumento com os 16 casos arquiteturais.

## Comandos e preservação

```powershell
.\.venv\Scripts\python.exe -m pytest -q docs/avaliacao/c04/test_instrumento.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe docs/avaliacao/c04/executar.py
```

O executor cria um lote único em `evidencias-c04/`, sem sobrescrever resultados anteriores. Verificações prévias do instrumento usam diretórios temporários e não integram a coleta. Relatório e índices serão escritos depois dos resultados. C05 permanece responsável pela fidelidade documental de respostas reais; C06, pelo fluxo de dados e confidencialidade.
