# Evidências do C04

Coleta de testabilidade encerrada em 09/11/2026: **16/16 casos aprovados**, zero tentativas externas, sem credenciais ou pesos de modelos, com Python funcional preservado. Ver [relatório](../C04-relatorio-execucao.md), [protocolo prévio](../C04-protocolo.md) e [matriz](../c04/casos.json). O resultado inclui ingestão, splitter, FAISS, prompt/parser e NLP reais, com substitutos nas fronteiras e ajustes temporários no processo de teste.

Lote arquitetural único: [20261109-161456-offline-af50da](20261109-161456-offline-af50da/). Os ciclos temporários dos testes do instrumento não integram essa amostra.

| Arquivo no lote | Finalidade |
|---|---|
| [ambiente.json](20261109-161456-offline-af50da/ambiente.json) | Commit, branch, estado do Git, versões e hashes das fontes/instrumentos anteriores à coleta |
| [C04-protocolo.md](20261109-161456-offline-af50da/C04-protocolo.md), [casos.json](20261109-161456-offline-af50da/casos.json) | Cópias do protocolo e da matriz executados; links relativos do protocolo copiado conservam a base do original |
| [executar.py](20261109-161456-offline-af50da/executar.py), [test_cenario.py](20261109-161456-offline-af50da/test_cenario.py), [test_instrumento.py](20261109-161456-offline-af50da/test_instrumento.py) | Cópias preservadas dos instrumentos; executar a reprodução a partir dos originais na raiz do projeto |
| [corpus](20261109-161456-offline-af50da/projeto-sintetico/data/servicos/) | TXT Aurora/Horizonte e MD ignorado, todos fictícios |
| [casos-executados.json](20261109-161456-offline-af50da/casos-executados.json) | Resultados pytest por fase, conteúdo, prompts/respostas, erros e chamadas observadas por caso |
| [isolamento.json](20261109-161456-offline-af50da/isolamento.json) | Nomes de variáveis, ausência de credenciais, caches vazios antes/depois, neutralização de dotenv e tentativas externas |
| [pytest.txt](20261109-161456-offline-af50da/pytest.txt) | Saída completa do pytest isolado, incluindo o aviso de depreciação |
| [cobertura.json](20261109-161456-offline-af50da/cobertura.json), [resumo por pacote](20261109-161456-offline-af50da/cobertura-por-pacote.json), [cobertura.txt](20261109-161456-offline-af50da/cobertura.txt) | Linhas/ramos individuais e agregados, separados por `app/` e `api/` |
| [resumo.json](20261109-161456-offline-af50da/resumo.json), [execucao.json](20261109-161456-offline-af50da/execucao.json) | Contagens, validade, julgamento e horários |

[verificacao-previa.txt](verificacao-previa.txt) registra os 244 testes existentes e as 13 verificações do instrumento, separados dos 16 casos arquiteturais. A [conferência posterior](validacao-evidencias.json), produzida pelo [conferidor](../c04/conferir_evidencias.py), guarda checks e hashes dos artefatos, sem repetir o lote ou fazer chamadas externas.

O gerador falso retorna AIMessage e os embeddings locais usam contagem dos nomes dos serviços. Assim, os registros demonstram o exercício dos componentes e a adaptação de resultados definidos, não a qualidade de um modelo real. O uso de `CACHED_LLM` e de `ingestion.__file__` é explicitado como acoplamento no relatório. Nenhuma credencial foi utilizada nesta coleta.

Para reproduzir, executar os comandos do protocolo na raiz do repositório, com as dependências previamente instaladas. Cada coleta cria outro diretório e preserva os lotes anteriores. Não editar as cópias e registros brutos para atualizar resultados históricos.
