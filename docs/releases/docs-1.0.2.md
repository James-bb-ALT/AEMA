# Documentação AEMA 1.0.2

Edição documental de 24/11/2026. Classificação do projeto: melhoria incremental da
documentação. App e pacote permanecem em **1.0.0**; dependências, schemas e catálogo
preservam suas versões. Esta release não contém um novo APK nem um modelo treinado.

## Conteúdo

- [Caderno de estudos](../estudos/README.md) com requisitos definidos pelo autor e
  conclusão provisória para previsão offline das próximas seis horas.
- Revisão de trabalhos de modelagem de consumo, previsão com LLMs e alternativas
  numéricas; resultados divergentes e limites de extrapolação documentados.
- Sete candidatos e triagem complementar, runtimes, licenças e orçamento de execução
  a medir em aparelhos a partir de 6 GB de RAM.
- Desenho de dataset, rótulos, personalização, avaliação temporal e ensaios de recomendações.
- [24 fontes primárias](../estudos/FONTES.md), datas/alcance de leitura e
  [registro estruturado](../estudos/fontes.json), incluindo revisões dos model cards.

O S25 Plus/One UI 9 foi informado pelo autor. Não houve conexão ao aparelho, benchmark
de modelos, treinamento, download de pesos ou nova validação elétrica nesta entrega.
Os números candidatos de memória, latência e ganho são propostas de ensaio, não resultados.

## Verificação e distribuição

Conferidos 110 links locais em 12 páginas alteradas/novas, blocos de código e consistência
dos 24 registros JSON com as fontes documentais. A suíte passou com **167 testes e
92,16% de cobertura**; Ruff check e format passaram. A mudança é documental; não exige
repetir os ensaios instrumentados históricos do app.
O ZIP documental inclui o manual e os estudos; links para código exigem o checkout
completo ou navegação no repositório. Nenhum dump pessoal integra o arquivo publicado.
