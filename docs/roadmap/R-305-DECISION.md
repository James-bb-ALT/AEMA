# R-305 - viabilidade de medir RAM

## Decisao para a captura atual

**Medição de RAM indisponível.** `stats.csv` registra `pwi,memory,0` na linha 807.
Esse zero é uma atribuição estimada do BatteryStats, não uma leitura elétrica de DRAM e
não demonstra consumo físico nulo. `stats.txt` informa `On-battery energy consumer stats
(microcoulombs): Not supported on this device` nas linhas 45703-45704. Não há série
temporal de rail de memória, referência externa ou workload isolado no repositório.

## Limite da decisão

A decisão se aplica apenas aos dados disponíveis, não a todos os aparelhos Android.
Um contador de RAM usada, bytes ou page faults seria proxy de atividade, não energia.
ODPM/PowerStats HAL pode expor rails em dispositivos compatíveis, mas a existência,
abrangência e calibração do rail precisam ser verificadas no dispositivo escolhido.
Mesmo um rail chamado `memory` pode incluir outras cargas; o mapeamento físico importa.

## Para reavaliar

1. Identificar dispositivo/build e listar rails realmente disponíveis, suas unidades,
   abrangência, taxa de atualização e proveniência.
2. Executar baseline e workloads de memória isolados e repetidos, controlando CPU,
   frequência, tela, temperatura, rádio e estado de carga.
3. Sincronizar BatteryStats, rail e referência externa, preservar dados brutos e hashes.
4. Comparar incrementos contra baseline e orçamento de incerteza. Classificar como
   `medida`, `proxy` ou `indisponível` com escopo específico do dispositivo.

Fontes: [AOSP Power Stats HAL](https://source.android.com/docs/core/power/power-stats-hal),
[Android Power Profiler](https://developer.android.com/studio/profile/power-profiler).
