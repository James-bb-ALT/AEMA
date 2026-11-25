# Ridge versus MLP pequena: experimento executado

24/11/2026 · Experimento **1.0.0** · Documentação **2.0.3** · App/pacote **2.0.1**.

**Resultado:** neste gerador sintético, Ridge foi mais preciso para consumo que as
MLPs candidatas e foi selecionado na validação em todos os dez casos pareados. A MLP
aprendeu e seus pesos exportados reproduziram a inferência de referência, mas não
superou Ridge. Isso favorece Ridge como primeira implementação candidata; não prova
precisão no telefone nem superioridade universal de uma família de modelos.

Código: [`ultralight_validation.py`](../../experiments/ultralight_validation.py).
Resultados completos: [JSON da execução](resultados/ultralight-1.0.0.json).
Reprodução e ambiente: [guia dos experimentos](../../experiments/README.md).

## Pergunta e desenho

Uma rede pequena consegue superar uma regressão regularizada usando o mesmo histórico
para prever o consumo das seis horas seguintes? Há custo pequeno e exportação portátil?
O teste compara capacidade técnica em simulação porque não há um conjunto de janelas
reais verificadas disponível para esse objetivo. As fontes conceituais continuam
[F29–F34](FONTES.md), do estudo anterior; esta etapa acrescenta evidência local.

Reutilizamos o processo sintético do estudo 5, sem mudar o experimento histórico:
112 dias com quatro slots por dia, quatro componentes e três UIDs sintéticos, padrão
horário/semanal e mudança de rotina no dia 80. Usamos sementes 17, 42, 103, 251, 907.
O segundo regime aplica uma transformação quadrática/limiar de carga ao mesmo processo.
São **cinco séries de origem e dois regimes pareados**, não dez aparelhos ou dez séries
independentes. O regime não linear foi definido antes de consultar seus resultados.

Cada caso usa 216 janelas de treino (até dia 56), 56 para validação (dias 56–70) e
168 para teste (dias 70–112). O início descarta oito slots para formar os lags. Atributos
no instante t usam somente valores já observados até t−1 e calendário conhecido.
Alvo é o slot t, equivalente às próximas seis horas nesse gerador. Não há rótulos de
energia medida nem nomes de apps reais. Componentes e UIDs são eixos sobrepostos;
o total é calculado somente nos quatro componentes.

## Modelos e seleção pré-teste

Todos usam **24 atributos e sete saídas**: consumo no slot anterior, no mesmo horário
do dia anterior, média dos oito slots passados (21 valores), seno/cosseno de horário
e indicador de fim de semana (3). Os 96 atributos do estudo 6 eram um exemplo de
orçamento; não foram criados campos fictícios para atingir esse tamanho.

- Ridge: normalização ajustada no treino, intercepto não penalizado e alpha em
  `{0,1; 1; 10; 100}`. A validação escolhe alpha.
- MLP: camadas ocultas `(16,8)` ou `(32,16)`, ReLU, saída linear, duas penalizações L2
  `{0,001; 0,01}`. Adam implementado em NumPy, taxa 0,003, batch de treino completo,
  máximo 600 épocas e paciência de 60 épocas. Normalizadores de entradas e alvos são
  ajustados somente no treino. A validação escolhe a configuração e a melhor época;
  não há divisão interna aleatória que misture passado/futuro.
- Ambos refazem o ajuste em treino + validação, com hiperparâmetros/épocas fixados,
  antes da avaliação de teste. Previsões negativas são limitadas a zero.
- Valor do dia anterior e média por horário antes do teste são referências simples.
  A decisão registrada `validation_selected_model` compara somente Ridge e MLP pelo
  MAE médio dos sete alvos na validação; o teste não seleciona o vencedor.

Quatro configurações por família não equivalem a uma busca completa das arquiteturas.
Foi usada uma inicialização da rede por caso/semente. Não foram ajustadas opções após
observar o teste. A escolha conjunta dos sete alvos não otimiza diretamente ranking;
isso é uma limitação deliberadamente registrada, não um erro a esconder.

## Resultado de consumo no teste

MAE do total dos componentes em **mAh sintéticos por seis horas**, média das cinco
sementes. Valores menores são melhores; arredondamento apenas nesta tabela.

| Modelo | Rotina com mudança | Transformação não linear com mudança |
|---|---:|---:|
| Valor do dia anterior | 62,97 | 79,27 |
| Média por horário | 63,95 | 81,71 |
| Ridge | **60,58** | **76,60** |
| MLP selecionada | 68,60 | 88,38 |

Ridge foi escolhido na validação nos dez casos e teve menor MAE total que a MLP no
teste em todos eles. Isso não significa que venceu o baseline em cada semente: na
semente 42, o valor do dia anterior foi melhor que ambos. O teste não é reusado para
trocar de modelo ou ajustar hiperparâmetros. O JSON registra cada semente, erros por
componente/UID, RMSE, WAPE e ranking, incluindo o resultado da seleção pré-teste.
Os resultados do Ridge são comparáveis ao modelo **congelado** anterior; não à versão
com atualização móvel de 28 dias, que tem outro regime de aprendizagem.

## Maiores consumidores são outro objetivo

Acerto top-1 médio no cenário de rotina, em proporção de intervalos sintéticos:

| Modelo | Maior componente | Maior UID |
|---|---:|---:|
| Valor do dia anterior | **0,788** | 0,856 |
| Média por horário | 0,689 | **0,905** |
| Ridge | 0,721 | 0,894 |
| MLP | 0,689 | 0,874 |

Menor erro no total não implica melhor escolha do maior consumidor. Para o produto,
precisão de consumo e ranking precisam de critérios separados, escolhidos na validação,
sem usar os números do teste para decidir um novo ranking nesta execução. O cenário
não linear e detalhes por semente estão no JSON. A métrica usa argmax; não houve
estudo específico de empates nem top-3 aqui. Os sete alvos simulados não representam
variedade de apps, instalação nova, fabricantes ou UIDs compartilhados reais.

## Tamanho, treino e execução medidos

Máquina: AMD Ryzen 7 5700X, Windows x86_64, Python 3.13.9 e NumPy 2.5.3.
`OPENBLAS_NUM_THREADS=1` e `OMP_NUM_THREADS=1` definidos antes de iniciar Python.
Sem GPU, PyTorch, scikit-learn ou download de pesos neste experimento.

| Item | Ridge | MLP selecionada |
|---|---:|---:|
| Parâmetros de pesos/bias | 175 | 599–1.447 |
| Pesos FP32 binários, cálculo | 700 bytes | 2.396–5.788 bytes |
| Normalizadores FP32, cálculo | 192 bytes | 248 bytes |
| Arquivo JSON exportado, medido | 5.029–5.090 bytes | 14.278–31.622 bytes |
| Busca + refit por caso, medido | 0,0012–0,0323 s | 0,482–1,368 s |
| p95 host NumPy por linha (sete saídas) | 0,025–0,082 ms | 0,026–0,194 ms |
| p95 host por listas/loops escalares | 0,033–0,104 ms | 0,181–0,615 ms |

As faixas de tempo representam dez execuções; não intervalos de confiança. Cada
benchmark de inferência mede uma linha fixa, com 20 aquecimentos e 500 repetições.
São temporizações de CPU no computador; não são desempenho Android, custo cold-start,
RAM incremental, APK reduzido ou energia. Nenhum ganho de bateria foi medido.
O treino das quatro opções MLP e refit levou 8,17 s somados nos dez casos; Ridge
levou 0,049 s para sua busca/refit. Pequenos tempos são sensíveis a ruído do host.

O JSON serializa números arredondados para FP32 em texto; isso explica a diferença
para a conta de pesos binários. Contém ordem dos atributos/alvos, normalizadores,
versões, marcação sintética e hash do arquivo no relatório. Um arquivo final de
produção ainda precisa de validação de contrato/limites e carregamento seguro.
Os modelos não foram quantizados int8 nem instalados no app.

## Provas executadas e limites

- Mutação deliberada de rótulos futuros preservou os atributos na origem da previsão
  e os dados usados pelo ajuste/seleção. Normalização da MLP foi conferida contra o
  treino no teste automatizado; seleção de época corresponde à loss de validação.
- As duas famílias foram exportadas, relidas de JSON e executadas por loops escalares
  sobre todas as 168 linhas de teste por caso. Maior diferença de previsão versus
  referência: MLP 0,0000543 mAh sintético; Ridge 0,0000141. Limite de aceite: 0,001.
  É paridade host, não validação Android ou do formato por leitores externos.
- Teste separado de aprendizado verifica que a rede reduz erro em um sinal artificial
  reservado. Testes rejeitam arrays curtos, dimensões erradas, NaN e valores negativos.
  A suíte completa e a verificação de estilo são registradas na release desta edição.

Não há dados reais suficientes para concluir qual será mais preciso no telefone.
Não houve migração de Chaquopy, redução de APK, versão móvel do preditor, aprendizagem
contínua, validação de carregamento no Android ou comprovação de economia. O pipeline
de janelas reais com controle de reset e rótulos futuros continua necessário.

## Decisão desta etapa

O custo de inferência de uma rede pequena é tecnicamente compatível com um protótipo
ultraleve **no host medido**, mas a MLP não justificou custo adicional neste conjunto.
Manter Ridge como primeira candidata para consumo, conservar baselines para ranking
e avaliar com janelas reais antes de escolher o modelo do app. O próximo teste móvel
deve usar os pesos pequenos e contrato verificado, com paridade host/Android e medição
do pipeline completo. Não instalar os pesos sintéticos como se fossem treino pessoal.
