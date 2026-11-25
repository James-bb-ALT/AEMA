# Previsão ultraleve: redes pequenas, regressão e embeddings

Consulta: 24/11/2026. Edição documental 2.0.2; app/pacote existentes 2.0.1.
Pedido: reduzir substancialmente armazenamento, memória e custo da IA, usando Indra
OCR e EmbeddingGemma 2 como referências de especialização. Estudo exploratório com
fontes primárias; nenhuma substituição de modelo ou nova rede treinada nesta etapa.

**Execução posterior:** a documentação 2.0.3 acrescenta o
[experimento Ridge/MLP 1.0.0](07-COMPARACAO-RIDGE-MLP.md). Ridge venceu em erro de
consumo nos regimes sintéticos testados; a rede treinou/exportou, sem ganho de precisão.
O texto abaixo preserva a proposta original, não descreve o estado da execução posterior.

## Recomendação

Comparar **Ridge, árvores pequenas e uma MLP compacta treinada em atributos numéricos**,
com previsão de consumo nas próximas seis horas e ordenação dos maiores consumidores.
A MLP é uma rede neural; LLMs e modelos de embeddings também são redes neurais, mas
foram treinados para tarefas diferentes. A escolha depende da tarefa e dos dados,
não do rótulo “IA”. Para o AEMA, a proposta é prever números diretamente e apresentar
explicações por modelos de texto fixos preenchidos com evidências verificáveis.

Esta recomendação é uma inferência de engenharia, não uma vitória experimental da MLP.
O Ridge continua candidato principal com poucos dados: na simulação anterior teve
resultado favorável, mas isso não determina o desempenho em dados reais. Ver
[ensaio sintético anterior](05-SIMULACAO-E-VIABILIDADE-LLM.md).

## O que os dois exemplos realmente oferecem

**Indra OCR.** O autor descreve um OCR de 1 milhão de parâmetros executável em CPU,
com pipeline de reconhecimento e processamento de documentos. É uma referência de
especialização: resolver uma tarefa limitada pode exigir muito menos capacidade que
um modelo generativo geral. Seus pesos, entradas e objetivos são de OCR; não fornecem
um preditor de consumo e não há motivo demonstrado para transferi-los ao BatteryStats.
O número de parâmetros anunciado não equivale ao tamanho de toda a aplicação, seus
modelos auxiliares, bibliotecas ou memória. O benchmark divulgado de 49 páginas/s usa
32 núcleos em servidor AMD EPYC; não é benchmark Android. O README atual e o artigo
original descrevem versões diferentes: não combinar números entre essas versões.
[Artigo do autor](https://www.datalab.to/blog/indra-ocr),
[repositório do autor](https://github.com/datalab-to/indra).

**EmbeddingGemma 2.** O guia oficial identifica 270 milhões de parâmetros para texto,
e até 740 milhões com visão e áudio. A função é produzir representações vetoriais
para busca/recuperação e tarefas derivadas; não prevê mAh diretamente nem gera a
explicação do relatório. Encurtar o vetor de saída de 768 para 128 dimensões reduz
armazenamento dos vetores, não os pesos da rede. Poderia buscar episódios semelhantes
ou documentos, mas exigiria outra camada para prever consumo. Como os registros do
AEMA já são estruturados, transformar números em texto e depois em embeddings é
uma hipótese adicional que precisa superar a alternativa numérica simples.
[Guia oficial](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/),
[visão geral oficial](https://ai.google.dev/gemma/docs/embeddinggemma).

Conclusão aplicada: seguir a ideia de **modelo específico pequeno** do Indra, não
usar o OCR no projeto. Não adotar EmbeddingGemma como substituto direto do preditor.
Um “embedding” treinável de identidade de aplicativo, caso necessário, é uma pequena
tabela numérica própria; não exige EmbeddingGemma nem compreensão de linguagem.

## Comparação para o AEMA

Tamanhos abaixo são faixas de projeto ou cálculos de pesos, não arquivos exportados
nem medições de RAM. Runtime, escalas, metadados, tensores temporários e coleção de
dados têm custos adicionais. Modelos treinados não acompanham esta edição.

| Candidato | Papel proposto | Escala candidata | Limite / decisão |
|---|---|---|---|
| Média por horário / valor do dia anterior | Referência e fallback | Dezenas a milhares de valores | Obrigatório comparar; aproveita rotina repetida, reage mal a mudanças. |
| Ridge / regressão linear regularizada | Prever consumo por alvo com lags e contexto | Centenas a milhares de coeficientes | Priorizar com poucas janelas; atualização barata e inspeção direta. |
| Árvores rasas / boosting limitado | Relações não lineares em dados tabulares | Centenas de KB a poucos MB como orçamento | Limitar número/profundidade; tamanho não é dado só por “parâmetros”. |
| MLP pequena | Regressão não linear de atributos normalizados | Cerca de 3,6 mil a 50 mil parâmetros como busca inicial | Melhor primeira rede candidata; exige treino e comparação temporal. |
| CNN temporal / GRU pequena | Processar sequências, ordem e estados | Orçamento inicial de 10 mil a 100 mil parâmetros | Só avançar se MLP/Ridge não capturarem padrão e houver sequências válidas suficientes. |
| DLinear / TSMixer reduzido | Modelar histórico temporal explícito | Depende da janela, canais e largura; contar cada arquitetura | Pesquisa promissora; não existe tamanho universal de “DLinear”/“TSMixer”. |
| EmbeddingGemma 2 | Busca semântica de textos/episódios | 270M texto; 740M completo segundo produtor | Não é o preditor numérico; custo ainda muito superior ao alvo mínimo. |
| Qwen3-0.6B atual | Selecionar evidências de snapshot | GGUF Q8_0 de 639.446.688 bytes nesta release | Já executado; não treinado para previsão pessoal. Inadequado como padrão para nova meta ultraleve. |

Modelos lineares simples são baselines sérios em previsão temporal: o trabalho
[LTSF-Linear](https://arxiv.org/abs/2205.13504) compara arquiteturas em seus próprios
datasets e encontra resultados favoráveis à simplicidade. Isso não prova superioridade
em bateria. O [TSMixer do Google](https://research.google/blog/tsmixer-an-all-mlp-architecture-for-time-series-forecasting/)
combina camadas MLP ao longo do tempo e dos atributos; fornece alternativa sem atenção
para comparação. Nesta revisão foram lidos resumo do primeiro e descrição técnica
do produtor do segundo, sem reprodução dos benchmarks.

## Uma rede concreta pequena o suficiente

Proposta inicial, ainda não treinada: vetor de **96 atributos**, duas camadas ocultas
ReLU e saída de regressão. O número 96 é um orçamento ilustrativo; a lista real só
deve incluir campos disponíveis e verificados, com máscara de ausência. Não se assume
que o coletor atual já produz todos esses atributos de janela.

| Exemplo de rede densa (incluindo biases) | Parâmetros | Pesos FP32 | Armazenamento int8 idealizado |
|---|---:|---:|---:|
| 96 → 32 → 16 → 1 | 3.649 | 14.596 bytes | 3.649 bytes |
| 96 → 64 → 32 → 16 | 8.816 | 35.264 bytes | 8.816 bytes |

Conta reproduzida localmente: `sum((entrada + 1) * saida)` para cada par de camadas.
O arquivo final será maior: normalização, biases int32 em implementações quantizadas,
escalas, formato e metadados não estão no cálculo int8. Não são estimativas de RAM.
Com 50 mil parâmetros, FP32 ocupa 200 mil bytes apenas em pesos; quantizar não é
necessário para provar que a arquitetura já pode ser pequena.

Separar dois usos: uma rede com saída escalar compartilhada pode receber contexto de
um app/componente e prever seu alvo, repetindo a avaliação por entidade; uma rede de
saída fixa pode prever um conjunto fixo de componentes. As 16 saídas do exemplo são
ilustrativas, não uma lista de apps cadastrada. Uma saída por pacote instalado cria
problemas de apps novos e troca de telefone. Considerar atributos de comportamento,
categoria quando confiável, fallback de entidade nova e personalização local. Não
atribuir o consumo de um UID compartilhado a um pacote isolado.

## Dados e aprendizado ao longo do tempo

O principal bloqueio continua sendo construir pares válidos de **histórico observado
até t** e **consumo entre t e t+6h**. Os ZIPs atuais são snapshots acumulados desde o
reset Android. Subtrair sem controlar reset, reboot, carga, período coberto, mudança
de formato, campos ausentes e duração real pode produzir rótulos incorretos.
Preservar os brutos; rejeitar ou marcar intervalos inválidos. Campos ausentes não
viram zero. Quando o fabricante só fornecer estimativas, o alvo será explicitamente
“estimativa BatteryStats futura”, não medição elétrica exata.

Entradas candidatas: lags de consumo, médias móveis, hora/dia, duração do intervalo,
indicadores de carga e dados de uso coletáveis. Só usar contexto conhecido no instante
da previsão; uso das próximas seis horas só entra em cenário informado pelo usuário.
Treinar consumo por componente e por UID em eixos separados: eles se sobrepõem.
Não somar os dois eixos, nem usar percentual de bateria para alegar causalidade por app.

Quatro janelas não sobrepostas por dia rendem no máximo **112 em 28 dias**, **360 em
90 dias**, antes das exclusões. Cem apps não transformam 112 intervalos em 11.200
observações independentes: os mesmos hábitos e contextos se repetem entre entidades.
Com tão poucos períodos, uma rede maior pode memorizar; começar com baseline/Ridge,
curvas de aprendizado e abstenção quando o histórico for insuficiente. Nenhum número
de dias é garantia de precisão. Compatibilidade “qualquer telefone” exige controles
de disponibilidade por fabricante e testes em aparelhos diferentes.

Treino inicial no computador continua autorizado pelo desenho do projeto. Exportar
pesos, normalizador, ordem/unidades dos atributos, versão de schema, dispositivo de
origem e métricas, com hash e substituição atômica. Evitar desserializar pickle recebido.
No telefone, a primeira personalização pode ser calibração de erro ou regressão
incremental; o [`SGDRegressor`](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDRegressor.html)
documenta `partial_fit` como referência de método, não como dependência Android proposta.
Atualizar somente depois de chegar o rótulo de seis horas; guardar modelo anterior e
reverter se piorar em validação temporal. Fine-tuning local de MLP fica para uma etapa
posterior, condicionado a memória, tempo, energia e estabilidade medidos.

## Runtime e tamanho do aplicativo

Inspeção local dos APKs publicados 2.0.1 com `zipfile.ZipFile.infolist()` e soma de
`compress_size`; bytes decimais. É inspeção de armazenamento, não perfil de memória:

| Item | Bytes |
|---|---:|
| APK light no disco | 98.423.493 |
| APK com Qwen no disco | 737.870.307 |
| Entradas relacionadas a Python/Chaquopy, soma comprimida | 82.922.547 |
| Outras entradas nativas em `lib/`, soma comprimida | 14.392.824 |
| Asset GGUF sem compressão | 639.446.688 |

A classificação por nome de entrada é aproximada: `chaquopy` ou `python` no caminho;
demais `lib/` em outro grupo. Assinatura, alinhamento e cabeçalhos explicam a diferença
entre as somas e o tamanho final. Não se atribui toda biblioteca nativa a llama.cpp.
Mesmo sem pesos, a base atual continua grande. O app usa Python/pandas para compartilhar
parsers com o computador; remover esse custo implica uma migração real de arquitetura,
testes de paridade e preservação dos formatos. Esta pesquisa não executa essa migração.

Para MLP pequena, comparar uma implementação densa mínima em Kotlin/Java com runtime
padronizado. A primeira evita framework de rede no app, mas exige contrato restrito,
paridade numérica host/Android e testes de carregamento/limites; não é um runtime geral.
LiteRT oferece execução móvel/quantização; sua documentação atual sinaliza migração
para LiteRT Quantizer, portanto não copiar fluxo antigo de conversão sem conferir
versão. Int8 requer calibração representativa de treino e comparação pós-quantização
no teste separado. [Documentação Google AI Edge](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_integer_quant).

ONNX Runtime é alternativa com operações suportadas e build reduzida por modelo.
Os tamanhos que sua documentação apresenta são exemplos de uma versão/modelo, não
previsões para este app. Para redes com poucos KB, a biblioteca pode custar mais que
os pesos; medir o APK completo. [Guia mobile](https://onnxruntime.ai/docs/tutorials/mobile/),
[build customizada](https://onnxruntime.ai/docs/build/custom.html).

Orçamentos propostos para aceite, ainda não atingidos/medidos: pesos do preditor até
1 MB; memória incremental do preditor até 16 MB; p95 de uma rodada completa de previsões
até 100 ms em CPU de telefone de referência. Medir número real de apps, cold/warm,
carregamento e pré-processamento; não extrapolar uma chamada escalar. Meta de APK mínimo
até 25 MB só após protótipo nativo/uma ABI: não é previsão do tamanho da base atual.
Registrar também espaço instalado, overhead de coleta e energia por dia. Não manter
um processo de IA carregado o dia inteiro para prever quatro vezes ao dia.

## Próximo experimento recomendado

1. Gerar janelas reais verificadas, com previsão persistida antes da chegada do alvo.
   Comparar dia anterior, média por horário, Ridge, árvores rasas e MLP pequena usando
   exatamente os mesmos atributos e splits cronológicos agrupados por intervalo.
2. Selecionar hiperparâmetros na validação e avaliar uma única vez no teste reservado.
   Incluir mudanças de rotina, apps novos e modo carregando/sem carga. Medir MAE total,
   erros por componente/UID, ranking top-1/top-3 com tratamento de empate e cobertura de
   abstenção. WAPE só com denominador válido; mAh e pontos percentuais são alvos distintos.
3. Escolher o menor modelo dentro de uma margem de erro pré-definida na validação.
   Medir arquivos, APK, PSS/RSS, tempo p50/p95 e energia no telefone; comparar FP32/int8
   e transferência para outro aparelho. Sugestões usam evidências previstas e textos
   locais, com indicação de incerteza; economia causal exige ensaio controlado separado.

Hipóteses: H1 — MLP compacta melhora erro sobre Ridge; H2 — calibração pessoal melhora
teste futuro; H3 — arquitetura nativa reduz overhead total; H4 — quantização mantém erro
dentro da tolerância escolhida. Todas permanecem abertas. Um modelo pequeno pode
aprender padrões; não pode conhecer mudanças futuras de uso sem informação disponível.

## Evidência e rastreabilidade

Fontes externas F25–F34 no [registro estruturado](fontes.json), com alcance de leitura.
Consulta via web disponível após Exa/Agent Reach retornar `Unknown MCP server 'exa'`.
Sem instalação, download de pesos, cookies ou execução dos benchmarks dos autores.
As contagens MLP foram calculadas; os tamanhos APK foram lidos dos artefatos locais.
Nenhuma latência, precisão ou energia de rede ultraleve foi medida nesta etapa.
