# C03 — Disponibilidade: protocolo de falhas controladas

Registro em 08/11/2026, antes da coleta. Plano: [árvore de utilidade](arvore-de-utilidade.md#c03--disponibilidade-continuidade-após-falha-externa). Condução pelo autor com assistência de IA.

## Pré-requisitos e corte

C01 está encerrado com ressalvas desde 19/10/2026, conforme sua [análise](C01-analise-resultados.md#fechamento). C02 está encerrado com ressalvas desde 05/11/2026, conforme seu [relatório](C02-relatorio-execucao.md). Não dependem de corrigir o modelo padrão para iniciar C03. Os 244 testes passaram na verificação inicial desta etapa.

- Corte: `666b60175f8e16c6678ae3da3aca975ae2a4fa5e`; branch `experimento/c03-disponibilidade`. Python funcional, menus, documentos e testes têm o mesmo conteúdo do corte C02 (`46a87a7`), conferido por `git diff`.
- Windows local, Python 3.12.10 em `.venv`; versões efetivas, commit, estado do Git e SHA-256 dos arquivos avaliados e instrumentos por lote em `ambiente.json`.
- Aplicação representada por chamadas diretas ao `ChatService`, após preparação do NLP e do cliente. Sem servidor HTTP, gateway, embeddings ou execução de `setup_system()`.
- Banco SQLite em memória por caso, com modelos, sessão, persistência e auditoria reais. Usuário sintético `Teste C03` e chat já criados e confirmados. A mesma sessão e usuário permanecem durante falha e retomada; o instrumento não faz rollback nem altera o estado entre essas etapas.
- O `.env` não é carregado pelo instrumento: a importação do pipeline ocorre com `load_dotenv` neutralizado. Uma credencial sintética substitui `GROQ_API_KEY` somente no processo; nenhuma credencial real é necessária. Conexões de socket e resolução DNS são bloqueadas durante preparação e execução; tentativas são registradas e invalidam o lote.

O loop `asyncio` é criado antes de ativar o bloqueio e fechado depois de desativá-lo: no Windows, sua infraestrutura usa um par de sockets locais. O cliente, o NLP e todas as mensagens são preparados/executados dentro do bloqueio. O tracing externo do LangChain fica desativado no processo.

## Fronteiras preservadas e substituídas

Executar o `ChatService`, interpretador de menu, `NLPService`, `run_rag`, prompt, composição LangChain e cliente `ChatGroq` reais. O retriever é um `RunnableLambda` local que devolve um documento sintético fixo; não se avalia recuperação vetorial neste cenário.

Injetar a falha no método síncrono `llm.client.create` (SDK Groq, `chat.completions.create`), depois da composição do prompt. Construir `APITimeoutError`, `APIConnectionError` ou `NotFoundError` reais do SDK com requisição/resposta HTTP sintéticas. Não substituir `run_rag` nem `NLPService.process` por um gerador de falhas. Um envelope de observação chama o NLP real, registra a exceção e relança o mesmo objeto; nunca a converte em `None`.

Esta fronteira preserva o tratamento de erros da aplicação e do adaptador LangChain, mas substitui os internals HTTP/retries do SDK. O timeout é imediato, sem espera; o 404 representa modelo indisponível na chamada e não verifica o catálogo atual do provedor. O modelo configurado no corte é mantido, sem geração real.

## Entradas, ordem e retomada

[casos.json](c03/casos.json) fixa as entradas e a ordem. Duas repetições, cada uma com timeout, conexão e modelo indisponível; para cada falha, executar menu e texto livre nessa ordem: **3 falhas × 2 percursos × 2 repetições = 12 casos**. Não há aquecimento, cronômetro de desempenho nem repetição seletiva.

| Percurso | Estado inicial | Mensagem | Consulta esperada no prompt |
|---|---|---|---|
| Menu com `query` | `WAITING_1_1_INFO` | `1` | Onde posso agendar Exames e Consultas? |
| Texto livre | `WAITING_MAIN_MENU` | Onde posso agendar Exames e Consultas? | Onde posso agendar Exames e Consultas? |

Após a falha, manter a injeção ativa e enviar ao mesmo usuário:

1. `/menu` → `WAITING_MAIN_MENU`, com o texto do menu principal.
2. `4` → `WAITING_4_SERVICOS`, com o texto exato do menu de serviços.
3. `2` → `WAITING_4_2_CEMERF`, com o texto exato dessa opção estática.
4. `0` → `WAITING_4_SERVICOS`, com o texto exato do menu de serviços.

São 60 mensagens no total: 12 estímulos de falha e 48 interações de retomada. Instanciar `ChatService` por mensagem, como na entrada da aplicação, sem reiniciar o processo nem substituir o NLP. Confirmar estado via nova consulta ao banco após cada mensagem. Registrar respostas completas, exceções, chamadas NLP/SDK, estado, mensagens persistidas e eventos de auditoria por etapa. Conservar os logs Python em `aplicacao.log`, com dados exclusivamente sintéticos.

## Critérios definidos antes da coleta

- **Injeção válida:** exatamente uma recuperação local e uma chamada SDK por estímulo; prompt contém consulta e marcador do documento; o NLP relança o mesmo objeto de exceção injetado. Zero tentativas de rede. Falha de instrumentação impede julgar o cenário, em vez de virar evidência favorável.
- **Retorno controlado:** a chamada ao `ChatService` devolve `ChatResponse` com texto não vazio, sem propagar exceção ao chamador. Este critério é operacional; não exige uma redação específica da resposta.
- **Estado preservado:** estado persistido após a falha é igual ao inicial, e identidade/nome do usuário permanecem iguais após todas as etapas.
- **Continuidade estática:** as quatro etapas posteriores devolvem os estados/textos previstos, com um par de mensagens usuário/bot persistido e `MESSAGE_SENT`, sem `MESSAGE_FAILED`, sem NLP/SDK adicionais. Nenhum reparo pelo instrumento entre falha e retomada.
- **Julgamento principal:** atendido no recorte se os 12 casos válidos satisfizerem retorno controlado, estado e continuidade; parcialmente atendido se houver resultados mistos; não atendido se nenhum caso satisfizer; não avaliado se a coleta estiver incompleta ou inválida.
- **Ressalvas obrigatórias, separadas do critério de continuidade:** descrever se a resposta informa uma falha ou atribui o problema à entrada, se há instrução de retomada, se a auditoria distingue geração falha e se o diálogo registra a resposta efetivamente devolvida. Não confundir `MESSAGE_SENT` com geração bem-sucedida. Um retorno operacionalmente controlado pode ser inadequado ao usuário.

## Reprodução e preservação

Da raiz do repositório, com dependências de API e `langchain-core`, `langchain-groq`, `groq` e `httpx` já instaladas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q docs/avaliacao/c03/test_executor.py
.\.venv\Scripts\python.exe docs/avaliacao/c03/executar.py
```

O executor cria um diretório único em `evidencias-c03/`. Guarda cópias de protocolo, casos e executor, inventário/hashes, `casos-executados.json`, `resumo.json`, `aplicacao.log` e `execucao.json`. Código de saída 0 indica coleta válida e completa, inclusive se o julgamento arquitetural for parcial ou não atendido; 1 indica impedimento/instrumentação inválida. Não sobrescrever lotes anteriores. Os testes do instrumento são verificação prévia e não integram os 12 casos coletados.

## Limites

O recorte verifica contenção de exceções e continuidade após falhas imediatas em aplicação preparada. Não mede tempo até timeout, retries, percentuais de disponibilidade, SLA, recuperação de processo, falhas no boot, concorrência, entrega WhatsApp, banco PostgreSQL nem fidelidade de uma resposta gerada. O bloqueio de rede evita chamadas acidentais; não é uma avaliação de segurança. Nenhum Python funcional será corrigido durante esta coleta; melhorias devem ser propostas separadamente.
