# 2. Metodologia de coleta e estudo

[Índice](../README.md) · [Anterior](01-OBJETO-E-HIPOTESES.md) · [Próximo](03-ARQUITETURA-E-TECNOLOGIAS.md)

## 2.1 Dois usos distintos dos dados

| Uso | O que se faz | Conclusão possível |
|---|---|---|
| Observação periódica | Snapshots a cada seis horas pelo app, sem reset | Descrever relatórios, padrões e falhas observados |
| Experimento controlado proposto | Workloads repetidos e referência externa na mesma janela | Avaliar erro e repetibilidade sob condições declaradas |

O primeiro uso fornece o acervo para análise posterior. Ele não satisfaz sozinho o
segundo. A coleta automática não sincroniza workloads, não integra corrente da referência,
não executa randomização e não transforma a série de snapshots em ensaios independentes.

## 2.2 Método já implementado: aquisição e preservação

O app recebe autorização do Shizuku, executa comandos fixos somente de leitura e grava
suas saídas em arquivos. Cada execução registra origem, timestamps, resultado dos comandos
e hashes; depois realiza parsing estrito e publica um ZIP com nome único. O host também
pode coletar esses mesmos relatórios por ADB.

| Arquivo | Comando lógico | Papel |
|---|---|---|
| `stats.csv` | `dumpsys batterystats --checkin` | Estatísticas tabulares Android |
| `stats.txt` | `dumpsys batterystats` | Relatório humano, incluindo estimativas de carga |
| `packageUID.txt` | `pm list packages -U` | Relação pacote/UID |
| `battery_state.txt` | `dumpsys battery` | Estado adicional preservado; sem parser elétrico dedicado |

Modelo, fingerprint e SDK são obtidos com `getprop`. No app, o identificador do manifesto
é um UUID de instalação, não o serial físico. No host, o serial ADB fornecido é registrado.
As quatro leituras são sequenciais; o intervalo inteiro de captura não implica que os
quatro arquivos representem o mesmo instante.

O intervalo nominal do app é `6 × 60 × 60 × 1000 = 21.600.000 ms`. Os alarmes são
rearmados por execução, a partir da âncora da automação. O arquivo registra horário previsto
e atraso; UTC facilita correlação e o relógio monotônico Android auxilia a observação de
intervalos durante o mesmo boot. Esses registros não realizam sincronização com instrumento.

## 2.3 Contadores acumulados e delimitação da janela

Um snapshot pode refletir atividade desde um reset ou outra janela interna do Android.
Coletá-lo a cada seis horas não altera essa origem. Somar snapshots acumulados provoca
dupla contagem. Subtrair dois totais só é defensável quando a semântica de acumulação,
o mesmo reset/base, unidade, contexto e continuidade estiverem demonstrados.

**O código 1.0.0 não calcula deltas entre snapshots.** O pesquisador deve registrar como
o total candidato corresponde à janela da referência. Se isso não puder ser demonstrado,
o par não deve entrar na análise controlada.

Um reset de BatteryStats, se necessário ao desenho, exige procedimento explícito no
protocolo aprovado. Ele não é feito automaticamente pelo app nem pelo analisador. Marque
início/fim do workload e preserve o estado anterior/posterior; não trate o horário de
download do arquivo como início do fenômeno físico.

## 2.4 Método proposto: experimento pareado

O desenho inicial candidato compara repouso e uma carga de trabalho reprodutível no
mesmo dispositivo/build. Outras condições só devem ser incluídas com justificativa e
capacidade de repetição. Para cada ensaio `i`, o par é `(Q_Android,i, Q_referência,i)`.

### Preparação

Defina população-alvo e aparelho inicial, grandeza, condições, janela, controles,
referência, margens de erro e regras de exclusão. Faça um piloto para avaliar variabilidade
e falhas; dimensione as repetições pelo objetivo inferencial. Não adote o mínimo de duas
linhas do software como cálculo amostral.

Registre modelo/build, bateria e condição física relevante, versão do app, instrumento,
certificado de calibração, faixa, taxa, sinal e ponto elétrico de medição. Uma medição
de entrada USB pode incluir perdas e caminhos de alimentação diferentes da descarga
da bateria. Ela não é automaticamente a referência da carga atribuída pelo BatteryStats.

### Execução proposta

1. Estabilizar o aparelho nas condições definidas e registrar estado inicial, carga e temperatura.
2. Registrar marcadores de início no Android e na referência; executar a condição na ordem predefinida.
3. Registrar fim, perdas, alterações térmicas e eventos de alimentação/reset; preservar os brutos das duas fontes.
4. Integrar a referência na janela compatível e construir uma linha do ledger com hashes e metadados.
5. Auditar o ledger contra o protocolo congelado antes de produzir as estatísticas descritivas.

Intercale ou randomize condições para reduzir confusão com deriva temporal e aquecimento.
Mantenha brilho, tela, rádio, sinal, conectividade, estado de carga, temperatura e tarefas
de fundo sob o controle previsto. Toda alteração relevante deve permanecer no registro.

O app usa seis horas para aquisição periódica; a duração do ensaio controlado não está
definida por esse número. Ela deve ser escolhida conforme a pergunta, a resolução efetiva
das fontes e o custo de repetir as condições.

## 2.5 Integração da referência e unidades

Para corrente de descarga em mA e tempo em segundos:

```text
Q_referência [mAh] = (1 / 3600) × integral de I_mA(t) dt
```

Uma regra candidata para amostras sincronizadas é a integração trapezoidal:

```text
Q_referência ≈ Σ ((I_k + I_(k+1)) / 2) × (t_(k+1) − t_k) / 3600
```

Essa integração é **proposta e não implementada** no AEMA 1.0.0. O analisador recebe
`reference_charge_mah` já calculado e sua incerteza padrão. O método de integração,
sinal, lacunas, offset, taxa e arquivo bruto devem ser preservados fora dessa tabela.

mAh representa carga; mA representa corrente; mWh representa energia; mW representa
potência. Para converter energia em carga, seria necessário conhecer a tensão pertinente
e o método temporal de conversão. Dividir mAh por horas produz uma corrente média na
janela declarada, não uma série de corrente instantânea nem prova de resolução de 1 µA.

## 2.6 Estatísticas atualmente calculadas

Em cada condição, `validation.analyze_trials` calcula:

```text
e_i = Q_Android,i − Q_referência,i
erro relativo_i [%] = 100 × e_i / Q_referência,i
viés descritivo = média(e_i)
erro absoluto médio = média(|e_i|)
s_erro = sqrt(Σ (e_i − média(e))² / (n − 1))
erro relativo médio = média(100 × e_i / Q_referência,i)
```

A média dos erros relativos não é necessariamente a razão entre as médias. O desvio-padrão
do erro descreve dispersão dos pares; não decompõe sozinho as contribuições de Android,
referência, sincronização e condição experimental.

O código rejeita valores não finitos, referências não positivas, cargas estimadas negativas,
incertezas negativas, IDs repetidos, janelas UTC inválidas e hashes com formato inválido.
Ele também rejeita mistura de dispositivo/build/instrumento/calibração dentro da mesma
condição. Esse controle sintático não verifica certificados nem recalcula hashes de brutos
externos a partir do ledger.

Ensaios excluídos continuam precisando de metadados válidos no formato atual. Uma condição
com menos de dois ensaios não excluídos é rejeitada. O resumo devolve a lista das incertezas
da referência, sem combiná-las com o desvio-padrão.

## 2.7 Incerteza e regra de decisão propostas

O [GUM/JCGM](https://www.bipm.org/en/committees/jc/jcgm/publications/) é a referência
metrológica para formular modelo, contribuições e combinação de incertezas. O orçamento
do estudo deverá considerar referência, calibração, integração, resolução, offset,
sincronização, deriva e efeitos relevantes do arranjo físico. Declare correlações e
coeficientes de sensibilidade; não some termos como se fossem independentes sem evidência.

Incerteza padrão e incerteza expandida têm papéis distintos. Se for reportada uma
incerteza expandida `U = k × u_c`, declare o modelo, o fator `k` e o significado da
abrangência. O AEMA 1.0.0 não implementa esse orçamento e não fornece `U` calibrada.

Antes de testar H1/H2, escolha procedimento inferencial e avaliação de pressupostos
compatíveis com dependência entre ensaios e distribuição dos erros. Intervalos de confiança,
testes de equivalência e gráficos de concordância são extensões possíveis, não funções
atuais. Correlação alta entre duas fontes não estabelece concordância entre elas.

## 2.8 Confiabilidade da coleta e overhead

Para estudar confiabilidade, use como denominador os horários **planejados** de uma série
definida, e não apenas os ZIPs encontrados. Telefone desligado ou processo impedido pode
resultar em ausência de arquivo. Classifique captura completa, parsing completo, parsing
incompatível, coleta frustrada e horário sem captura. Meça atraso e lacunas separadamente.
O AEMA registra dados de apoio, mas não implementa o relatório estatístico da série.

Para overhead, compare coleta ativada/desativada no mesmo workload e arranjo elétrico.
Alterne a ordem, repita e meça carga total com a referência. Controle aquecimento e efeitos
de tela, rede e inicialização de Python. A ausência de permissão de internet não implica
ausência de custo de CPU, armazenamento ou wake locks.

## 2.9 RAM, componentes e meta de 1 µA

Ensaios por componente devem declarar o recurso alterado e os efeitos acoplados.
A diferença A/B do total do telefone mede resposta incremental do sistema; só um rail
com escopo físico conhecido ou outra referência adequada permite uma interpretação
mais específica. Rótulos como `memory` não substituem o mapeamento do hardware.

Para 1 µA, escolha primeiro resolução ou incerteza, faixa, janela e fonte de corrente.
Depois caracterize sentinelas, atualização, ruído, offset e patamares conhecidos.
O [protocolo R-303](../roadmap/R-303-PROTOCOL.md) descreve essa avaliação condicional.

## 2.10 Congelamento, exclusões e publicação

O protocolo deve listar IDs por condição e motivos permitidos de exclusão antes dos ensaios.
`study.audit_study` exige `status: frozen` e compara esse plano ao ledger; isso não prova
que o arquivo foi congelado antes da coleta. Preserve uma evidência temporal independente,
como revisão assinada ou registro de aprovação, e registre toda emenda prospectiva.

Não remova ensaios porque seu resultado é inconveniente. Publique contagens de planejados,
excluídos e válidos, motivos, método, versões e limites. Para estudos por aplicação,
identidades e contextos de dispositivo precisam permanecer consistentes: UID não é um
identificador global de aplicativo, pode ser compartilhado e pode ser reutilizado.

Use os exports mínimos/pseudonimizados quando adequados, revisando risco de reidentificação.
No estado atual, qualquer conclusão elétrica permanece **não avaliada** até existirem
referência, janelas compatíveis e repetições reais suficientes.
