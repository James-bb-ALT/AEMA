# R-302 - protocolo para comparar carga total

Estado: protocolo preliminar. Nenhum resultado experimental foi produzido.

A captura historica pode fornecer `computed_drain_mah`, mas nao uma referencia externa.
`actual_drain_min_mah` e `actual_drain_max_mah` tambem sao valores do Android e nao
substituem instrumento calibrado. A exportacao minima `aema study-summary` preserva
esse total com unidade/limite sem publicar identificadores de app. O erro experimental,
a repetibilidade por condicao e a incerteza permanecem nao avaliados.

## Objetivo e grandeza

Comparar a carga total estimada por BatteryStats, em mAh, com a carga integrada por uma
referencia externa na mesma janela. Usar `computed_drain_mah` da secao `Estimated power use
(mAh)` como total primario candidato. Registrar separadamente `actual_drain_min_mah` e
`actual_drain_max_mah`; ambos sao numeros do Android, nao referencia independente.

A pergunta cientifica, a populacao de dispositivos e o significado da meta de 0,001 mA
dependem de R-001/R-004. Esta comparacao em mAh nao valida corrente instantanea em mA.

## Ensaio

1. Identificar dispositivo, build, bateria, instrumento, firmware, certificado de calibracao,
   faixa, resolucao, taxa de amostragem e incerteza declarada para a faixa usada.
2. Definir condicoes reproduziveis, incluindo repouso (baseline) e pelo menos uma carga de
   trabalho. Fixar brilho, radios, temperatura, estado de carga inicial e duracao planejada.
3. Antes de cada repeticao, registrar o estado do BatteryStats e o instante de inicio. Qualquer
   reset de estatisticas deve ser explicito, registrado e autorizado pelo protocolo; nunca
   executado pelo analisador.
4. Sincronizar marcadores de inicio e fim entre Android e instrumento. Registrar desvios de
   relogio e falhas de amostragem. O dispositivo nao deve receber carga USB durante o workload.
5. Preservar arquivos brutos, hashes SHA-256 e logs. Repetir cada condicao em ordem definida
   antes da coleta; registrar exclusoes sem apagar ensaios.
6. Integrar a corrente da referencia ao longo da janela para obter mAh, com sinal e unidade
   verificados. Registrar a regra de integracao, lacunas, offset e incerteza do instrumento.
7. Parear um unico total BatteryStats e um unico total de referencia por repeticao e janela.
   Rejeitar pares com janelas incompatíveis ou metadados ausentes.

## Tabela de ensaios pareados

Uma linha por repeticao. Campos minimos propostos:

`trial_id`, `condition`, `device_id`, `build_id`, `instrument_id`, `calibration_id`,
`window_start_utc`, `window_end_utc`, `clock_offset_ms`, `estimated_charge_mah`,
`reference_charge_mah`, `reference_standard_uncertainty_mah`, `battery_stats_sha256`,
`reference_sha256`, `exclusion_reason`.

Quando houver dados, executar `python -m aema.validation ensaios.csv` com `src` no
`PYTHONPATH` ou o pacote instalado. O analisador exige pelo menos duas repeticoes validas por
condicao, IDs unicos, hashes e janelas UTC. Ele rejeita a mistura de device, build,
instrumento ou calibracao dentro da mesma condicao e devolve JSON descritivo. A verificacao
fisica da sincronizacao e da calibracao continua sendo responsabilidade do protocolo.

O arquivo de referencia original deve guardar amostras com timestamp e corrente, ou uma
integracao assinada pelo instrumento com metodo documentado. Um numero digitado sem rastro
nao satisfaz o criterio de referencia. `reference_standard_uncertainty_mah` nao pode ser
inferido das casas decimais exibidas.

## Analise e publicacao

- Erro assinado por ensaio: `estimated_charge_mah - reference_charge_mah`.
- Erro relativo: erro assinado dividido pela referencia, apenas quando a referencia e positiva.
- Por condicao: numero de pares validos/excluidos, media do erro, erro absoluto medio,
  desvio-padrao amostral e distribuicao dos erros.
- Separar repetibilidade observada, incerteza da referencia, sincronizacao e possiveis vieses
  sistematicos. Nao somar incertezas como se fossem independentes sem modelo de correlacao.
- Publicar dados, protocolo congelado, versoes, hashes, criterios de exclusao e limites de
  generalizacao. Sem repeticoes e referencia calibrada, relatar apenas comparacao descritiva.

## Aceite pendente

R-302 so termina com pergunta/metrologia aprovadas, manifesto de aquisicao R-101, ensaios
repetidos com baseline e referencia calibrada, resultados por condicao e incerteza sustentada
por dados. A captura atual do repositorio nao atende a esses requisitos.

## Fontes

- Android, [Power profiles](https://source.android.com/docs/core/power).
- AOSP, [Measure device power](https://source.android.com/docs/core/power/device).
- Android Developers, [Batterystats workflow](https://developer.android.com/topic/performance/power/setup-battery-historian).
