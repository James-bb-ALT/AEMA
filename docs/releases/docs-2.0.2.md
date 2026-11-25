# Documentação AEMA 2.0.2 — alternativas ultraleves

Melhoria incremental documental de 24/11/2026, conforme a classificação do projeto.
App e pacote Python permanecem 2.0.1. Dependências, schemas, modelos instalados e
funcionalidades de coleta/leitura não foram alterados. Esta etapa não gera novo APK.

O [estudo 6](../estudos/06-MODELOS-ULTRALEVES-E-REDES-NEURAIS.md) compara redes pequenas
e modelos tabulares para prever seis horas de consumo. Analisa os exemplos Indra OCR
e EmbeddingGemma 2, separa previsão de busca semântica e propõe experimento com Ridge,
árvores rasas e MLP compacta. Registra cálculo de parâmetros/pesos, inspeção local dos
APKs e o custo adicional do runtime Python, sem chamar essas contas de benchmark.

Fontes primárias F25–F34 foram acrescentadas ao registro. O protocolo propõe atributos,
tratamento de janelas/reset, personalização, validação temporal e critérios de recursos
a medir. Os resultados e scripts históricos de 2.0.1 continuam preservados.

Verificação desta edição: 59 links locais em 7 páginas novas/alteradas, blocos de código,
integridade/unicidade das 34 entradas JSON e consistência das versões documentais. Nenhum código do
produto mudou; testes do produto não foram repetidos. Nenhuma nova rede foi treinada.
