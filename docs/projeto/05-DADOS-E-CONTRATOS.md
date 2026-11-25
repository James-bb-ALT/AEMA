# 5. Dados, arquivos e contratos

## Contratos novos em 3.0.0

Modelo `aema_ridge_6h/1.0`, resultado `aema_forecast_result/1.0`, horizonte seis horas.
O modelo exige vínculo por hash de instalação/build, marcação sintética booleana,
quatro componentes fixos e 1–12 UIDs, normalizadores e pesos finitos. O atributo
`valid_lag1_lag4_mean8_calendar_age_utc_v1` tem `3 × saídas + 5` entradas.
O resultado identifica período, eixos separados, escopo do ranking, hash do modelo e
de cada captura usada; inclui abstenção explícita quando faltam dados elegíveis.

O manifesto de captura 1.0 recebe `forecast_boot_count` aditivo. Ausência mantém
compatibilidade dos parsers existentes, mas impede usar o par na previsão. Dataset,
registro canônico e catálogo não mudam. Contrato completo e privacidade dos novos
arquivos: [previsão leve](../android/PREVISAO-LEVE.md).

[Índice](../README.md) · [Anterior](04-CODIGO-E-ALGORITMOS.md) · [Próximo](06-OPERACAO-VALIDACAO-E-LIMITES.md)

## 5.1 Grandezas e interpretação

| Unidade | Significado | Limite de interpretação |
|---|---|---|
| `mAh` | Carga elétrica | Não é corrente instantânea, potência ou energia |
| `ms` / `us` | Duração em milissegundos/microssegundos | Não converter um tempo de atividade em carga sem modelo explícito |
| `bytes` / `packets` | Volume ou contagem de tráfego | Pode ser proxy de atividade; não mede energia de rádio |
| `count` | Contagem de eventos | Não informa custo elétrico individual do evento |

O catálogo diferencia capacidade reportada, faixa de drenagem reportada, estimativa ou
atribuição de carga, duração, contagem e quantidade. Na versão atual, nenhuma métrica é
declarada como medição elétrica direta independentemente validada. `estimated` e `proxy`
são classes de evidência do catálogo, não coeficientes de confiança ou calibração.

O campo `measurement_kind` textual dos CSVs de compatibilidade não é idêntico a todas as
classificações específicas do registro canônico. O adaptador e o catálogo estabelecem
a semântica de cada métrica, preservando o texto original como contexto quando aplicável.

## 5.2 Estrutura de uma captura Android

```text
aema_<UTC>_<id>.zip
├── stats.csv
├── stats.txt
├── packageUID.txt
├── battery_state.txt
├── model.txt
├── build.txt
├── sdk.txt
├── capture_manifest.json
└── parsed/                         # quando o parsing e a exportação passam
    └── parsed_<UTC>_<id>/
        ├── manifest.json
        ├── canonical_records.csv
        ├── canonical_records.jsonl
        ├── canonical_relations.csv
        ├── canonical_relations.jsonl
        ├── canonical_diagnostics.json
        ├── metric_catalog.json
        └── três CSVs de compatibilidade
```

Os três arquivos de propriedades também ficam no ZIP gerado pela implementação Android.
Em uma falha podem faltar saídas, existir arquivos parciais e não haver `parsed/`.
O manifesto descreve essa situação. O coletor ADB do host publica um diretório de captura
com os quatro arquivos de dados e manifesto, sem adotar esse mesmo empacotamento ZIP.

## 5.3 Manifesto de captura

O contrato de uma captura completa é validado por `session.validate_capture_manifest`.
Extensões Android fornecem dados de agendamento e execução sem mudar a versão básica.

| Campo | Papel |
|---|---|
| `schema_version` | Versão da captura: `1.0` |
| `session_id` | Identificador da execução |
| `status` | `complete` para coleta completa; `failed` para diagnóstico de coleta frustrada no app |
| `started_at_utc`, `ended_at_utc` | Intervalo da captura, não a janela inteira de acumulação do BatteryStats |
| `device` | Identificação de origem; `serial`, `model`, `build_fingerprint`, `sdk` |
| `commands` | Argumentos, timestamps, código de retorno, hash de stdout e stderr/erro |
| `file_sha256` | Hash dos quatro arquivos de captura presentes; conjunto completo exigido na sessão completa |
| `battery_state_file` | Proveniência do estado da bateria: `battery_state.txt` |
| `scheduled_at_utc`, `delay_ms` | Horário solicitado e atraso no app |
| `started_elapsed_realtime_ms`, `ended_elapsed_realtime_ms` | Relógio monotônico Android durante o boot; também registrado nos comandos |
| `transport` | `shizuku_user_service` nas capturas do app |
| `app_version` | Versão incorporada pelo bridge Android: `1.0.0` |
| `snapshot_semantics` | Aviso de acumulação desde reset, sem delta exclusivo de seis horas |
| `parse_status`, `parse_error` | Resultado do parsing e erro, quando houver |
| `parsed_directory` | Caminho relativo dentro do ZIP para o dataset válido, quando publicado |
| `scientific_validation` | `false`; não há referência externa validada nessa captura |

No Android, `device.serial_kind` informa `installation_uuid_not_hardware_serial`.
O campo legado `serial` contém um UUID da instalação. Ele muda após perda dos dados
da instalação e não deve ser interpretado como identidade física permanente do aparelho.

## 5.4 Estados e tratamento analítico

| Coleta | Parsing | Significado | Uso permitido |
|---|---|---|---|
| `complete` | `complete` | Brutos e dataset publicados | Inspeção/importação, respeitando diagnósticos e limites científicos |
| `complete` | `unsupported_or_invalid` | Brutos preservados, mas contrato ou parsing/exportação não passou | Investigar formato; não tratar como dataset canônico válido |
| `failed` | `not_attempted` | Coleta frustrada ou incompleta | Contabilizar falha e analisar diagnóstico |
| Sem ZIP | Sem estado final | Pode ter ocorrido desligamento, bloqueio, falta de espaço ou interrupção | Investigar lacuna usando o plano e evidências externas |

`unsupported_or_invalid` é uma classificação ampla do bridge, incluindo erros de domínio
durante validação/parsing/exportação; não é um diagnóstico exclusivo de versão Android.
Um ZIP de diagnóstico existir não significa que os quatro arquivos estejam completos.

## 5.5 Artefatos do dataset

| Arquivo | Conteúdo |
|---|---|
| `stats_checkin_parsed.csv` | Linhas suportadas do check-in, com colunas específicas por tag |
| `stats_power_estimates_parsed.csv` | Resumo global e registros UID do relatório TXT |
| `package_uid_parsed.csv` | Relações de pacotes e UIDs |
| `canonical_records.csv` / `.jsonl` | Uma linha/objeto por métrica numérica normalizada |
| `canonical_relations.csv` / `.jsonl` | Relações pacote/UID com proveniência |
| `canonical_diagnostics.json` | Diagnósticos consolidados por fonte e relações |
| `metric_catalog.json` | Catálogo versionado e interpretação das métricas |
| `manifest.json` | Contratos, caminhos/hashes de entrada, hashes de artefatos, contagens e limites |

### Registro canônico

| Campo | Regra/semântica |
|---|---|
| `schema_version` | `1.0` |
| `entity` | Entidade compatível com o catálogo, como `checkin_record` ou `power_record` |
| `metric` | Nome conhecido do catálogo; não um rótulo arbitrário |
| `value` | Número finito, sem booleanos; o contrato de parsing pode preservar valores assinados |
| `unit` | Unidade correspondente à métrica, como `mAh` |
| `measurement_kind` | Classe semântica compatível com a métrica |
| `source` | `checkin`, `power` ou `packages`, conforme o contrato |
| `method` | Método declarado no catálogo, como `batterystats_power_report` |
| `uid`, `package_name` | Identidades opcionais; uma métrica UID não é automaticamente atribuída a um único pacote |
| `input_sha256`, `line_number` | Hash e linha de origem quando disponíveis; no modelo, compõem `Provenance` |
| `payload` | Contexto privado da linha, como processo, wakelock, categoria e texto de UID |

No CSV, `value`, `uid`, `line_number` e `payload` têm serialização que o importador
reconstrói com JSON. Em JSONL, esses tipos ficam explícitos. A proveniência normaliza
o hash para minúsculas no modelo; manifestos e hashes de artefatos são emitidos em
maiúsculas pelos exportadores atuais. Use a API de importação para respeitar o contrato.

`PackageUidRelation` contém pacote, UID e proveniência, sem carga atribuída. Se dois
pacotes compartilham o mesmo UID, uma junção simples que repita o total UID para ambos
pode duplicar o valor no somatório. O AEMA não inventa uma divisão proporcional entre eles.

## 5.6 Manifesto e verificação do dataset

O manifesto usa `manifest_format_version: 2.0`, `canonical_schema_version: 1.0` e
`catalog_version: 1.2`. Há 147 entradas de campos no catálogo; nem todas são métricas
numéricas, pois também existem identificação e metadados.
O [inventário completo dos 147 campos](../CATALOGO-COMPLETO.md) foi gerado do catálogo
executável, agrupando fonte, unidade, classificação e tipo de medição.

`load_dataset` confere versões exatas suportadas, igualdade entre lista de arquivos e
hashes, presença das duas tabelas canônicas CSV, nomes válidos de artefatos, SHA-256,
contagens totais e hashes de proveniência dos registros/relações. Depois reconstrói
os modelos tipados. A leitura canônica é feita dos CSVs; os outros artefatos declarados
também têm hashes conferidos.

Essas checagens não demonstram que os brutos externos foram produzidos no aparelho
declarado. Caminhos de entrada podem apontar a staging já removido e devem ser tratados
como metadados históricos, não como arquivos que sempre existirão no computador de destino.
O manifesto canônico não registra automaticamente toda a cadeia de versões de dependências;
preserve também a release e o ambiente de análise.

## 5.7 Diagnósticos e valores ausentes

`ParseDiagnostics` distingue linhas totais, registros interpretados, linhas vazias,
tags não suportadas, linhas aceitas, linhas rejeitadas e avisos. O diagnóstico canônico
consolida fontes, campos numéricos desconhecidos e problemas de relação. Não converta
linhas rejeitadas ou campos ausentes em zeros.

Zero numérico, campo ausente, componente não suportado e linha rejeitada são situações
distintas. Uma capacidade `Rated` omitida não significa capacidade nominal zero. Um
`pwi,memory,0` não é uma medição elétrica de consumo físico nulo de RAM.

## 5.8 Ledger de ensaios e protocolo

Uma linha representa um ensaio pareado, e não um snapshot arbitrário.

| Grupo | Colunas obrigatórias |
|---|---|
| Identidade | `trial_id`, `condition`, `device_id`, `build_id` |
| Referência | `instrument_id`, `calibration_id`, `reference_standard_uncertainty_mah` |
| Janela | `window_start_utc`, `window_end_utc`, `clock_offset_ms` |
| Comparação | `estimated_charge_mah`, `reference_charge_mah` |
| Rastreabilidade | `battery_stats_sha256`, `reference_sha256` |
| Exclusão | `exclusion_reason`, vazio quando o ensaio não foi excluído |

O protocolo JSON exige `protocol_id`, `status: frozen`, `planned_trials` como mapa
condição/lista de IDs, e `allowed_exclusion_reasons` como lista de textos. A auditoria
exige correspondência exata de IDs e condições com o ledger. O campo `clock_offset_ms`
é validado numericamente, mas o analisador não aplica automaticamente correção temporal
nem verifica um limite máximo de desalinhamento. Esses critérios pertencem ao protocolo.

Os [exemplos sintéticos](../examples/README.md) demonstram esses formatos sem representar
participantes, calibração ou resultados reais.

## 5.9 Exportações para estudo e privacidade

`study_summary.json` expõe o total candidato e seus limites, mas mantém o hash da fonte,
que pode permitir correlação com um dump conhecido. O export de `pseudonymize` usa
`schema_version: aema-pseudonymous-study-1`, métricas e relações com tokens HMAC.

Nenhum dos dois formatos é uma licença automática para compartilhamento. O export
pseudonimizado não contém brutos/payloads, mas padrões numéricos ainda podem identificar
uso ou participante. A política, retenção, acesso à chave e contexto de dispositivo
estão descritos em [Privacidade](../study/PRIVACY.md).
