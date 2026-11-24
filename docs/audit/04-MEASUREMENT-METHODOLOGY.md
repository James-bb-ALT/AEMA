# 04 — Metodologia de medição

## Conclusão científica

O projeto não mede corrente. Ele pós-processa um snapshot cumulativo de BatteryStats. Na amostra, o próprio Android declara `Can trust power_profile: true` e apresenta “Estimated power use (mAh)”; os contadores `EnergyConsumer` em microcoulombs declaram “Not supported on this device” ([`stats.txt`, linhas 45698–45704](../../stats.txt)). Portanto, os números por componente são **estimativas/modelos e atribuições**, não leituras elétricas diretas de cada componente.

O Android explica que BatteryStats acumula tempos de estado e os combina com valores de `power_profile.xml` para aproximar consumo; o serviço não acompanha diretamente a corrente da bateria ([AOSP — Power profiles](https://source.android.com/docs/core/power)). Valores do perfil são correntes médias de laboratório multiplicadas por duração para produzir mAh ([AOSP — Power values](https://source.android.com/docs/core/power/values)).

## Período e origem da amostra

- Reset/início registrado: `2025-06-26 09:00:22` (`stats.txt`, início do histórico).
- Janela “since last charge”: 4 h 7 min 13,729 s.
- Saída capturada enquanto `currently on battery: false`; o período acumulado contém 91,7% do tempo em bateria.
- Build registrado pelo check-in: `AP3A.240905.015.A2`; versão check-in 9 e parcel 36 (`stats.csv`, linha 1). Modelo, serial, versão SDK e propriedades do fuel gauge não foram coletados.
- Frequência do **projeto**: uma única captura, sem loop de amostragem. Constantes internas como `external_stats_collection_rate_limit_ms=600000` não são frequência de coleta deste script.

## Rastreabilidade das métricas

| Métrica/grupo | Significado físico | Origem e API/arquivo | Unidade original | Transformação do projeto | Frequência/resolução | Precisão/exatidão demonstrada | Disponibilidade/permissões/erros |
|---|---|---|---|---|---|---|---|
| Capacidade e drain | Capacidade nominal/aprendida e carga drenada | `dumpsys batterystats`; `stats.txt` 37026+; `pws` em `stats.csv` 793 | mAh | Linha inteira guardada como string em `Battery_capacity`; computed/actual não separados | Snapshot acumulado; inteiros no resumo | Nenhuma calibração; computed 1377 mAh excede o limite superior “actual” 1363 mAh | Requer coleta ADB/shell; depende do fuel gauge e cálculo Android |
| Potência por componente/UID | Carga atribuída durante a janela | BatteryUsageStats/BatteryStats, bloco 37152+ e registros `pwi` 794–1202 | mAh | Regex remove unidade e converte para `float`; vários campos são chamados `*_time` | Snapshot; casas decimais variáveis até valores muito pequenos | Casas exibidas não provam resolução física; método mistura perfil, atividade e atribuição | Schema/versionamento do dump; valores zero podem significar sem suporte/sem atribuição |
| CPU | Tempo por UID/frequência e carga modelada | `cpu`, `ctf`, `gcf`, power profile; `stats.csv` | Tempos/contagens no check-in; mAh no `pwi` | Check-in perdido; apenas estimativa textual por UID preservada | Acumulado; pull em transições internas Android | Corrente média por bracket aparece no dump, não foi calibrada pelo projeto | Dependente de frequências/OEM; não mede cada núcleo eletricamente |
| Rede/Wi-Fi/modem | Bytes, pacotes, estados e carga atribuída | `nt`, controller activity e BatteryStats | bytes, pacotes, tempo; mAh no resumo | Check-in perdido; parte da estimativa por UID preservada | Acumulado e interno ao Android | Correlação/atribuição; `per_uid_modem_power_model=modem_activity_info_rx_tx` confirma modelo configurado | Dados e campos variam por modem, firmware e Android |
| Wakelocks/sensores/áudio/vídeo/câmera/GNSS/BT | Uso/atividade e carga estimada | BatteryStats por UID | tempo/contagem e mAh | Apenas mAh por UID; duração entre parênteses é descartada | Acumulado | Sem incerteza ou referência externa | Disponibilidade por componente e OEM; nomes/sensores podem ser específicos |
| Pacote↔UID | Identidade lógica, não energia | `pm list packages -U`, `packageUID.txt` | identificador | Conversão direta para inteiro | Snapshot | Exato para a captura, mas UIDs podem ser compartilhados | ADB/shell; pacote instalado após captura pode mudar mapeamento |
| Corrente no histórico | Corrente total da bateria em eventos | Campos `current=` no histórico bruto | Semântica/unidade não validada neste projeto | **Ignorada** | Eventos irregulares | Nenhuma | Não pode sustentar resultado sem metadados do gauge e fonte AOSP compatível |
| EnergyConsumer | Carga medida/acumulada por buckets | PowerStats/BatteryStats interno | microcoulombs | Nenhuma | Indisponível | O dump afirma “Not supported” | Dependente de HAL/OEM/hardware |

### Transformações e erros semânticos

Expressão implementada para UID textual:

```text
u0aN  -> 10000 + N
uUaN, U>0 -> (U + 1) * 10000 + N
```

A segunda linha é incorreta. AOSP compõe UID como `userId * PER_USER_RANGE + appId`, com `PER_USER_RANGE = 100000` ([`UserHandle.getUid`](https://android.googlesource.com/platform/frameworks/base/+/5301928/core/java/android/os/UserHandle.java)). A amostra contém apenas usuário 0, portanto o erro é latente, não observado nela. Correção proposta para fase futura: usar a fórmula oficial e testes multiusuário.

O parser também aplica `re.sub(r'[^0-9.]', '', val)`. Isso remove sinal, expoente, separador/unidade e pode transformar dados em outro número. Correção futura: parsers por schema que reconheçam explicitamente número e unidade, rejeitando o restante.

## Meta de 0,001 mA (1 µA)

### Conceitos que não podem ser confundidos

- **Resolução:** menor incremento distinguível/reportado.
- **Precisão/repetibilidade:** dispersão entre repetições iguais.
- **Exatidão:** proximidade do valor verdadeiro/rastreável.
- **Sensibilidade:** mudança da saída por mudança da grandeza de entrada.
- **Frequência de amostragem:** leituras por unidade de tempo; afeta fenômenos observáveis.
- **Incerteza:** intervalo quantificado associado ao resultado.
- **Precisão de apresentação:** quantidade de casas impressas; não melhora sensor ou método.

### Veredito

**Não demonstrada e não alcançada pela implementação atual.** Não existe leitura de `BatteryManager`, sysfs, HAL ou instrumento. O pipeline lida principalmente com mAh acumulados e imprime floats com casas variáveis. Um valor como `0.00000542 mAh` é resolução numérica de uma estimativa atribuída, não evidência de medição de corrente a 1 µA.

`BATTERY_PROPERTY_CURRENT_NOW` e `CURRENT_AVERAGE` são expressos em µA inteiros, mas unidade da API não garante resolução, precisão ou exatidão do fuel gauge ([BatteryManager](https://developer.android.com/reference/android/os/BatteryManager)). A documentação AOSP afirma que resolução e taxa de atualização dependem do hardware, resistor de sense e configuração do driver; offset domina correntes pequenas ([AOSP — Measure device power](https://source.android.com/docs/core/power/device)).

### O que seria necessário para validar 1 µA

1. Definir se 1 µA é resolução ou incerteza-alvo e em qual faixa de corrente.
2. Identificar fuel gauge, driver, LSB, intervalo de média, taxa de atualização e acesso permitido.
3. Usar referência externa calibrada com resolução e incerteza adequadas, ligação que não injete carga, e sincronização temporal.
4. Ensaiar zero/offset, linearidade, ruído, deriva térmica, repetibilidade e diferentes estados de carga.
5. Registrar média, desvio, intervalo de confiança, incerteza combinada e rastreabilidade.
6. Só então comparar leitura Android com referência. Nenhum resultado de calibração existe hoje.

## Corrente, carga, potência e energia

| Grandeza | Unidade | Relação idealizada |
|---|---|---|
| Corrente | A, mA, µA | `I = dQ/dt` |
| Carga | Ah, mAh, µAh, C | `Q = ∫ I dt`; `1 mAh = 3,6 C` |
| Potência | W, mW | `P = V × I` |
| Energia | Wh, mWh, J | `E = ∫ P dt`; `1 Wh = 3600 J` |

Converter mAh em mA exige uma janela temporal e hipótese sobre média; converter em energia exige tensão ao longo do tempo. O projeto não realiza essas conversões nem sincroniza tensão.

## Classificação por componente

| Componente | Evidência na amostra | Classificação da implementação |
|---|---|---|
| CPU/núcleos | 406 mAh global, tempos/frequências e brackets de corrente | **Estimativa**; atividade por núcleo/frequência é proxy, não trilho medido |
| GPU | Nenhum campo processado ou atribuição | **Indisponível** |
| RAM/memória | `pwi,memory,0`; nenhum contador de RAM processado | **Indisponível**; zero não comprova consumo zero |
| Armazenamento/UFS | Ausente | **Indisponível** |
| Tela | 641 mAh e tempos/brilho | **Estimativa** por modelo/atividade |
| Wi‑Fi | 16,5 mAh, estados/bytes/pacotes | **Estimativa + proxy indireto** |
| Bluetooth | 16,4 mAh e atividade | **Estimativa + proxy indireto** |
| Modem celular | 108 mAh; modelo RX/TX configurado | **Estimativa + proxy indireto** |
| Sensores/GNSS | 13,1/36,1 mAh e durações | **Estimativa + proxy indireto** |
| Câmera/áudio/vídeo | mAh e durações | **Estimativa** |
| Processos/apps | CPU, rede, wakelocks e mAh por UID | **Estimativa/atribuição**, não medição individual |
| Bateria total | faixa “actual drain” derivada pelo Android | **Estimativa de carga drenada**, não corrente direta do projeto |

ODPM/Power Profiler poderia oferecer trilhos de CPU, GPU, memória, UFS etc. em dispositivos compatíveis, mas mede no nível do dispositivo e a disponibilidade por trilho varia; a documentação limita o fluxo oficial do profiler a Pixel 6+ com suporte ([Android Power Profiler](https://developer.android.com/studio/profile/power-profiler)). O dispositivo desta captura declarou EnergyConsumer não suportado.
