# R-304 - validacao de atribuicao por componente

Estado: protocolo preliminar, sem resultado experimental. A meta principal do projeto esta
definida como carga total em mAh. R-304 e uma avaliacao adicional de atribuicao, dependente
dos dados e limites de R-302/R-303.

## Evidencia ja disponivel

O arquivo `stats.txt` (linhas 37151-37167) apresenta estimativas globais para tela, CPU,
Bluetooth, camera, audio, video, radio celular, sensores, GNSS, Wi-Fi, wakelock, display
ambiente e idle. A secao `On-battery energy consumer stats (microcoulombs)` declara
`Not supported on this device` (linhas 45703-45704). Portanto, esta captura permite estudar
as atribuicoes do BatteryStats, mas nao oferece medida de rail por componente neste hardware.

## Hipotese por componente

Definir uma hipotese isolada antes de cada ensaio: um workload deve alterar um componente
principal em relacao ao baseline. Registrar a metrica BatteryStats especifica, o recurso
ativado, possiveis recursos acoplados e o sinal esperado. Exemplos candidatos:

| Componente | Variacao controlada | Confundidores a controlar |
|---|---|---|
| Tela | brilho ou estado da tela | conteudo exibido, CPU, toque |
| CPU | carga computacional fixa | frequencia, termica, tela, memoria |
| Wi-Fi | trafego ou estado do radio | CPU, sinal, modem, retransmissoes |
| Bluetooth | trafego/estado do controlador | audio, CPU, dispositivo remoto |
| GNSS | aquisicao/uso de localizacao | tela, radio, ceu/sinal, CPU |

Uma mudanca no total do dispositivo apos ativar o componente nao e automaticamente energia
eletrica exclusiva daquele componente. Uma medicao de rail so pode ser chamada de medida do
componente quando o rail, sua abrangencia e unidade forem identificados no hardware usado.

## Coleta A/B

1. Selecionar device/build, condicao A (baseline), condicao B (workload), duracao e numero de
   repeticoes antes da coleta. Intercalar ou randomizar a ordem A/B e registrar temperatura,
   estado de carga, brilho, conectividade e potenciais interferencias.
2. Para cada repeticao, capturar a mesma janela no BatteryStats e na referencia externa
   calibrada. Se houver ODPM/PowerStats HAL, registrar rails disponiveis, escopo fisico,
   unidade, clock, taxa de atualizacao e suporte real do dispositivo.
3. Preservar leituras brutas, comandos, hashes, marcadores temporais e exclusoes. Nao subtrair
   valores acumulados de janelas distintas sem normalizar duracao e estado inicial.
4. Calcular `delta_estimado = B_BatteryStats - A_BatteryStats` para a metrica do componente.
   Calcular separadamente `delta_referencia = B_externa - A_externa` para a carga total. Essa
   referencia testa resposta incremental do dispositivo, nao isolamento do componente.
5. Se houver rail medido compativel, comparar tambem o delta desse rail com o delta estimado,
   preservando a diferenca de grandeza e unidade. Energia de rail nao vira mAh sem tensao
   correspondente e metodo de conversao documentado.
6. Reportar repetibilidade, vies, sincronizacao, incerteza, correlacoes e efeitos cruzados.
   O sinal deve ser maior que a variacao e incerteza relevantes para sustentar a conclusao.

## Decisao

- `validado para atribuicao`: metodo do rail ou referencia e escopo fisico identificados;
  resposta consistente, repetida e acima da incerteza; efeitos cruzados tratados.
- `proxy/estimativa util`: resposta A/B observada, mas sem isolamento fisico do componente
  ou sem orcamento de incerteza suficiente.
- `nao avaliado`: hardware, referencia, janelas ou repeticoes ausentes.
- `rejeitado`: dados validos contradizem a hipotese predefinida sob criterios estabelecidos.

Nao classificar zero mAh como consumo fisico zero. Nao somar componentes ou valores por UID
para afirmar uma medicao total sem conhecer as regras de atribuicao do Android.

## Fontes

- AOSP, [Measure component power](https://source.android.com/docs/core/power/component).
- AOSP, [Power stats HAL](https://source.android.com/docs/core/power/power-stats-hal).
- Android Developers, [Power Profiler](https://developer.android.com/studio/profile/power-profiler).
