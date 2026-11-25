# 8. Ridge no app: implementação e simulação

**25/11/2026 · App/pacote/documentação 3.0.0 · dados exclusivamente sintéticos.**

A comparação anterior favoreceu Ridge no erro de consumo, sem ganho suficiente da
MLP para justificar sua adoção. Esta etapa implementa o preditor numérico no app,
treino no computador e demonstração offline. Não utiliza nem treina um LLM para prever.
O resultado é satisfatório como prova de integração; não aprova precisão pessoal.

## Pergunta e hipóteses desta etapa

É viável transformar capturas no formato real do projeto em atributos, treinar um
modelo pequeno e reproduzir suas seis saídas no Android sem pesos de linguagem?
Hipóteses técnicas: paridade host/Java dentro de 0,001 mAh, exclusão de janelas
inválidas e teste futuro separado do ajuste. A hipótese de prever o consumo real
com precisão e a de economizar bateria continuam sem confirmação.

## Método reproduzível

`experiments.forecast_simulation` usa semente 17 e a série sintética já versionada.
Gera 96 ZIPs acumulados com quatro componentes e dois UIDs (um compartilhado),
horários UTC de seis horas, relógio monotônico, boot, época de reset e estado de bateria.
Cada relatório passa pelo parser e exportador reais antes da verificação/importação.
Os dados não vêm do telefone do autor. Os hashes verificam integridade, não autenticidade.

O treino usa oito janelas anteriores válidas, última/quarta janela, médias, calendário
UTC e idades explícitas. Reservam-se 16 rótulos finais para teste e 16 para validação.
Normalização e escolha de alpha não consultam o teste. O modelo exportado é reajustado
em treino + validação; o teste não entra nos pesos. Contém 23 entradas e seis saídas.

No uso pessoal, cada par deve manter boot/reset, instalação/build, contadores
monotônicos e cadência entre 5,7 e 6,3 horas. Pares inválidos são descartados sem
atravessar a lacuna. Oito janelas válidas podem ocupar até 14 dias; o app verifica até
64 capturas recentes e exige que o último par também seja válido. Isso permite
reutilizar histórico após recarga/reboot, sem inventar intervalos ou zeros.

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python -m experiments.forecast_simulation --output dist/forecast-3.0.0
python -m pytest --cov=aema --cov-report=term-missing
android/gradlew.bat -p android assembleDebug assembleDebugAndroidTest testDebugUnitTest lintDebug
```

`ForecastFlowTest` lê `tests/fixtures/forecast-native-cases.json` e compara os mesmos
16 casos reservados com o motor Java. Testes instrumentados também exercitam a tela
de demonstração, preservação de modelo em importação inválida e recusa de sintéticos.
O teste de importação altera a marca sintética somente dentro de fixture isolada de
cache para verificar escrita atômica; não instala um modelo pessoal no app.

## Resultados medidos

| Medida | Resultado |
|---|---:|
| Capturas sintéticas verificadas | 96 |
| Exemplos após lags | 87 (55 treino / 16 validação / 16 teste) |
| Alpha selecionado | 100 |
| MAE teste Ridge, média entre seis alvos | 22,1647 mAh |
| MAE baseline quarta janela válida | 23,2052 mAh |
| Pesos + interceptos | 144 números; 576 bytes em FP32 teórico |
| JSON completo do modelo, indentado | 6.360 bytes |
| Paridade Android, 16 casos × seis saídas | erro máximo 5,6843 × 10⁻¹⁴ mAh |
| Testes Python | 248; cobertura 92,94% |
| Testes JVM do motor | 3 |
| Testes instrumentados executados | 5 |
| Lint Android | 0 erros; 35 avisos |
| APK release assinado, duas ABIs, sem pesos Qwen | 98.442.636 bytes (~93,88 MiB) |

O MAE agregado do Ridge foi cerca de 4,48% menor que o baseline nesta série. Uma série
e 16 exemplos não estabelecem superioridade estatística, precisão de ranking ou
generalização. Os seis alvos têm escalas diferentes; a média não representa erro
do total completo da bateria. Não se somam componentes e UIDs sobrepostos.

No emulador Android 15/API 35 x86_64, configurado com 6 GiB, 20 chamadas de aquecimento
e 1.000 repetições do mesmo vetor tiveram p50 **0,0587 ms** e p95 **1,406 ms**.
O tempo cobre só o produto numérico Java, excluindo coleta, inicialização Python,
leitura de ZIPs e preparação. A execução ocorreu durante trabalho de build no host;
não é benchmark de telefone nem medida de energia. O arquivo bruto registra o escopo.

Resultados estruturados: [forecast-3.0.0.json](resultados/forecast-3.0.0.json).
Os logs, ZIPs sintéticos e casos reproduzíveis acompanham o pacote de validação da release.

## Comportamento implementado

Após cada coleta salva, o app tenta preparar uma previsão. Sem modelo/histórico válido,
salva abstenção explícita. Previsões pessoais válidas preservam relatório e modelo em
ZIP prospectivo, com hashes dos dados usados, e tentam copiar para a pasta SAF. Há
rankings separados por eixo, sugestões locais e debug de motivos/tempos. Demonstração
e previsão pessoal usam arquivos separados; a demonstração não instala pesos pessoais.

O JSON de treino é limitado a 256 KiB, validado, associado à instalação/build e importado
atomicamente. Sem treino automático no telefone: reajustes exigem computador e nova
importação local. [Guia completo](../android/PREVISAO-LEVE.md).

## Limites e próximo estudo

Não foram usados dados reais nem executada a cadeia de previsão pessoal com histórico
real no Android. A preparação/treino com ZIPs foi testada no host; o emulador verificou
cálculo, importação, demonstração, parsing e falha de coleta. Arquivamento prospectivo e
cópia SAF de uma previsão pessoal precisam de aceite físico com histórico elegível.
Não houve ciclo real de seis horas, Shizuku no S25 Plus, referência elétrica, overhead,
economia comprovada, generalização entre aparelhos ou aprendizado contínuo no telefone.

Estados nos extremos não provam ausência de carga no meio da janela. O alvo é uma
estimativa futura BatteryStats, sujeita ao próprio modelo do Android; não é medição
elétrica nem previsão de porcentagem final. UIDs novos/ausentes podem impedir inferência.
Reinstalação/mudança de build exige novo vínculo/treino. Sem precisão real validada,
as sugestões não demonstram causalidade nem quantificam economia.

O motor é pequeno; o APK ainda contém Python/pandas para preservar todos os parsers
e o runtime nativo da leitura LLM opcional. Reduzir o APK exige outra etapa de arquitetura.
O próximo ensaio deve coletar dados pessoais, comparar baselines por eixo/UID com
avaliação temporal prospectiva e medir memória, latência completa e energia no aparelho.

## Fontes e evidências

- [Comparação Ridge/MLP do projeto](07-COMPARACAO-RIDGE-MLP.md), resultado anterior que fundamenta a escolha.
- [Revisão ultraleve](06-MODELOS-ULTRALEVES-E-REDES-NEURAIS.md) e [fontes primárias F29–F34](FONTES.md).
- Implementação: [preparação](../../src/aema/forecast.py), [treino](../../src/aema/forecast_training.py), [simulação](../../experiments/forecast_simulation.py).
- Verificação: [testes host](../../tests/unit/test_forecast.py) e [testes instrumentados](../../android/app/src/androidTest/java/org/aema/capture/ForecastFlowTest.java).

Esta etapa registra evidências locais; não atribui os números acima às fontes externas.
