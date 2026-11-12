# C05 — Evidências de preparação

**Estado em 12/11/2026: preparação concluída; coleta das 12 respostas reais e julgamento de fidelidade pendentes.** Referência funcional `ffcd30fe07cbf281a030a14d481d3eee5533db5c`; [protocolo](../C05-protocolo.md) e [matriz de perguntas](../c05/casos.json).

## Preparação local

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

Para coletar respostas reais, configurar `GROQ_API_KEY` somente no ambiente local ou no `.env` ignorado pelo Git. O executor verifica a listagem de modelos da conta, preserva a configuração escolhida, cria outro lote e gera as 12 fichas de revisão pendentes. A chave nunca deve ser enviada em conversa ou incluída nas evidências. Nenhum relatório de aprovação do C05 pode ser derivado apenas desta preparação.
