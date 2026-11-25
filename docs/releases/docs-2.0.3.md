# AEMA — documentação 2.0.3 e experimento ultraleve 1.0.0

Entrega do experimento Ridge/MLP, executável sem GPU ou novos frameworks. App/pacote
permanecem 2.0.1, dependências e contratos do produto preservados. Não há novo APK.

O [estudo 7](../estudos/07-COMPARACAO-RIDGE-MLP.md) contém desenho, resultados, recursos,
fontes locais e limites. O [guia dos experimentos](../../experiments/README.md) descreve
comandos. A edição 2.0.3 é melhoria incremental documental; o novo componente
experimental inicia na etapa 1.0.0, segundo a classificação do projeto.

Ridge teve menor MAE de consumo que MLP nos dois regimes sintéticos e foi escolhido
pela validação nos dez casos pareados. Os pesos da rede ocupam 2,4–5,8 KB em FP32
binário teórico; arquivos JSON medidos ocupam 14–32 KB. Ridge tem 700 bytes em pesos,
192 bytes de normalizadores e JSONs medidos de aproximadamente 5 KB. O ranking dos
maiores consumidores não tem o mesmo vencedor do erro total.

As duas famílias foram exportadas e relidas com paridade menor que 0,001 mAh sintético
em todas as linhas de teste. Pesos exportados são somente pesquisa, sem instalação no
Android ou precisão física validada. Os artefatos de pesquisa incluem relatórios,
modelos sintéticos, código e checksums; não incluem dados de uso pessoal.

Verificações locais: **209 testes Python passaram**, incluindo sete casos específicos
do experimento; cobertura do pacote de produto **92,74%** (não é cobertura do novo
script de pesquisa). Ruff check/format passaram em `src`, `tests` e `experiments`.
Conferidos links documentais, integridade JSON, hashes dos modelos e versões preservadas
do app/pacote. Os testes Android não foram repetidos porque não houve mudança no app.
