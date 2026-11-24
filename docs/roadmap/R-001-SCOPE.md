# R-001 - escopo cientifico proposto

Estado: rascunho para aprovacao do proprietario/orientador.

Grandeza primaria escolhida nesta conversa: **carga total em mAh**. Pergunta proposta:
"Qual e o erro da estimativa de carga total do BatteryStats, em mAh, em relacao a uma
referencia externa calibrada durante janelas e condicoes controladas?"

Hipotese proposta (ainda nao aprovada): o erro e a repetibilidade variam entre condicoes
de uso do mesmo dispositivo. A captura historica unica nao testa essa hipotese.

Populacao/dispositivo, condicoes, tamanho amostral, limite de erro aceitavel e referencia
continuam indefinidos. RAM, atribuicao por componente e meta de 1 microampere sao questoes
secundarias, nao criterios de sucesso da comparacao primaria em mAh.

Cheque dimensional: `computed_drain_mah` e referencia integrada de carga podem ser
comparados em mAh na mesma janela. Corrente em mA, potencia em mW e energia em mWh nao podem
ser comparadas diretamente com mAh. Uma razao mAh/tempo estimaria corrente media apenas
com janela e metodo declarados; isso nao valida corrente instantanea.
