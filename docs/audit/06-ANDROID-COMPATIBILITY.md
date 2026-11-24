# 06 — Compatibilidade Android

## Natureza da compatibilidade

Não há APK nem biblioteca Android neste diretório. Portanto não existem `minSdk`, `targetSdk`, permissões do Manifest, Activities, Services, receivers, JNI ou comportamento de lifecycle a validar. A compatibilidade é entre:

1. o host Windows/Python;
2. o formato de saída `dumpsys batterystats`/`pm`;
3. o dispositivo, build Android, OEM e hardware que geraram os dumps.

## Matriz observada

| Dependência | Evidência | Estado/limite |
|---|---|---|
| Python | `.venv` 3.13.9; global 3.10.6 | Código sintaticamente válido; versão não declarada |
| pandas | 2.3.0 na `.venv` | Única dependência externa importada |
| ADB | 35.0.2 no PATH | Disponível; nenhum dispositivo conectado em 2026-09-20 |
| BatteryStats check-in | Versão 9, parcel 36 | Parser incompatível com o schema observado |
| Build Android | `AP3A.240905.015.A2` | Exato no dump; API/modelo não capturados, logo não verificados |
| OEM/hardware | Muitos pacotes Samsung; capacity 4700/4755/4900 | Sugere ambiente Samsung, mas modelo não deve ser inferido |
| Power profile | `Can trust power_profile: true` | Habilita estimativas do framework; não é calibração do projeto |
| EnergyConsumer/PowerStats | “Not supported on this device” | Sem buckets medidos em microcoulombs nesta captura |

## Acesso e permissões

- A coleta indicada pelos comentários requer USB debugging/ADB e autorização do dispositivo. A documentação oficial usa `adb shell dumpsys batterystats` e recomenda desconectar o USB durante o workload para não alimentar o aparelho ([BatteryStats setup](https://developer.android.com/topic/performance/power/setup-battery-historian)).
- `pm list packages -U` via shell fornece o mapeamento usado. Aplicativos comuns enfrentam restrições de visibilidade de pacotes; este projeto não é um app e não declara `QUERY_ALL_PACKAGES`.
- Acesso direto a sysfs, serviços internos, BatteryStats privilegiado ou HAL não deve ser presumido para app comum. Nenhum contorno de segurança é proposto.
- `BatteryManager` público fornece corrente instantânea/média em µA em API 21+, porém suporte, resolução e atualização dependem do dispositivo. Ele não está implementado aqui ([BatteryManager](https://developer.android.com/reference/android/os/BatteryManager)).

## Variabilidade por versão e fabricante

O formato humano não é contrato estável para máquina. Tags e campos check-in evoluem; por isso o primeiro registro (`vers`) deve selecionar um schema conhecido, e versões desconhecidas devem falhar explicitamente. Extensões OEM presentes no dump (`CONNECTIVITY POWER SUMMARY`, temperaturas, eventos Samsung) não podem ser tratadas como universais.

PowerStats HAL existe a partir do Android 10 para dados cumulativos por rail/entidade quando o fabricante o implementa; pode retornar não suportado sem monitoramento de hardware. Leituras são acionadas em momentos relevantes, não uma série periódica garantida ([AOSP — Power stats HAL](https://source.android.com/docs/core/power/power-stats-hal)).

ODPM no Power Profiler expõe rails como CPU, GPU, memória, UFS e WLAN em hardware oficialmente suportado; mede no nível do dispositivo e exige correlação com eventos da aplicação. Disponibilidade por rail varia ([Power Profiler](https://developer.android.com/studio/profile/power-profiler)). Isso é uma alternativa de investigação, não substituição automática.

## Alternativas por objetivo

| Objetivo | Opção | Viabilidade/limite |
|---|---|---|
| Ranking aproximado por app | BatteryUsageStats/BatteryStats | Amplo via ADB; atribuição/modelo, não medição direta |
| Linha do tempo de atividade | Perfetto/System Trace | Boa correlação temporal; atividade não equivale a energia |
| Energia por trilho | ODPM/PowerStats | Forte quando suportado; dispositivo específico e geralmente nível do dispositivo |
| Corrente total | BatteryManager/fuel gauge | Fácil, mas qualidade depende do gauge; requer caracterização |
| Referência metrológica | Analisador externo | Melhor para validação; custo, montagem e sincronização |
| RAM/DRAM | Rail de memória quando exposto ou instrumento/plataforma específica | Raramente portátil; métricas de RAM ocupada são apenas proxies não energéticos |

## Dados mínimos a coletar numa próxima sessão

Serial pseudonimizado, fabricante/modelo, `ro.build.fingerprint`, SDK, kernel, nível de patch, capacidade/gauge, suporte a ODPM/PowerStats, lista de rails, timezone, estado de carga/plug, brilho, rádios, temperatura e hashes de todos os artefatos. Dados sensíveis devem ser protegidos e minimizados.
