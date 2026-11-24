# R-402 - sincronizacao e custo da coleta

Estado: contrato preliminar. O repositorio processa arquivos ja coletados e nao possui
coletor de corrente ou tracing. Nao ha overhead ou perda medidos.

## Relogios e eventos

Cada fonte deve registrar um dominio de relogio declarado, timestamp monotono da amostra,
timestamp UTC auxiliar, identificador de sessao e marcadores de inicio/fim. Guardar pares de
sincronizacao entre Android e instrumento externo no inicio e no fim de cada ensaio, com
incerteza e deriva estimadas. Nao alinhar apenas por UTC de arquivo ou por ordem das linhas.
Se Perfetto for usado, preservar os `ClockSnapshot` para converter dominios de relogio.

## Integridade

- Preservar dados brutos, configuracao do coletor, taxa solicitada e taxa observada.
- Registrar numero esperado e recebido de amostras, gaps, eventos perdidos, buffer cheio,
  reinicios, leituras repetidas do gauge e hashes dos arquivos.
- Definir antes do ensaio limite de perda, tolerancia de desalinhamento e janela maxima sem
  amostras. Rejeitar ensaios que ultrapassarem os limites; registrar o motivo.
- Usar janelas identicas para referencia e BatteryStats; quantificar o erro temporal de
  alinhamento e seu efeito no integral de carga.

## Overhead

Comparar o mesmo workload com e sem coleta, em ordem alternada e com repeticoes. Usar uma
referencia externa independente para medir carga total em mAh e registrar CPU, temperatura,
duracao e estado de carga. Relatar diferenca media, dispersao e incerteza; nao atribuir todo
desvio ao coletor sem controlar deriva e variacao natural. O limite aceitavel deve ser
estabelecido antes de observar os dados.

## Aceite pendente

R-402 exige coletor real, clocks sincronizados, ensaios com/sem coleta, teste de perda e
limites predefinidos. O parser host-side atual nao permite concluir essa fase.

Fonte: [Perfetto - Clock synchronization](https://perfetto.dev/docs/concepts/clock-sync).
