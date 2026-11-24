# Resultados - modelo para R-502

Estado: estrutura de redacao, sem resultados experimentais. Nao preencher com valores da
captura unica como se fossem medidas de referencia.

## Escopo aprovado

- Pergunta cientifica e hipotese: pendentes de R-001.
- Grandeza primaria: carga total em mAh.
- Populacao de dispositivos, builds e condicoes: pendente.
- Referencia, calibracao, faixa e incerteza: pendente.
- Identificador e SHA-256 do protocolo congelado: pendente.

## Metodo executado

Descrever dispositivo/build, instrumento, configuracao, janela, sincronizacao, baseline,
workloads, numero planejado de repeticoes e criterios de exclusao. Registrar desvios do
protocolo como desvios, nunca como edicoes retroativas do plano.

## Fluxo dos dados

| Condicao | Planejados | Capturados | Excluidos (motivo) | Validos |
|---|---:|---:|---|---:|
| A preencher com o ledger auditado | | | | |

Relatar hashes das entradas brutas, manifesto de aquisicao e saida de
`python -m aema.study protocolo.json ensaios.csv`. A auditoria do ledger nao certifica
calibracao ou sincronizacao fisica; estas evidencias devem ser revisadas separadamente.

## Comparacao primaria

| Condicao | BatteryStats (mAh) | Referencia (mAh) | Erro assinado (mAh) | Repetibilidade | Incerteza |
|---|---:|---:|---:|---:|---|
| A preencher somente apos R-501 | | | | | |

Explicar sinal do erro, dispersao, incerteza da referencia, possiveis vieses e tratamento
de correlacoes. Nao confundir desvio-padrao entre repeticoes com incerteza expandida.

## Atribuicao e limite das conclusoes

Separar explicitamente:

| Tipo de numero | Fonte | Conclusao permitida |
|---|---|---|
| Estimativa por componente/UID | BatteryStats | Atribuicao modelada pelo Android |
| Carga total de referencia | Instrumento externo caracterizado | Resultado na janela e faixa validada |
| Atividade (tempo/bytes/contagem) | Check-in | Proxy de atividade, nao energia medida |

Nao afirmar 1 microampere, energia de RAM ou energia exclusiva de componente sem as
evidencias e ensaios R-303/R-305. Registrar limitacoes de generalizacao por dispositivo.

## Matriz afirmacao-evidencia

Antes de finalizar cada afirmacao quantitativa, indicar arquivo/hash, janela, unidade,
metodo, condicao, estatistica, incerteza, exclusoes e referencia. Ausencia de qualquer
item necessario deve resultar em uma afirmacao mais estreita ou em `nao avaliado`.
