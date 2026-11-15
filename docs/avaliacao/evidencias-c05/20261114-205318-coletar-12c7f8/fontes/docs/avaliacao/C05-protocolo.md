# C05 — Confiabilidade: fidelidade ao contexto documental

Protocolo definido em 12/11/2026 antes da coleta de respostas. Condução pelo autor com assistência de IA, com julgamento semântico a revisar pelo autor. Plano: [árvore de utilidade](arvore-de-utilidade.md#c05--confiabilidade-fidelidade-ao-contexto-documental).

## Pergunta e corte

As respostas do gerador ficam sustentadas pelo contexto efetivamente recuperado, distinguem serviços semelhantes e se abstêm quando a informação solicitada está ausente?

Referência funcional: `ffcd30fe07cbf281a030a14d481d3eee5533db5c`. Preservar os 17 TXT de `data/servicos`, inclusive o documento sintético do C01. Não editar aplicação, corpus, prompts, chunking, `k` ou testes existentes durante o cenário. Instrumentos e documentação novos são separados da referência funcional; cada lote guarda hashes e cópias das fontes e do instrumento efetivos. Alterações posteriores do protocolo exigem nova versão explícita, preservando lotes anteriores.

Este recorte avalia fidelidade documental, não a validade clínica ou a atualidade dos dados municipais. As perguntas são sintéticas; os endereços e informações são tratados como conteúdo da base de corte. Não há dados pessoais de usuários, recomendações clínicas ou avaliação de segurança adversarial.

**Ambiguidade identificada antes da geração:** `servico_ambulatorio_saude_mental_atencao_a_adultos.txt` tem título de Ambulatório de Saúde Mental, mas uma seção pergunta “Onde fica o CAPS II?” e fornece Avenida Olívia Flores, 3000. O documento específico do CAPS II fornece Avenida Régis Pacheco, 770. Preservar essa inconsistência e verificar se seus trechos chegam ao contexto de P03/P06. O gabarito usa a identidade do serviço no documento específico; uma resposta baseada na seção conflitante deve ser marcada como ambiguidade documental, com os dois trechos, sem atribuição automática de alucinação ao gerador. Se o contexto não permitir resolver a atribuição, o fato permanece indeterminado, impedindo aprovação global. O cenário também pode revelar risco de curadoria da base.

## Hipóteses arquiteturais

- Recuperação: os trechos necessários estão entre os documentos que chegam ao prompt. A fonte esperada estar presente não assegura que o chunk contenha a resposta.
- Geração: cada afirmação factual da resposta é sustentada por esse contexto e atribuída ao serviço correto. Um fato correto no corpus, mas ausente do contexto enviado, não está ancorado nesta execução.
- Abstenção: nos dois casos sem informação, o gerador comunica ausência sem acrescentar uma resposta factual inferida. Registrar separadamente a obediência à frase exigida e o reconhecimento por `sem_contexto`/`NLPService`.

O prompt é um mecanismo de orientação; a inspeção de seu texto não comprova as hipóteses. FAISS retorna os vizinhos mais próximos mesmo quando não há resposta documental; contexto não vazio também não comprova respondibilidade.

## Matriz fixada antes da coleta

A especificação detalhada, com trechos literais e fatos esperados, está em [casos.json](c05/casos.json).

| ID | Tipo | Pergunta e referência esperada |
|---|---|---|
| P01 | Respondível | Passos para realizar espirometria: solicitação médica, entrega na UBS, espera pelo contato e comparecimento ao CEMAE após agendamento |
| P02 | Respondível | Documentos do Programa Asma Grave, incluindo diagnóstico/CID e boleto de marcação |
| P03 | Respondível | Endereço e funcionamento do CAPS II, incluindo exceção de quinta-feira à tarde |
| P04 | Ausente | Número de horas de jejum para espirometria, não informado pelo corpus |
| P05 | Ausente | Prazo máximo em dias para realizar eletrocardiograma após entrega da solicitação, não informado pelo corpus |
| P06 | Distinção | Públicos e endereços do CAPS II e CAPS AD III, sem trocar atributos |

Antes de gerar respostas, conferir os trechos esperados nos documentos e inspecionar o corpus integral para confirmar as lacunas P04/P05. O lote preserva cópia dos 17 documentos. A ausência não é comprovada apenas por busca de palavras; a leitura deve considerar sinônimos e informações indiretas. Se alguma pergunta não representar a definição prospectiva, registrar a revisão antes da geração, sem adaptar casos a respostas observadas.

São duas rodadas na ordem P01–P06: **12 respostas previstas**, sequenciais, sem aquecimento de geração, histórico de conversa ou escolha de melhor resposta. Cada execução usa a recuperação real daquele percurso; a preparação não reutiliza seu contexto na coleta real.

## Componentes e instrumentação

Usar ingestão, splitter (1000/200 caracteres), embeddings multilíngues locais, FAISS, recuperador `k=10`, `run_rag`, prompt, parser e `NLPService.process` reais. Sem servidor HTTP, gateway ou banco; a fidelidade é observada na fronteira NLP/RAG, não na mensagem final da navegação do chatbot.

O executor observa o recuperador com Runnable que devolve a mesma lista de Documents, na mesma ordem; observa o gerador com Runnable que captura o PromptValue e encaminha a invocação ao ChatGroq real. Não formatar ou resumir Documents: a cadeia atual interpola sua lista no prompt, e a representação efetivamente enviada deve ser preservada. Uma chamada a `NLPService.process`, sem personalização, produz a resposta original e a saída adaptada registradas; não repetir a inferência para capturar estágios diferentes.

O gerador observado é instalado temporariamente em `CACHED_LLM`. Isso depende de estado global interno, como observado no C04, e não constitui nova interface pública. Testes com gerador sintético verificam apenas o instrumento e nunca entram nas 12 respostas.

## Ambiente e configuração externa

- Inventariar Python, pacotes, Git, hashes do código/corpus/instrumento e dos pesos locais; não instalar pacotes nem baixar pesos durante a coleta.
- Usar snapshot local `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` de `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, se disponível. O caminho local é ajuste de resolução do mesmo modelo; o inventário identifica os bytes efetivos. Ausência de pesos impede essa etapa; não substituir por embeddings falsos na coleta.
- Desabilitar tracing, telemetria e carregamento automático de `.env`; ler explicitamente apenas `GROQ_API_KEY` para a execução real, sem persistir seu valor. Preferir variável de ambiente e, na ausência, a chave no `.env` local. Nunca solicitar ou registrar a chave em conversa, evidência ou Git.
- A preparação é local, com Hub/Transformers offline e bloqueio de sockets durante importação/montagem/recuperação. Não verifica disponibilidade do gerador e não comprova fidelidade.
- Na coleta real, consultar a listagem de modelos da conta antes das inferências. Sem troca automática: o padrão é `llama-3.3-70b-versatile`; um alternativo exige `--modelo` explícito e caracteriza configuração adaptada, sem corrigir a aplicação. `openai/gpt-oss-120b` é candidato das coletas anteriores, não disponibilidade presumida nesta data.
- Geração: temperatura 0,1, máximo de 500 tokens, timeout de 60 s e `max_retries=2`, explícitos apenas no instrumento. O timeout é uma adaptação da configuração; não integra o código funcional nem é critério de rapidez. Cada resposta é uma invocação lógica; retries do SDK não são novas amostras. Registrar tentativas HTTP e respectivos status, sem cabeçalhos de autenticação ou corpo de erros.
- Indisponibilidade/erro não autoriza rerodar seletivamente perguntas. Preservar o erro e continuar a ordem prevista; uma nova série recebe outro lote. Não agrupar modelos ou lotes para compor 12 respostas favoráveis.

## Evidências e julgamento

Cada execução preserva ID, rodada, pergunta, chunks ordenados com conteúdo e metadados, prompt exato, resposta textual original, saída do NLP, reconhecimento de ausência, metadados de término/uso de tokens, tentativas HTTP e tipo de erro quando houver. Não registrar mensagens brutas de exceções do provedor. `finish_reason=length` indica possível truncamento, que exige ressalva e exame da resposta, sem nova execução seletiva.

O diagnóstico automático de recuperação registra fontes e presença literal dos trechos esperados no contexto. Isso é uma ajuda de localização, não julgamento semântico: outra fonte pode sustentar um fato, e presença parcial exige leitura. Nos casos ausentes, retornar o documento do serviço é apenas evidência de pertinência temática.

Para cada resposta, o autor deve preencher a ficha de revisão:

1. Decompor o texto em afirmações factuais atômicas. Para cada uma, copiar um trecho sustentador do contexto com o índice do chunk, ou marcar não sustentada/contraditória. Atribuição ao serviço faz parte do fato; fatos de outro serviço não são apoio válido.
2. Conferir os fatos esperados, marcando presença, omissão ou impossibilidade por recuperação. Omissões são registradas à parte: resposta ancorada pode ser incompleta. Abstenção em pergunta respondível é inadequada, mesmo sem invenção.
3. Julgar recuperação e geração separadamente. Sem trecho necessário, registrar falha de recuperação; se o modelo ainda afirmar esse fato, registrar também geração não sustentada. Contexto suficiente com resposta inventada/omitida é falha de geração. Não impor um diagnóstico único quando ambos ocorrem.
4. Em P04/P05, conferir abstenção sem informação inventada e se o NLP reconheceu o texto. Uma resposta que mistura a frase de ausência com afirmações inventadas não é aprovada só porque `sem_contexto` retornou True. Nos casos com conflito entre fontes, registrar afirmação ambígua separadamente de não sustentada.
5. Em P06, conferir cada associação entre público, endereço e serviço. Não declarar que os públicos nunca se sobrepõem: essa exclusividade não está estabelecida pelo corpus.

**Atendido apenas na amostra** se as 12 respostas forem obtidas, todas as afirmações forem sustentadas, não houver troca de serviços e a abstenção for adequada em P04/P05, sem abstenção indevida nas respondíveis. Reportar completude dos fatos esperados separadamente. Resultados mistos são parcialmente atendidos; nenhum resultado satisfatório é não atendido. Ausência de credencial, erro externo ou falha do instrumento deixa a parte impedida não avaliada; não equivale a falha factual. Não dar aprovação global se há respostas ou revisões pendentes.

O executor não atribui notas semânticas automaticamente: cria fichas pendentes. Uma análise assistida por IA deve ser identificada como preliminar; a avaliação pelo autor prevista na árvore exige revisão humana. O relatório posterior distingue coleta completa, validade da instrumentação e julgamento do conteúdo.

## Comandos e estado inicial

```powershell
.\.venv-c01\Scripts\python.exe -m pytest -q docs/avaliacao/c05/test_instrumento.py
.\.venv-c01\Scripts\python.exe docs/avaliacao/c05/executar.py preparar
# Após configurar a credencial local e identificar o modelo escolhido:
.\.venv-c01\Scripts\python.exe docs/avaliacao/c05/executar.py coletar --modelo openai/gpt-oss-120b
```

Lotes únicos em `evidencias-c05/`, sem sobrescrever anteriores. O modo `preparar` verifica corpus e recuperação e cria registros sem respostas, explicitamente separados da coleta. Em 12/11/2026, a inspeção inicial encontrou ambiente Python e snapshot local, mas nenhuma chave Groq configurada. A geração real permanece pendente; isso ainda não é um resultado de fidelidade do C05.
