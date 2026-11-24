# 1. Objeto de estudo, objetivos e hipóteses

[Índice](../README.md) · [Próximo: metodologia](02-METODOLOGIA.md)

## 1.1 Problema e contexto

O Android mantém estatísticas de bateria, atividade e atribuição por UID. O BatteryStats
relaciona essas informações a estimativas de carga e componentes. É útil para investigar
comportamento do dispositivo, mas a presença de um número no relatório não estabelece
que ele corresponda a uma medição elétrica independente e calibrada. A documentação
[AOSP sobre perfis de potência](https://source.android.com/docs/core/power) explica a
relação entre estados de componentes, atividade e perfis usados pelo sistema.

O AEMA fornece a infraestrutura para coletar esses relatórios, preservar sua origem,
convertê-los em tabelas com significado explícito e preparar comparações reproduzíveis.
O software é um instrumento de apoio ao estudo; seu funcionamento não é, sozinho,
uma validação das estimativas do Android.

## 1.2 Objeto de estudo

**Objeto primário proposto:** a diferença entre a estimativa de carga elétrica total
do BatteryStats e a carga integrada por uma referência externa calibrada, em janelas
temporais compatíveis e condições controladas de uso de um dispositivo Android.

O campo primário candidato é `computed_drain_mah`, extraído de `Estimated power use (mAh)`.
Os campos `actual_drain_min_mah` e `actual_drain_max_mah` também são valores produzidos
pelo Android; o nome `actual` não os transforma na referência externa do experimento.

**Objeto de engenharia complementar:** a confiabilidade da cadeia de coleta, parsing,
preservação, exportação e reimportação, incluindo atraso de agendamento, falhas e
equivalência entre host e app. Esse objeto tem evidência de testes de software, distinta
da evidência necessária para avaliar carga física.

## 1.3 Perguntas de pesquisa

| ID | Pergunta | Estado |
|---|---|---|
| P1 | Qual é a diferença em mAh entre BatteryStats e referência externa na mesma janela? | Proposta; faltam ensaios e referência |
| P2 | O erro e sua dispersão mudam entre repouso e cargas de trabalho no mesmo aparelho? | Proposta; hipótese principal de R-001 |
| P3 | A coleta periódica preserva dados interpretáveis, com atrasos e falhas quantificados? | Integração testada; série contínua de seis horas pendente |
| P4 | Qual é o custo adicional da coleta sobre o consumo total e o comportamento do aparelho? | Proposta; overhead ainda não medido |
| P5 | Em hardware adequado, atribuições por componente e RAM correspondem a grandezas observáveis independentemente? | Exploratória e condicionada ao hardware |

O texto de P1/P2 consolida [R-001](../roadmap/R-001-SCOPE.md). Sua publicação como proposta
documental não constitui aprovação de protocolo pelo proprietário ou orientador.

## 1.4 Objetivo geral e objetivos específicos

O objetivo científico geral proposto é caracterizar o erro e a repetibilidade das
estimativas de carga total do Android em um escopo de dispositivos e condições definido
antes dos ensaios. O objetivo técnico já perseguido é oferecer dados verificáveis para
essa caracterização, sem converter estimativas em alegações de medição direta.

| Objetivo específico | Entrega correspondente | Situação |
|---|---|---|
| Coletar relatórios com baixo atrito operacional | App Shizuku, coleta manual e alarmes de seis horas; coletor ADB no host | Implementado; compatibilidade física pendente |
| Preservar brutos, origem e diagnósticos | ZIP, manifestos, SHA-256 e linhas de origem | Implementado; hash não prova autenticidade externa |
| Interpretar dados sem perder unidades ou identidades | Parsers, normalização, catálogo e modelo canônico | Implementado no formato suportado |
| Analisar ensaios pareados e rastrear exclusões | `validation.py` e `study.py` | Implementado e testado com dados sintéticos |
| Quantificar erro, incerteza e generalização | Ensaios controlados com referência externa | Proposto; não executado |

## 1.5 Hipóteses científicas propostas

### H1 — O erro depende da condição de uso

Hipótese candidata: no mesmo aparelho/build, o erro médio ou sua dispersão difere entre
repouso e uma carga de trabalho predefinida. Para a comparação do erro médio de duas
condições A/B, uma formulação possível é:

```text
H0: média do erro em A = média do erro em B
H1: média do erro em A ≠ média do erro em B
erro = carga estimada pelo Android − carga da referência
```

Essa formulação é uma proposta para orientar o planejamento. O analisador atual produz
estatísticas descritivas por condição; não calcula p-valores, intervalos de confiança ou
testes de igualdade de variâncias. A avaliação de dispersão exige critério próprio,
amostragem apropriada e definição anterior à observação dos resultados.

### H2 — A estimativa atende a uma margem de erro útil

Uma segunda hipótese candidata é que o erro fique dentro de uma margem prática `Δ`,
definida pelo objetivo do estudo. Isso exige especificar se a margem se aplica ao viés
médio, ao erro de cada ensaio ou a uma fração declarada dos ensaios. Essas proposições
não são intercambiáveis.

Se o alvo for equivalência do viés médio, uma formulação candidata é `H0: |μ_erro| ≥ Δ`
contra `H1: |μ_erro| < Δ`, com procedimento inferencial e abrangência previamente escolhidos.
Essa avaliação não está implementada. Não rejeitar uma hipótese de erro médio zero
também não demonstra equivalência ou exatidão suficiente.

### H3 — O coletor introduz efeito observável no sistema

Comparar o mesmo workload com e sem coleta permite investigar overhead. A hipótese
alternativa é que a execução do coletor altere a carga total, duração ou temperatura.
O protocolo deve estabelecer uma margem aceitável `Δ_coleta` e uma regra de decisão.
Não há resultado atual que permita chamar o custo de desprezível.

### Questões secundárias

Atribuições de CPU, tela, rádios e RAM podem ser examinadas em ensaios A/B, conforme
[R-304](../roadmap/R-304-PROTOCOL.md) e [R-305](../roadmap/R-305-DECISION.md). Um aumento
no total do aparelho não isola a carga de um componente. Uma atribuição zero para memória
não comprova que DRAM consuma zero.

A meta secundária `0,001 mA = 1 µA` não está definida como resolução ou incerteza.
Ela permanece **não avaliada**, conforme [R-004](../roadmap/R-004-DECISION.md). O parser
não lê uma série de corrente instantânea que permita avaliá-la.

## 1.6 Hipóteses de engenharia e evidência atual

| Proposição técnica | Como verificar | Alcance atual |
|---|---|---|
| As mesmas entradas geram dados canônicos equivalentes no host e no APK | Fixture comum, exportação e reimportação | Verificado para a fixture documentada, não para todos os formatos |
| Uma falha não é apresentada como parsing bem-sucedido | ZIP com `status` e `parse_status` separados | Verificado nos testes de falha |
| O alarme pode iniciar coleta fora da tela | Teste instrumentado de disparo antecipado | Verificado no emulador Android 15; não comprova seis horas contínuas |
| Pausar não remove capturas anteriores | Teste de preservação do ZIP | Verificado no cenário instrumentado |
| O export pseudonimizado remove os identificadores explícitos selecionados | Testes de campos permitidos e HMAC | Verificado para os contratos testados; não prova anonimato |

## 1.7 Variáveis, unidade experimental e limites de generalização

A unidade experimental do estudo controlado é **um ensaio pareado**, com uma condição,
um dispositivo/build, uma janela e uma referência. Uma linha canônica ou um pacote não
é uma repetição independente. Snapshots consecutivos de contadores acumulados podem
compartilhar informação e não devem ser tratados automaticamente como amostras independentes.

Variáveis explicativas propostas incluem workload, presença da coleta e, numa extensão
do desenho, dispositivo/build. Variáveis de resposta incluem erro em mAh, erro relativo,
dispersão do erro, atraso, proporção de capturas válidas e overhead. Temperatura, estado
de carga, tela, rede, alimentação, termal throttling e tarefas de fundo são controles ou
potenciais confundidores.

Os primeiros ensaios devem restringir conclusões ao aparelho/build e às condições
avaliadas. Um emulador testa integração de software, não representa a bateria de um
telefone físico nem sustenta generalização populacional.

## 1.8 Decisões abertas antes do estudo final

| Decisão | Informação a fixar | Consequência de permanecer aberta |
|---|---|---|
| Escopo e aprovação | Pergunta final, responsáveis e finalidade | Hipóteses continuam propostas |
| Hardware e referência | Aparelho/build, ponto de medição, instrumento e calibração | Sem comparação elétrica válida |
| Desenho e amostragem | Condições, duração, repetições, ordem e controles | Sem inferência ou repetibilidade sustentada |
| Aceite e exclusões | Margens, limites de atraso/perda e motivos de exclusão | Risco de escolher critérios após ver resultados |
| Governança | Consentimento aplicável, acesso, retenção e compartilhamento | Sem autorização contextual para dados reais de participantes |

O mínimo de duas observações válidas por condição, exigido pelo software, permite
calcular desvio-padrão amostral. Ele não é uma justificativa de tamanho de amostra científico.
