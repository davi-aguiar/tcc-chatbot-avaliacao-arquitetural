# C02 — Desempenho: protocolo de coleta

Registro em 03/11/2026, antes das medições. Plano: [árvore de utilidade](arvore-de-utilidade.md#c02--desempenho-processamento-e-inicialização). Condução pelo autor com assistência de IA.

## Corte e ambiente

- Corte do GitHub: `46a87a7` (`origin/main`, conferido com `git fetch origin`); branch de trabalho `experimento/c02-desempenho`.
- Python funcional, menus e documentos permanecem nessa versão. Os novos arquivos são instrumentos, protocolo e evidências de avaliação. O manifesto guarda o hash completo do commit e SHA-256 dos arquivos avaliados e instrumentos.
- Windows local, Python 3.12.6 no ambiente existente `.venv-c01`, com dependências herdadas do Python do sistema. Inventário completo por lote em `ambiente.json`. Não equivale ao ambiente do CI.
- Banco SQLite em memória, descartável, com os modelos e auditoria reais; não representa PostgreSQL de produção. Nenhum acesso ao banco definido em `DATABASE_URL`.
- Chamadas diretas ao `ChatService`, sequenciais, sem servidor HTTP e sem gateway WhatsApp. Não mede rede de entrada/entrega ao aparelho.
- Embeddings padrão do corte, salvo configuração prévia identificada no manifesto; somente cache local (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`). Ausência de cache produz impedimento/falha, sem download durante a série.
- Geração real: modelo padrão `llama-3.3-70b-versatile`, temperatura 0,1, até 500 tokens. Registrar parâmetros efetivos de timeout e retries da biblioteca em `modelo.json`. Não presumir disponibilidade pelo ensaio C01. Modelo alternativo somente como configuração adaptada, em lote separado e identificado por `--modelo`.

## Entradas, estados e ordem fixados

O arquivo [casos.json](c02/casos.json) fixa nove entradas e seus estados iniciais e esperados. Três casos por percurso:

| Caso | Percurso | Estado inicial | Entrada |
|---|---|---|---|
| E1 | Estático | `WAITING_MAIN_MENU` | `1` — Agendamento |
| E2 | Estático | `WAITING_MAIN_MENU` | `4` — Serviços |
| E3 | Estático | `WAITING_4_SERVICOS` | `2` — CEMERF |
| M1 | Menu RAG | `WAITING_1_1_INFO` | `1` — Onde agendar exames e consultas |
| M2 | Menu RAG | `WAITING_1_1_INFO` | `4` — Documentos obrigatórios para marcação |
| M3 | Menu RAG | `WAITING_4_4_CEO` | `1` — O que é o serviço CEO |
| L1 | Texto livre | `WAITING_MAIN_MENU` | Onde posso agendar Exames e Consultas? |
| L2 | Texto livre | `WAITING_MAIN_MENU` | Quais documentos são obrigatórios para qualquer marcação? |
| L3 | Texto livre | `WAITING_MAIN_MENU` | O que é o serviço CEO? |

Cada caso tem um usuário sintético e chat previamente criados. Antes de cada mensagem, restaurar o estado inicial fora do intervalo cronometrado. Nome sintético `Teste C02`. Conversas e auditoria crescem no banco ao longo do lote; esse efeito e a ordem fixa devem constar dos limites. Não há onboarding incluído nas 45 mensagens.

Executar uma passagem de aquecimento por todos os casos do lote, separada da medição. Depois executar cinco rodadas, cada uma percorrendo os casos na ordem da tabela. Total previsto: 45 mensagens medidas, até 30 com geração. Aquecimento completo pode adicionar seis gerações, fora das 30 medidas. Sem pausa artificial ou repetição seletiva de falhas; retries internos do SDK integram a duração e devem ser identificados.

Como a credencial está ausente na inspeção inicial, a navegação será coletada primeiro com `--escopo estatico` (3 aquecimentos + 15 medidas), sem carregar o RAG. O lote `--escopo rag` terá 6 aquecimentos + 30 medidas, com índice e NLP reais no mesmo processo. São lotes distintos, com inventários e horários próprios; não alegar execução contínua única. A navegação isolada também não representa memória/CPU concorrente de uma API com RAG residente. A falta de chave é impedimento de preparação, não 30 falhas medidas. Havendo interesse em um regime único, executar `--escopo todos` como nova série, preservando a anterior.

## Inicialização

Executar uma preparação/verificação com cache e, depois, três chamadas reais a `setup_system()` em processos Python novos e sequenciais. Guardar a preparação separada. Cada processo deve construir o índice e recuperar documentos para a consulta fixa `O que é o serviço CEO?`; a verificação ocorre fora do tempo de `setup_system()`.

Registrar todas as etapas de `METRICAS_INDEXACAO`, documentos/chunks e duração externa do processo. O intervalo externo inclui importações, consulta de verificação e encerramento, e não deve ser chamado de tempo de montagem do índice. Processos têm limite operacional de 900 segundos; interrupções são falhas, sem classificação como respostas rápidas. Se a preparação não encontrar cache utilizável, interromper a série e registrar o impedimento.

## Medidas e julgamento

- Guardar as durações existentes de aplicação e RAG em `MESSAGE_SENT`, eventos de falha e duração externa da chamada. O intervalo externo inclui o commit final da auditoria; `duracao_total_ms` é obtida antes desse commit.
- A auditoria real permanece ativa no banco. O instrumento desabilita emissão de logs Python no lote de mensagens para evitar registrar detalhes de exceções remotas; isso reduz custo de console e deve ser considerado na interpretação. A inicialização em subprocessos conserva seus logs. Nenhum resultado representa desempenho com uma configuração de logging de produção não identificada.
- Um envelope de observação chama o `NLPService` real e relança a mesma exceção. Guarda consulta, ausência de resposta e tipo de erro. Não transforma exceções em `None`. Isso detecta falhas de texto livre que o próprio `ChatService` captura e pode registrar como `MESSAGE_SENT`.
- Sucesso operacional: estado esperado, exatamente um `MESSAGE_SENT`, nenhum `MESSAGE_FAILED`, nenhuma exceção e comportamento do percurso conferido. Estático: texto do destino exato e zero chamadas NLP. RAG: uma chamada com pergunta prevista e resposta não vazia. Ausência de contexto é contada separadamente pelos registros como percurso sem resposta, sem julgamento clínico ou de fidelidade documental.
- Manter valores individuais e falhas. Resumir quantidade, mediana, mínimo e máximo dos sucessos por caso e percurso; durações externas das falhas ficam separadas. Sem p95/p99, capacidade sob carga, teste de simultaneidade ou requisito arbitrário de latência.
- Não alterar Python funcional durante a coleta. Novas configurações ou correções exigem identificação em nova série. O C02 é descritivo, sem atribuição de aprovação por rapidez.

## Comandos e artefatos

Na raiz do repositório:

```powershell
.\.venv-c01\Scripts\python -m pytest -q
.\.venv-c01\Scripts\python docs/avaliacao/c02/executar.py mensagens --escopo estatico
.\.venv-c01\Scripts\python docs/avaliacao/c02/executar.py inicializacao
# Após disponibilizar GROQ_API_KEY no .env local:
.\.venv-c01\Scripts\python docs/avaliacao/c02/executar.py mensagens --escopo rag
```

Cada execução cria diretório único em `evidencias-c02/`, sem sobrescrever tentativas. Artefatos: inventário e hashes, entradas, mensagens/aquecimento e auditoria estruturada, CSV de medidas, resumo e status. Inicialização: preparação, três resultados, logs e resumo. As respostas são sintéticas e ficam no artefato para conferência, sem envio ao WhatsApp.

Ver o [relatório](C02-relatorio-execucao.md) para estado efetivo da execução. Ausência de coleta permanece não avaliada.

## Adendo de preparação — 03/11/2026, antes da série de inicializações

A preparação padrão falhou com `OfflineModeIsEnabled`. O diagnóstico local mostrou chamada de `transformers.tokenization_utils_base._patch_mistral_regex` a `model_info` do Hub, mesmo com pesos presentes. A tentativa e o traceback foram preservados. Não houve inicialização medida bem-sucedida nessa configuração.

Na nova série, configurar `EMBEDDINGS_MODEL` com o caminho absoluto do snapshot já existente do **mesmo** modelo padrão, revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. O adaptador funcional já aceita essa variável; nenhum Python funcional ou pacote será alterado. A inicialização deve continuar offline. Identificar como configuração local adaptada para carregamento dos mesmos pesos, sem generalizar o resultado para resolução do identificador remoto. Inventariar arquivos, tamanhos e hashes do snapshot antes da nova coleta.

```powershell
$env:EMBEDDINGS_MODEL = Join-Path $env:USERPROFILE '.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
.\.venv-c01\Scripts\python docs/avaliacao/c02/executar.py inicializacao
```

Os lotes anteriores conservam cópia de `protocolo-original.md`, cujo hash corresponde aos seus manifestos. Este adendo precede a nova série; resultados anteriores não serão reclassificados.

## Adendo de nova série em outra máquina — 05/11/2026, antes da coleta

O autor decidiu refazer a coleta completa em uma segunda máquina (Windows 11, Intel Core i7-6700, 8 CPUs lógicas), pois a credencial só estava disponível nela e a [árvore de utilidade](arvore-de-utilidade.md#c02--desempenho-processamento-e-inicialização) prevê uma máquina identificada. Os lotes de 03/11/2026 são preservados, sem reclassificação, e não são somados nem comparados diretamente aos novos.

**Mantido:** casos, ordem, aquecimento, cinco rodadas, instrumento e critérios deste protocolo. O Python funcional, os menus e os documentos têm o conteúdo do corte `46a87a7`: conferência contra o manifesto anterior encontrou 64 de 67 arquivos idênticos em bytes; `casos.json`, `executar.py` e este protocolo diferem apenas pelo CRLF do checkout com `core.autocrlf=true` ([conferência](evidencias-c02/maquina2-preparacao/hashes-corte.json)). Este adendo altera o protocolo e por isso o commit dos novos manifestos é posterior a `46a87a7`.

**Ambiente adaptado:**

- Branch `experimento/c02-desempenho`, criada nesta máquina. O commit anterior `efb274f` havia sido integrado à `main`, sem a branch citada acima no remoto.
- Python 3.12.6 em `.venv` isolado, instalado com `uv`, sem herança de pacotes. As versões seguem o [inventário anterior](evidencias-c02/maquina2-preparacao/constraints.txt), usando a versão mais nova onde o inventário registrava duas (`idna`, `langchain-core`, `langsmith`). Só os pacotes necessários foram instalados (121, contra 160 listados antes); cada lote guarda o próprio inventário.
- Embeddings baixados nesta preparação, fora de qualquer série, na mesma revisão `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Os dez arquivos conferem em tamanho e SHA-256 com o [inventário anterior](evidencias-c02/cache-embeddings.json) ([conferência](evidencias-c02/maquina2-preparacao/cache-embeddings.json)). `EMBEDDINGS_MODEL` aponta para o snapshot em todos os lotes, inclusive os de mensagens, cujo comando original omitia essa variável.
- Máquina de uso geral, com aplicativos do usuário abertos e sem isolamento de processos.
- Validação prévia: 244 testes do projeto e 4 do instrumento passaram ([registro](evidencias-c02/maquina2-preparacao/verificacao-testes.txt)).

**Modelo.** A listagem da API Groq em 05/11/2026 não inclui `llama-3.3-70b-versatile` e inclui `openai/gpt-oss-120b` ([listagem](evidencias-c02/maquina2-preparacao/modelos-groq.txt)). A listagem não substitui a tentativa: primeiro executar o modelo padrão, preservando o resultado. Se este não concluir as gerações, executar nova série com `openai/gpt-oss-120b`, identificada como configuração adaptada e escolhida por ter sido o modelo do ensaio C01. Outro modelo exigiria novo registro. Limites de uso do provedor (HTTP 429) contam como falhas, sem pausas ou repetição seletiva; se impedirem a série, registrar o resultado antes de decidir nova tentativa.

**Comandos**, nesta ordem, em regime único por lote (`--escopo todos`):

```powershell
$env:EMBEDDINGS_MODEL = Join-Path $env:USERPROFILE '.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
.\.venv\Scripts\python docs/avaliacao/c02/executar.py inicializacao
.\.venv\Scripts\python docs/avaliacao/c02/executar.py mensagens --escopo todos
# Somente se o modelo padrão não concluir as gerações:
.\.venv\Scripts\python docs/avaliacao/c02/executar.py mensagens --escopo todos --modelo openai/gpt-oss-120b
```

O lote `20261103-170640-inicializacao-todos-64f9d8` recebeu a cópia `protocolo-original.md` (reconstituída do Git com fim de linha LF), cujo hash corresponde ao seu manifesto.
