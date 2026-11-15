# C06 — Evidências de preparação, coleta e análise

**Estado: coleta oficial concluída em 14/11/2026; análise preliminar propõe parcialmente atendido no recorte. Revisão interpretativa do autor pendente.** C01 a C05 estão encerrados com ressalvas. Referência do protocolo: `92e48ab6eb76608904a3367a3b596ad34b12590d`, após a [revisão humana do C05](../evidencias-c05/julgamento-final.json); coleta no commit de preparação `d5aa477`, sem mudança funcional.

O [protocolo](../C06-protocolo.md) e a [matriz](../c06/casos.json) fixam sete perfis em duas rodadas: 14 observações, com consultas de menu, texto livre, nome/identificador autodeclarados e navegação estática. O SDK serializou 12 pedidos reais para um transporte HTTP local com respostas sintéticas, sem uso de chave real ou envio externo. Recuperação foi substituída por Document sintético; ChatService, NLP/RAG, prompt, fábrica/SDK, modelos, persistência e logger permaneceram reais.

## Coleta e análise preliminar

Lote [20261114-231108-coletar-7b9bcf](20261114-231108-coletar-7b9bcf/execucao.json): 14 observações válidas, 12 pedidos locais (seis HTTP 200 e seis HTTP 400), dois controles estáticos, zero tentativas externas e 68 fontes preservadas. Os arquivos D01–D07/R1–R2 contêm corpo serializado, snapshots antes/depois, logs e localizações dos marcadores. O [manifesto](20261114-231108-coletar-7b9bcf/ambiente.json) registra ambiente, Git, dependências e hashes; `fontes/` preserva suas cópias.

- [validacao-evidencias.json](validacao-evidencias.json): 381 verificações estruturais aprovadas, com corpos reconstruídos e caminhos recalculados. O [verificador posterior](../c06/conferir_evidencias.py) não estava no manifesto de coleta; quatro [testes de conferência](../c06/test_conferencia.py) passaram, incluindo três adulterações em cópias temporárias.
- [analise-preliminar.json](analise-preliminar.json): cinco critérios, caminhos e limites; proposta de julgamento, sem confirmação humana.
- [verificacao-analise.json](verificacao-analise.json): comandos, resultados e hashes dos dois módulos posteriores.
- [relatório técnico](../C06-relatorio-execucao.md): minimização automática atendida nos 12 pedidos; texto autodeclarado preservado; consulta/relato duplicados em quatro emissões operacionais de erro D04/D06; persistência e auditoria mapeadas separadamente.

Passar nas verificações estruturais não significa atender aos critérios de confidencialidade. Os registros originais de execução/preparação permanecem históricos e não são sobrescritos pela análise posterior.

## Preparação local histórica

Lote [20261114-222034-preparar-2f7d16](20261114-222034-preparar-2f7d16/execucao.json): matriz válida, sete dependências necessárias disponíveis, fontes preservadas e **zero observações executadas**. Não consultou modelos, leu `.env`, usou credencial real ou chamou o provedor. Não houve instalação de pacotes ou download de pesos.

- [ambiente.json](20261114-222034-preparar-2f7d16/ambiente.json): Python, plataforma, pacotes, Git e hashes das fontes/instrumentos vigentes.
- [execucao.json](20261114-222034-preparar-2f7d16/execucao.json): preparação completa, 14 observações previstas, zero executadas, coleta incompleta e julgamento não avaliado.
- [verificacao-instrumento.json](verificacao-instrumento.json): resultados dos testes e conferências desta preparação.

## Verificações do instrumento

As 13 verificações passaram em 3,39 s: matriz/ordem/query, rejeição de fixture que mistura identidade e contexto, rejeição de query divergente, bloqueio e contagem de DNS/conexão/UDP/subprocesso, localização de segredo antes de omissão, isolamento/restauração do ambiente, três percursos de teste com SDK/aplicação reais e garantia de que `preparar` não chama as observações.

Os três percursos de teste usam IDs próprios `INSTRUMENTO-*`, sem lote oficial ou julgamento do cenário; não são somados às 14 observações planejadas. A resposta de inferência continua sintética e não avalia conteúdo clínico ou fidelidade documental. Os 244 testes existentes passaram separadamente em 2,70 s. Lint e compilação dos dois novos módulos passaram.

## Instrumento e alcance

O [executor](../c06/executar.py) dispõe de `preparar` e `coletar`. Os lotes foram separados. A conferência e a síntese distinguem dados digitados pelo usuário, dados adicionados automaticamente, persistência e logs. O segredo sintético foi descartado após a procura bruta; a conferência posterior não pode refazer essa procura sem o marcador original. Nenhum corpo foi enviado ao provedor.

Nenhum achado de segurança deriva apenas da preparação. A coleta avalia o recorte técnico do protocolo, sem classificação jurídica ou certificação de segurança.
