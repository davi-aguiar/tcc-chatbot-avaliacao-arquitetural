# Evidências do C03

Este diretório preserva a coleta sequencial, denominada **C03-A** após a ampliação do cenário. A verificação de mensagens simultâneas está em [C03-B](../evidencias-c03-b/README.md), com bloqueio/timeout observado. Os 12 casos abaixo não demonstram disponibilidade sob concorrência.

Coleta de 08/11/2026: **12/12 casos com continuidade preservada**, após timeout, erro de conexão e modelo indisponível injetados no SDK. Foram 48/48 interações posteriores sem nova chamada à inferência e zero tentativas de rede. O critério operacional foi atendido com ressalvas: texto livre informa opção inválida e audita envio; menu informa erro interno e não preserva o par de mensagens na falha.

Interpretação e limites no [relatório](../C03-relatorio-execucao.md). Critérios prévios no [protocolo](../C03-protocolo.md). Não houve geração real, medição de timeout decorrido ou avaliação de falhas na inicialização.

## Lote principal

Diretório: `20261108-212956-falhas-4781d2`. Horário local do início: 21:30 de 08/11/2026; registros em UTC: 00:30 de 09/11/2026. Não somar os testes do instrumento aos 12 casos deste lote.

| Arquivo | O que permite conferir |
|---|---|
| [casos-executados.json](20261108-212956-falhas-4781d2/casos-executados.json) | Respostas, estados, exceções, persistência, auditoria e chamadas por caso e etapa |
| [resumo.json](20261108-212956-falhas-4781d2/resumo.json) | Contagens, julgamento de continuidade e diferenças entre os percursos |
| [ambiente.json](20261108-212956-falhas-4781d2/ambiente.json) | Commit de corte, estado do Git, Python, dependências e SHA-256 de fontes/instrumentos |
| [modelo.json](20261108-212956-falhas-4781d2/modelo.json) | Configuração do cliente e fronteira substituída; sem geração ou retries HTTP |
| [aplicacao.log](20261108-212956-falhas-4781d2/aplicacao.log) | Tratamento real das exceções e eventos de log da aplicação, com dados sintéticos |
| [execucao.json](20261108-212956-falhas-4781d2/execucao.json) | Comando, processo, horários e validade da coleta |
| [Protocolo preservado](20261108-212956-falhas-4781d2/C03-protocolo.md), [casos](20261108-212956-falhas-4781d2/casos.json), [executor](20261108-212956-falhas-4781d2/executar.py) | Conteúdo usado na coleta, copiado antes de executar |
| [validacao-evidencias.json](validacao-evidencias.json) | Conferência posterior de hashes, cópias, contagens e critérios registrados |
| [verificacao-previa.txt](verificacao-previa.txt) | 244 testes do projeto, 6 do instrumento C03, 4 do C02, lint e compilação antes da coleta |

## Reprodução

O [executor atual](../c03/executar.py) cria lote novo a cada execução e não sobrescreve estes arquivos. As entradas estão em [casos.json](../c03/casos.json) e as verificações do instrumento em [test_executor.py](../c03/test_executor.py). Comandos e fronteiras preservadas/substituídas no protocolo. Uma execução válida pode ter julgamento parcial ou não atendido: o código de saída do executor indica validade da coleta, não aprovação arquitetural.
