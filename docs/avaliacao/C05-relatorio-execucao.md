# C05 — Relatório de execução e julgamento

Coleta realizada em 14/11/2026, com assistência de IA, conforme o [protocolo prévio](C05-protocolo.md). **C05 encerrado com ressalvas: fidelidade atendida apenas na amostra, com completude parcial.** As 12 respostas foram revisadas e seus julgamentos confirmados pelo autor na conversa. Não foram identificadas afirmações sem apoio ou trocas de serviços; as quatro consultas sem informação tiveram abstenção adequada. P06-R1 ficou incompleta por truncamento. O resultado não garante ausência de alucinação fora da amostra.

**Revisão humana concluída:** 12 fichas confirmadas pelo autor e nenhuma pendente, em [revisao.json](evidencias-c05/20261114-205318-coletar-12c7f8/revisao.json). O [julgamento final](evidencias-c05/julgamento-final.json) aplica os critérios prévios às fichas confirmadas, separando fidelidade de completude. A [conferência após a revisão](evidencias-c05/validacao-revisao.json) mantém as 167 verificações estruturais aprovadas. A revisão foi assistida, sem cegamento ou avaliador independente.

## Referência e procedimento

O repositório foi atualizado por fast-forward para `c3df19ca9ac60ea508807a07c949376fc0cb005c`, que contém a preparação do C05. O código funcional e o corpus não apresentam diferenças em relação ao corte `ffcd30fe07cbf281a030a14d481d3eee5533db5c`. O trabalho desta sessão está na branch `experimento/c05-confiabilidade`, sem edição de aplicação, prompts, corpus, chunking ou `k`.

Antes das inferências, foram conferidos os 17 TXT, os trechos esperados e as lacunas das perguntas. A descrição de exame “rápido” não estabelece prazo de agendamento; os 30 dias mencionados no documento de oxigenoterapia se referem à idade de um relatório de outro serviço. Nenhum documento informa duração/exigência de jejum para espirometria ou prazo máximo em dias para realizar eletrocardiograma. A [verificação prévia](evidencias-c05/verificacao-previa-20261114.json) registra essa leitura assistida, os testes do instrumento e a escolha de modelo antes da coleta.

A credencial já estava configurada no `.env` local ignorado pelo Git. A listagem atual da conta retornou HTTP 200, sem `llama-3.3-70b-versatile` e com `openai/gpt-oss-120b`. Foi escolhido explicitamente o alternativo previsto no protocolo. Não houve inferência com o padrão indisponível, substituição automática nem alteração do modelo na aplicação. O resultado pertence à **configuração adaptada**, não ao modelo padrão.

Comando executado no ambiente `.venv` existente:

```powershell
python docs/avaliacao/c05/executar.py coletar --modelo openai/gpt-oss-120b
```

O lote [20261114-205318-coletar-12c7f8](evidencias-c05/20261114-205318-coletar-12c7f8/execucao.json) executou P01–P06 na primeira rodada e P01–P06 na segunda, sem aquecimento de geração, histórico ou repetição seletiva. A recuperação foi refeita em cada consulta. Ingestão, splitter, embeddings locais, FAISS, prompt/parser, `run_rag` e `NLPService.process` foram reais. Os observadores capturaram os objetos e encaminharam cada invocação; não impuseram respostas.

Montagem local com bloqueio de sockets e modelos offline; na geração, acesso real à listagem de modelos e ao provedor Groq. Não houve servidor do chatbot, gateway, banco ou mensagem enviada ao WhatsApp.

## Ambiente e validade da coleta

Python 3.12.10, Windows 11; LangChain 1.4.7, langchain-core 1.7.3, langchain-community 0.4.2, langchain-groq 1.1.3, Groq SDK 0.37.1, sentence-transformers 6.1.0, Transformers 5.20.2, Torch 2.14.1 e FAISS CPU 1.15.1. Inventário completo em [ambiente.json](evidencias-c05/20261114-205318-coletar-12c7f8/ambiente.json).

Foram usados os pesos locais do snapshot `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` de `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. O lote preserva hashes de dez arquivos do snapshot e de 68 arquivos de código, corpus e instrumentos, além das cópias destes 68 arquivos. Não foram instaladas dependências nem baixados pesos durante a coleta. O aviso de depreciação do adaptador `HuggingFaceEmbeddings` não impediu a montagem e não foi corrigido no meio do ensaio.

Configuração mantida nas 12 consultas: temperatura 0,1, máximo de 500 tokens, timeout explícito de 60 s, `max_retries=2`, recuperador `k=10` e splitter original de 1000/200 caracteres. O timeout explícito também é adaptação do instrumento. [Configuração efetiva](evidencias-c05/20261114-205318-coletar-12c7f8/configuracao.json) e [listagem de modelos](evidencias-c05/20261114-205318-coletar-12c7f8/modelos-disponiveis.json) preservadas.

As 12 invocações lógicas tiveram resposta textual não vazia e nenhuma exceção final. Houve **23 tentativas HTTP de geração: 12 respostas 200 e 11 respostas 429**, absorvidas pelos retries do SDK. A consulta prévia de modelos não integra essas 23 tentativas. Foram 120 chunks registrados, uma chamada ao recuperador e uma ao gerador observado por resposta. Retries HTTP não constituem amostras adicionais.

A [conferência posterior](evidencias-c05/validacao-evidencias.json), feita sem novas inferências, aprovou 167 verificações estruturais: hashes/cópias, pesos locais, corpus, ordem, conteúdo/origem dos chunks, configuração, prompt, adaptação NLP, tentativas HTTP e fichas humanas pendentes. O serializer estruturado do coletor guarda conteúdo/metadados; os IDs atribuídos pelo FAISS permanecem no prompt exato e são extraídos dele para reconstrução pelo [conferidor](c05/conferir_evidencias.py). O conferidor foi criado depois do início da coleta, não foi usado nas inferências e não integra seu manifesto prévio. Nenhum arquivo listado nesse manifesto mudou.

## Resultados observados e revisão pelo autor

| Caso | Recuperação em cada rodada | Rodada 1 | Rodada 2 |
|---|---|---|---|
| P01 — Acesso à espirometria | 4/4 trechos esperados | Quatro passos e endereço do CEMAE com apoio | Quatro passos e endereço do CEMAE com apoio |
| P02 — Documentos Asma Grave | 4/4 trechos esperados | Quatro grupos documentais esperados | Quatro grupos documentais esperados |
| P03 — CAPS II: endereço e horário | 3/3 trechos esperados; fonte conflitante também presente | Endereço da fonte específica, horário e exceção semanal | Endereço da fonte específica, horário e exceção semanal |
| P04 — Jejum | Documento temático presente; resposta ausente | Frase exata de abstenção | Frase exata de abstenção |
| P05 — Prazo do eletrocardiograma | Documento temático presente; resposta ausente | Frase exata de abstenção | Frase exata de abstenção |
| P06 — Diferenciar os CAPS | 4/4 trechos esperados; fonte conflitante também presente | Públicos apresentados; endereços incompletos por truncamento | Públicos e endereços de ambos apresentados |

O diagnóstico literal encontrou todos os 15 trechos de referência por rodada, totalizando 30 ocorrências esperadas com apoio no contexto. Isso descreve recuperação, não a presença dos fatos nas respostas. Na leitura semântica assistida, **28 fatos esperados apareceram integralmente, um parcialmente e um foi omitido**. Sete das oito respostas com fatos esperados ficaram completas; a resposta restante foi P06-R1. Os quatro casos de ausência são analisados separadamente, sem denominador artificial de completude.

A [análise preliminar de IA](evidencias-c05/analise-preliminar-ia.json) decompõe as respostas em 49 afirmações, com fragmento da resposta, índice do chunk e trecho literal de apoio. Não identificou afirmação factual sem apoio ou troca de atributos entre serviços. Não houve avaliador independente nem medição de concordância entre revisores. Em P01, “informando/confirmando data e horário” foi interpretado como paráfrase conjunta do contato e do comparecimento agendado. Em P02, “CPF e RG” encontra apoio em “CPF / RG” do programa e em “RG e CPF” no trecho recuperado sobre documentos para qualquer marcação.

**Truncamento:** [P06-R1](evidencias-c05/20261114-205318-coletar-12c7f8/P06-R1.json) terminou com `finish_reason=length`, após “Avenida Régis Pacheco, 770,”. F02 ficou parcial por faltar Centro; F04, endereço do CAPS AD III, foi omitido. Ambos os endereços completos estavam no contexto, nos chunks 5 e 3, respectivamente. Portanto, a incompletude está na geração/configuração, sem falta de recuperação para esses fatos. O provedor informou 500 tokens de saída, dos quais 406 de raciocínio. Isso sustenta sensibilidade ao orçamento de saída nesta configuração adaptada; não demonstra que aumentar o limite resolveria todos os casos. A [segunda resposta P06](evidencias-c05/20261114-205318-coletar-12c7f8/P06-R2.json) terminou com `stop` e trouxe os quatro fatos. As duas foram mantidas, sem escolher a melhor para substituir a primeira.

**Abstenção:** P04/P05, nas duas rodadas, produziram somente “Desculpe, não encontrei essa informação específica nos meus documentos.” O reconhecimento `sem_contexto` foi verdadeiro e o NLP retornou `None`. Não houve número de horas, dispensa de jejum, prazo ou garantia inventada nessas quatro respostas. A observação vale para essa fronteira: não demonstra qual texto seria apresentado pela navegação final do chatbot.

**Conflito documental:** o trecho do Ambulatório que pergunta “Onde fica o CAPS II?” e fornece Avenida Olívia Flores, 3000 chegou a P03 (chunk 3) e P06 (chunk 4), nas duas rodadas. O documento específico fornece Avenida Régis Pacheco, 770, Centro. O modelo escolheu o endereço da fonte específica nas quatro respostas, ainda que incompleto em P06-R1. O conflito continua sendo risco de curadoria; o resultado não comprova que o prompt resolverá qualquer inconsistência. Em P06-R2, “públicos diferentes” foi interpretado como distinção dos perfis descritos, sem afirmar que nunca se sobrepõem.

## Interpretação arquitetural

| Decisão ou condição | Evidência C05 | Implicação e possibilidade de manutenção |
|---|---|---|
| Recuperação semântica com `k=10` | Trechos necessários presentes nas duas rodadas; conflitos e textos de outros serviços também chegam | Favorece encontrar os fatos desta amostra, mas exige atribuição correta pelo gerador; não foi comparado outro `k` |
| Orientação de ancoragem no prompt | Afirmações examinadas com apoio e quatro abstenções exatas na leitura preliminar | Evidência local favorável, sem mecanismo determinístico de validação factual ou garantia geral |
| Ausência representada por frase reconhecida pelo NLP | Quatro respostas originais de ausência viraram `None` | Convenção funcionou na amostra; contrato continua sem distinguir estruturalmente ausência e outras causas em todos os consumidores |
| Limite de 500 tokens com modelo alternativo de raciocínio | P06-R1 usou o limite e terminou incompleta, com contexto suficiente | Custo/limite de saída e completude exigem avaliação conjunta; uma configuração diferente requer nova série identificada |
| Corpus com seção de serviço mal atribuída | Dois endereços incompatíveis no contexto de P03/P06 | Revisão da curadoria e identificação explícita do serviço são propostas posteriores, sem correção durante este cenário |
| Dependência de disponibilidade e quota do provedor | Padrão ausente da listagem; 11 HTTP 429 e retries na série adaptada | A coleta completa não elimina risco operacional nem demonstra disponibilidade sob carga |

São relações exploratórias entre decisões e comportamentos observados, não comparação causal entre arquiteturas ou modelos. Nenhuma recomendação desta tabela foi implementada ou teve benefício medido no C05.

## Verificações e limites

As 14 verificações prévias do instrumento passaram em 9,19 s; separadamente, os 244 testes existentes passaram em 5,23 s. Esses testes não fazem parte das 12 respostas e não julgam seu conteúdo. O registro das verificações posteriores, incluindo conferência de evidências e análise de integridade, está no [índice](evidencias-c05/README.md).

Uma máquina, um modelo alternativo, seis perguntas e duas rodadas sequenciais não estabelecem taxa populacional de alucinação, robustez a perguntas adversariais, causalidade, validade clínica, atualidade municipal, comportamento concorrente ou entrega final. As duas rodadas compartilham corpus, índice e configuração e não são uma amostra aleatória de uso. Houve revisão humana assistida concluída; não houve avaliação cega, avaliador independente ou comparação de modelos. A configuração padrão segue não avaliada por geração nesta sessão, pois não estava listada.

**Estado final: C05 encerrado com ressalvas; critério de fidelidade atendido apenas na amostra, com completude parcial.** O protocolo exige reportar completude separadamente; o truncamento não foi apagado ou substituído pela segunda resposta. Nenhuma nova coleta ou correção funcional foi necessária para esse fechamento. C06 passa à preparação com protocolo próprio, sem transmissão dos dados sintéticos ao provedor.
