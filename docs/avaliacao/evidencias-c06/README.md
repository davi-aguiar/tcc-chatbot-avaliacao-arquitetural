# C06 — Evidências de preparação

**Estado em 14/11/2026: preparação concluída; coleta oficial não executada e critérios de confidencialidade não avaliados.** C01 a C05 estão encerrados com ressalvas. Referência funcional e documental: `92e48ab6eb76608904a3367a3b596ad34b12590d`, após a [revisão humana do C05](../evidencias-c05/julgamento-final.json).

O [protocolo](../C06-protocolo.md) e a [matriz](../c06/casos.json) fixam sete perfis em duas rodadas: 14 observações, com consultas de menu, texto livre, nome/identificador autodeclarados e navegação estática. O SDK deve serializar pedidos reais para um transporte HTTP local com respostas sintéticas, sem uso de chave real ou envio externo. Recuperação é substituída por Document sintético; ChatService, NLP/RAG, prompt, fábrica/SDK, modelos, persistência e logger permanecem reais.

## Preparação local

Lote [20261114-222034-preparar-2f7d16](20261114-222034-preparar-2f7d16/execucao.json): matriz válida, sete dependências necessárias disponíveis, fontes preservadas e **zero observações executadas**. Não consultou modelos, leu `.env`, usou credencial real ou chamou o provedor. Não houve instalação de pacotes ou download de pesos.

- [ambiente.json](20261114-222034-preparar-2f7d16/ambiente.json): Python, plataforma, pacotes, Git e hashes das fontes/instrumentos vigentes.
- [execucao.json](20261114-222034-preparar-2f7d16/execucao.json): preparação completa, 14 observações previstas, zero executadas, coleta incompleta e julgamento não avaliado.
- [verificacao-instrumento.json](verificacao-instrumento.json): resultados dos testes e conferências desta preparação.

## Verificações do instrumento

As 13 verificações passaram em 3,39 s: matriz/ordem/query, rejeição de fixture que mistura identidade e contexto, rejeição de query divergente, bloqueio e contagem de DNS/conexão/UDP/subprocesso, localização de segredo antes de omissão, isolamento/restauração do ambiente, três percursos de teste com SDK/aplicação reais e garantia de que `preparar` não chama as observações.

Os três percursos de teste usam IDs próprios `INSTRUMENTO-*`, sem lote oficial ou julgamento do cenário; não são somados às 14 observações planejadas. A resposta de inferência continua sintética e não avalia conteúdo clínico ou fidelidade documental. Os 244 testes existentes passaram separadamente em 2,70 s. Lint e compilação dos dois novos módulos passaram.

## Coleta posterior

O [executor](../c06/executar.py) dispõe de `preparar` e `coletar`. A coleta posterior criará outro lote único com cópias das fontes, pedidos HTTP sem cabeçalhos secretos, snapshots de banco, logs e diagnósticos de localização dos marcadores. O registro de sucesso técnico não atribui automaticamente aprovação dos critérios de minimização, logs ou credenciais. A conferência posterior e a síntese interpretativa devem distinguir dados digitados pelo usuário, dados adicionados automaticamente, persistência e logs.

Nenhum achado de segurança ou classificação jurídica pode ser derivado apenas deste lote de preparação.
