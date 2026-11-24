# R-303 - avaliacao da meta de 1 microampere

Estado: protocolo preliminar. A meta de 0,001 mA ainda nao foi definida como resolucao ou
incerteza; nao ha dispositivo, fuel gauge, referencia calibrada ou serie de corrente no
repositorio. R-302 tambem depende de ensaios externos. Portanto, nenhum veredito experimental
de 1 microampere pode ser emitido agora.

## Grandeza e escopo

`0,001 mA = 1 microampere`. Isso e unidade de corrente. O objetivo principal escolhido para
R-302 e carga total em mAh; uma cifra de mAh no BatteryStats nao prova resolucao de corrente.
Uma avaliacao de 1 microampere exige uma fonte de corrente (por exemplo, fuel gauge ou
instrumento externo), amostras com tempo e uma referencia caracterizada. Nao usar as colunas
`*_estimated_charge_mah` do parser como leituras de corrente.

## Decisao metrologica obrigatoria

Escolher e registrar antes da coleta:

1. **Resolucao efetiva:** menor mudanca de corrente distinguivel na faixa e taxa de
   atualizacao declaradas. Um campo inteiro em microamperes ou casas decimais impressas nao
   estabelecem essa resolucao.
2. **Incerteza:** incerteza expandida maxima de uma estimativa de corrente, com nivel de
   abrangencia, faixa, janela de media e condicoes definidos. Repetibilidade isolada nao
   substitui calibracao nem corrige vies sistematico.

Se a meta continuar indefinida, o resultado de R-303 permanece `nao avaliado`. Nao converter
um teste de resolucao em afirmacao de exatidao.

## Preparacao e dados brutos

- Registrar modelo do dispositivo, build, fuel gauge, driver, resistor de sense, API e
  permissao de leitura, configuracao de media, temperatura e estado de carga.
- Registrar instrumento de referencia, identificador e certificado de calibracao, faixa,
  resolucao, taxa de amostragem, incerteza e data de validade.
- Guardar para cada amostra: timestamp monotono e UTC, valor bruto e unidade, estado de carga,
  condicao do ensaio, origem, flags de erro e hash do arquivo bruto.
- Identificar explicitamente o sinal de carga/descarga e a convencao da API.
- Documentar alimentacao do dispositivo e conexao do instrumento, evitando que a coleta mude
  a carga eletrica que se pretende observar.

## Ensaios

1. Verificar a propriedade de corrente disponivel, seu valor sentinela quando indisponivel,
   o menor passo reportado e a taxa efetiva de atualizacao observada; distinguir leituras
   repetidas do mesmo update de amostras novas.
2. Medir zero/offset em configuracao apropriada para o instrumento, com repeticoes e
   variacao de temperatura e estado de carga.
3. Aplicar patamares de corrente conhecidos em pontos ao longo da faixa alvo. Repetir subida
   e descida para detectar histerese, ruido, nao linearidade e deriva.
4. Comparar leituras do Android e da referencia em janelas sincronizadas. Registrar perdas,
   atraso e aliasing. Repetir cada condicao e manter todos os arquivos brutos.
5. Para resolucao, estimar passo efetivo e probabilidade de distinguir patamares proximos.
   Para incerteza, construir orcamento com referencia, offset, ganho, ruido, sincronizacao,
   deriva e correlacoes, mais fator de abrangencia declarado.

## Regra de decisao

- **Resolucao de 1 microampere:** aceitar somente se o protocolo escolhido demonstrar
  separacao repetivel de uma mudanca de 1 microampere na faixa e taxa declaradas.
- **Incerteza de 1 microampere:** aceitar somente se a incerteza expandida calculada e
  rastreavel nao exceder 1 microampere em toda a faixa declarada.
- Caso faltem referencia, metadados, definicao da meta ou dados suficientes, classificar como
  `nao avaliado`. Se os resultados validos excederem o limite, classificar como `rejeitado`.

## Fontes

- Android, [BatteryManager API](https://developer.android.com/reference/android/os/BatteryManager).
- AOSP, [Measure device power](https://source.android.com/docs/core/power/device).
- AOSP, [Power profiles](https://source.android.com/docs/core/power).
