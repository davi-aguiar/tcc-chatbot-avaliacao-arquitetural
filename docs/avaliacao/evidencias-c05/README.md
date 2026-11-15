# C05 — Evidências de preparação e coleta

**Estado em 14/11/2026: 12 respostas reais coletadas e conferidas; análise de IA preliminar entregue; revisão humana e julgamento final pendentes.** Referência funcional `ffcd30fe07cbf281a030a14d481d3eee5533db5c`; [protocolo](../C05-protocolo.md), [matriz](../c05/casos.json) e [relatório](../C05-relatorio-execucao.md).

## Coleta real de 14/11/2026

Lote [20261114-205318-coletar-12c7f8](20261114-205318-coletar-12c7f8/execucao.json), sobre o commit de preparação `c3df19c`, sem diferenças funcionais/corpus em relação ao corte. Modelo alternativo explícito `openai/gpt-oss-120b`; o padrão não estava listado na conta. Temperatura 0,1, 500 tokens, timeout de 60 s, dois retries, embeddings semânticos locais e FAISS reais. Uma recuperação e uma geração lógica por consulta; 23 tentativas HTTP de geração, sendo 12 HTTP 200 e 11 HTTP 429. Não houve repetição seletiva.

As 12 respostas são não vazias, sem exceção final. Os 15 trechos esperados chegaram ao contexto em ambas as rodadas. A leitura assistida identificou apoio para 49 afirmações e quatro abstenções exatas, sem troca de serviços observada. Completude: 28 fatos esperados presentes, um parcial e um omitido. P06-R1 terminou com `finish_reason=length`; a revisão pelo autor continua necessária e não há aprovação global.

- [Verificação anterior às inferências](verificacao-previa-20261114.json): leitura do corpus, lacunas, teste do instrumento e escolha explícita do modelo.
- [Ambiente e hashes](20261114-205318-coletar-12c7f8/ambiente.json), [configuração](20261114-205318-coletar-12c7f8/configuracao.json), [modelos disponíveis](20261114-205318-coletar-12c7f8/modelos-disponiveis.json) e [integridade](20261114-205318-coletar-12c7f8/integridade-fontes.json).
- `P01-R1.json` a `P06-R2.json` no lote: pergunta, contexto, prompt exato, resposta original, saída NLP, metadados, erros e tentativas HTTP. Exemplo de incompletude preservada: [P06-R1](20261114-205318-coletar-12c7f8/P06-R1.json).
- [revisao.json](20261114-205318-coletar-12c7f8/revisao.json): 12 fichas humanas ainda pendentes, sem assinatura atribuída ao autor.
- [Análise preliminar de IA](analise-preliminar-ia.json): afirmações com trechos literais/chunks, completude e ambiguidades, separadas das fichas humanas.
- [Conferência posterior](validacao-evidencias.json): 167 verificações estruturais aprovadas, sem julgar conteúdo semanticamente ou repetir inferências; [conferidor](../c05/conferir_evidencias.py) criado após o início da coleta.
- [Verificações da sessão](verificacoes-20261114.json): suíte existente, instrumento, lint, compilação e verificações negativas do conferidor.

Para reproduzir a conferência sem novas chamadas ao provedor, na raiz do repositório, com o snapshot local preservado:

```powershell
python docs/avaliacao/c05/conferir_evidencias.py docs/avaliacao/evidencias-c05/20261114-205318-coletar-12c7f8 --saida docs/avaliacao/evidencias-c05/validacao-evidencias.json
```

O conferidor também compara as fontes atuais e os pesos aos hashes do lote; diferenças posteriores são apontadas, não corrigidas. O valor da chave, quando disponível localmente, é usado apenas para conferir sua ausência nos artefatos. Os pesos não são copiados para o repositório.

## Preparação local histórica de 12/11/2026

Lote [20261112-100731-preparar-1600a7](20261112-100731-preparar-1600a7/execucao.json), modo `preparar`, com ingestão, splitter, embeddings multilíngues e FAISS reais, recuperador `k=10`, rede bloqueada no processo durante montagem e consultas. Não usou gerador, banco, HTTP do chatbot ou credencial. Foram consultadas as seis perguntas uma vez para inspecionar recuperação; essas consultas não são as duas rodadas de respostas previstas.

| Caso | Chunks recuperados | Fontes esperadas presentes | Trechos de referência localizados |
|---|---|---|---|
| P01 — Acesso à espirometria | 10 | Sim | 4/4 |
| P02 — Documentos do Programa Asma Grave | 10 | Sim | 4/4 |
| P03 — Endereço e funcionamento do CAPS II | 10 | Sim | 3/3 |
| P04 — Jejum para espirometria | 10 | Sim | Não aplicável: informação ausente |
| P05 — Prazo para eletrocardiograma | 10 | Sim | Não aplicável: informação ausente |
| P06 — Diferenciar CAPS II e CAPS AD III | 10 | Sim, ambos os serviços | 4/4 |

Os 15 trechos literais esperados estão no contexto dos quatro casos com fatos de referência. Nos casos P04/P05, recuperar documentos relacionados não cria a informação solicitada; a abstenção só poderá ser avaliada após geração real. A leitura dos 17 TXT realizada durante a preparação não encontrou exigência/duração de jejum para espirometria nem prazo máximo em dias para realização do eletrocardiograma.

**Ambiguidade documental observada:** o chunk 3 de P03 e o chunk 4 de P06 contêm a seção “Onde fica o CAPS II?” no documento do Ambulatório de Saúde Mental, seguida de Avenida Olívia Flores, 3000. O documento específico do CAPS II fornece Avenida Régis Pacheco, 770. Ambos chegaram ao contexto. Esse achado sustenta risco de curadoria/atribuição documental; não demonstra ainda como o modelo responderá. As fontes foram preservadas, sem correção durante o cenário.

## Arquivos do lote

- [recuperacao.json](20261112-100731-preparar-1600a7/recuperacao.json): as seis perguntas, os 60 chunks ordenados com metadados e o diagnóstico literal de fontes/trechos.
- [ambiente.json](20261112-100731-preparar-1600a7/ambiente.json): Python, pacotes, Git, hashes de 68 arquivos de código/corpus/instrumentação e dez arquivos do snapshot local dos embeddings. Pesos não foram copiados para o repositório.
- [integridade-fontes.json](20261112-100731-preparar-1600a7/integridade-fontes.json): fontes inalteradas entre início e fim da preparação.
- [execucao.json](20261112-100731-preparar-1600a7/execucao.json): preparação completa, credencial ausente, zero respostas obtidas, julgamento não avaliado.
- `fontes/`: cópias das fontes, dos 17 TXT, do protocolo e dos instrumentos vigentes na preparação. Versões preservadas não são editadas posteriormente.

## Verificação do instrumento e próxima etapa

As [14 verificações locais](verificacao-instrumento.txt) passaram. Os testes adicionais após o lote exercitaram a série completa com ChatGroq/SDK reais e transporte HTTP sintético, e a interrupção quando o modelo escolhido não está listado. Essas respostas sintéticas vivem apenas em diretórios temporários do pytest e não são resultados de fidelidade. A cópia de `test_instrumento.py` preservada no lote contém as 12 verificações existentes naquele momento; as duas verificações adicionais estão na versão atual do instrumento.

Na preparação histórica, nenhuma chave estava disponível e nenhuma resposta real foi gerada. A coleta de 14/11/2026 foi realizada em outro lote, usando a credencial já configurada localmente. Nenhum relatório de aprovação do C05 pode ser derivado apenas da preparação ou da conferência estrutural.
