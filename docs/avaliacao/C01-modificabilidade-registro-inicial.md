# C01 — Inclusão de serviço no menu: registro inicial

## Identificação e estado

- Data local do registro: 15/10/2026.
- Atributo: modificabilidade.
- Versão de referência: `c2028d50da878bfcecede18ca8822eca64672990`.
- Estado do repositório antes deste registro: sem alterações indicadas por `git status --short`.
- Situação atual (19/10/2026): coleta encerrada com ressalvas. C01-A atendido; C01-B parcialmente atendido na configuração original (modelo remoto retornou 404). Ensaio complementar com modelo disponível executou o percurso completo com geração real e retorno. Ver [relatório de execução](C01-relatorio-execucao.md) e [análise para o TCC](C01-analise-resultados.md).
- Avaliação conduzida pelo autor com apoio de IA. Registrar essa assistência na análise das limitações, especialmente ao interpretar esforço e tempo.
- Método: avaliação baseada em cenários inspirada no ATAM, adaptada ao estudo individual; este exercício não constitui aplicação completa do ATAM.

## Pergunta e hipótese

É possível incluir um serviço na estrutura de menus existente alterando apenas a configuração JSON e, na variante RAG, a base documental, sem modificar código Python da aplicação?

Hipótese a verificar: o interpretador genérico de menus localiza as alterações nesses artefatos. A hipótese não implica suporte a qualquer novo comportamento, atualização sem reinício ou ausência de regressões.

## Cenário em seis partes

| Elemento | Definição operacional |
|---|---|
| Fonte do estímulo | Desenvolvedor responsável pela manutenção |
| Estímulo | Solicitação de adicionar o serviço fictício `Serviço Experimental C01`, explicitamente marcado como teste |
| Ambiente | Desenvolvimento local, versão de referência identificada, sem dados de cidadãos e sem publicação |
| Artefato | Configuração de menus, interpretador de menus, orquestração da conversa e, na variante RAG, documentos e índice |
| Resposta esperada | Incluir o serviço, permitir acesso e retorno e preservar os percursos existentes verificados |
| Medida de resposta | Zero arquivos Python da aplicação alterados; alterações funcionais restritas ao JSON e, na variante RAG, a um TXT; aprovação dos percursos definidos abaixo; registrar arquivos, reinícios, reindexações e esforço observado |

A prioridade inicial é alta, herdada da proposta de pesquisa; não resulta de votação de stakeholders. Dificuldade de implementação ainda não classificada.

## Variantes e limites

**C01-A — Conteúdo estático:** adicionar a opção `17` ao estado `WAITING_4_SERVICOS`, apontando para um novo estado com descrição de teste em `text` e opção `0` de retorno ao menu de serviços. Isso reutiliza `next_state`; não pressupõe um novo tipo de opção com resposta estática direta.

**C01-B — Consulta documental:** adicionar ao novo estado uma opção com `query` e um documento sintético em `data/servicos/`. Executar e registrar separadamente a navegação com substituto controlado de NLP e, se disponível, a integração com recuperação e geração reais. O substituto verifica encaminhamento, não comprova recuperação nem geração.

Não avaliar conteúdo clínico, experiência de usuários ou desempenho em produção. Não misturar a inclusão de um serviço com mudanças nos mecanismos do interpretador. Arquivos de teste e de evidência devem ser contabilizados separadamente dos arquivos funcionais alterados.

## Inspeção inicial do código — evidências documentais

| Evidência | Local | Observação |
|---|---|---|
| E01 | `api/services/menu_texts.json`, estado `WAITING_4_SERVICOS` | Opções de serviços de 1 a 16 e retorno 0; a opção 17 é candidata à inclusão |
| E02 | `api/services/menu_handlers.py`, carga de `TEXTS` | JSON carregado na importação; editar o arquivo não demonstra atualização no processo em execução |
| E03 | `handle_dynamic_menu` | `next_state` muda o estado e retorna seu texto; `query` chama `nlp_service.process` |
| E04 | `app/core/ingestion.py`, `load_servicos` | Carregamento dos arquivos `*.txt` em `data/servicos/` |
| E05 | `app/main.py`, `setup_system` | Construção dos documentos, chunks, embeddings, índice e retriever |
| E06 | `tests/test_menu_texts.py` | Há verificações existentes de estrutura, destinos e retorno; não foram executadas neste registro |

Essas observações indicam viabilidade do ensaio, mas não constituem seu resultado. A verificação de alcance dos estados existente no teste não substitui a execução dos percursos a partir do menu principal.

## Procedimento previamente definido

1. Criar branch para o experimento e registrar nome, commit inicial e ambiente (Python, dependências e serviços utilizados).
2. Executar as verificações pertinentes na versão inicial e guardar comando, saída e código de retorno. Se houver falha preexistente, registrá-la antes da alteração.
3. Aplicar C01-A sem refatorações. Guardar diff e lista de arquivos funcionais alterados.
4. Verificar o percurso `principal → 4 → 17 → 0 → 0`, conferindo estados e textos em cada etapa.
5. Verificar opção inválida no novo estado; verificar `/menu` a partir dele.
6. Reexecutar os testes de menu e conversa disponíveis e um percurso existente: `principal → 4 → 2 (CEMERF) → 0 → 0`. Isso fornece evidência limitada de preservação dos comportamentos exercitados.
7. Registrar se a atualização exigiu reinício. Não usar recarregamento automático do ambiente como evidência de atualização dinâmica implementada pela aplicação.
8. Aplicar C01-B, guardar diff adicional e registrar reconstrução do índice. Separar resultados com NLP substituto dos resultados de integração real. Não chamar serviços pagos sem verificar a configuração e a autorização existente.
9. Preencher o relatório abaixo, incluindo falhas. Não corrigir mecanismos da aplicação durante o ensaio sem registrar a mudança de escopo.

## Critérios de julgamento

- **Atendido na variante:** nenhum Python funcional alterado e todos os percursos previstos para ela verificados com sucesso no nível declarado.
- **Parcialmente atendido:** apenas parte do comportamento foi verificada ou algum critério falhou; explicitar qual.
- **Não atendido:** a inclusão no escopo definido exige mudança em Python funcional ou o comportamento esperado não é obtido.
- **Não avaliado:** execução pendente ou impedida; não tratar ausência de evidência como sucesso ou falha.

Reinício e reindexação são custos operacionais a registrar, não reprovações automáticas do critério de localização da mudança. Tempo é descritivo, sem limite de aceitação arbitrário: separar edição, estudo, espera por dependências, execução e assistência de IA.

## Formulário original — preservado como registro do planejamento

Os campos abaixo representam o estado anterior ao ensaio. Os resultados de 19/10/2026 estão no [relatório preenchido](C01-relatorio-execucao.md).

| Campo | Resultado |
|---|---|
| Branch e commit/patch experimental | Pendente |
| Ambiente e dependências | Pendente |
| Comandos e resultados anteriores à alteração | Pendente |
| Diff C01-A e arquivos alterados | Pendente |
| Percursos C01-A: entradas, estados e saídas | Pendente |
| Diff C01-B e arquivos alterados | Pendente |
| Encaminhamento com substituto de NLP | Pendente |
| Recuperação e geração reais | Não executadas |
| Reinícios/reindexações | Pendente |
| Tempo e assistência de IA | Pendente |
| Regressões observadas e abrangência dos checks | Pendente |
| Julgamento por variante | Não avaliado |
| Riscos, sensibilidades e trade-offs | Pendente de análise das evidências |
| Recomendações e limitações | Pendente |

## Fundamentação

- Kazman, Klein e Clements (2000), [ATAM: Method for Architecture Evaluation](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/): método e análise de decisões e riscos. Complementa a referência de 1998 do projeto; é outra publicação.
- Bass, Clements e Kazman (2021), [Software Architecture in Practice, 4ª ed.](https://www.informit.com/store/software-architecture-in-practice-9780136885672): cenários de atributos de qualidade e modificabilidade, capítulos 3 e 8.
- Bachmann, Bass e Nord (2007), [Modifiability Tactics](https://www.sei.cmu.edu/library/modifiability-tactics/): análise de modificabilidade por acoplamento, coesão e custo de mudança.

As referências acima fundamentam o planejamento do cenário.
