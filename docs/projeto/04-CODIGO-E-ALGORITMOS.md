# 4. Código implementado e algoritmos

## Previsão Ridge adicionada em 3.0.0

`forecast.read_snapshot` reutiliza a verificação do dataset e exige metadados de boot,
reset, UTC/monotônico e estado de bateria. `delta` recusa pares incompatíveis e normaliza
deltas elegíveis para seis horas. `features` usa última/quarta janela válida, média de
oito, calendário UTC e idades explícitas; nunca usa o rótulo futuro. Janelas inválidas
não são atravessadas. `prepare_forecast` devolve atributos rastreáveis ou abstenção.

`forecast_training.train` ajusta Ridge NumPy com normalização somente do treino,
escolha de alpha por validação cronológica e teste final reservado. O JSON FP32 é
avaliado no Android por produto matricial Java limitado e validado. Ranking e sugestões
derivam apenas dos alvos previstos, com componentes e UIDs separados. Não é um modelo
elétrico físico, nem identifica causalidade de uma mudança de configuração.

Contratos, arquivos, comandos e caminhos: [previsão leve](../android/PREVISAO-LEVE.md).

[Índice](../README.md) · [Anterior](03-ARQUITETURA-E-TECNOLOGIAS.md) · [Próximo](05-DADOS-E-CONTRATOS.md)

Os caminhos abaixo são a referência de implementação. Esta documentação explica funções
e contratos; comentários/docstrings no código continuam úteis para detalhes locais.
O núcleo de parsing e análise descritiva é determinístico. A versão 2.0.1 acrescenta
seleção de fatos por LLM local e ações derivadas de regras revisadas, com validação posterior.
O AEMA extrai as estimativas de carga que o Android já apresenta. Ele não implementa
um modelo elétrico próprio para recalcular mAh a partir de tempos de CPU, tráfego ou RAM.

## Camada LLM e debug adicionada em 2.0.0

| Código | Responsabilidade |
|---|---|
| [`llm.py`](../../src/aema/llm.py) | Verifica ZIP/dataset/brutos, limita expansão, seleciona fatos por eixo e valida seleções do modelo. |
| [`AnalysisActivity.java`](../../android/app/src/main/java/org/aema/capture/AnalysisActivity.java) | Tela, importação, leitura, cancelamento e exportação. |
| [`AnalysisController.java`](../../android/app/src/main/java/org/aema/capture/AnalysisController.java) | Integridade, memória, preparação Python, serviço, prazo e persistência. |
| [`ModelStore.java`](../../android/app/src/main/java/org/aema/capture/ModelStore.java) | Cópia limitada, GGUF v3, hash e modelo privado. |
| [`AnalysisDebug.java`](../../android/app/src/main/java/org/aema/capture/AnalysisDebug.java) | Até 40 eventos, métricas sem prompts/pacotes e relatório JSON. |
| [`LlmService.java`](../../android/app/src/main/java/org/aema/capture/LlmService.java) | Processo `:llm`, geração serial, cancelamento e liberação. |
| [`LlmNative.java`](../../android/app/src/main/java/org/aema/capture/LlmNative.java) | JNI carregado somente no processo nativo. |
| [`aema_llm.cpp`](../../android/app/src/main/cpp/aema_llm.cpp) | Qwen3/CPU, contexto, gramática, deadline e métricas. |
| [`CMakeLists.txt`](../../android/app/src/main/cpp/CMakeLists.txt) | Upstream fixado por SHA, CPU e builds ARM64/x86_64. |

As interfaces `ILlmService` e `ILlmCallback`, em `android/app/src/main/aidl/`, transportam
somente prompt/gramática e resposta/código, sem arquivos grandes por Binder.
A camada não chama o coletor privilegiado. Ver [contratos e operação](../android/LLM-E-DEBUG.md).

## 4.1 Pontos de entrada e aquisição Python

| Módulo | Símbolos principais | Responsabilidade |
|---|---|---|
| [`__init__.py`](../../src/aema/__init__.py) | `__version__`, `__getattr__` | Expõe `PipelineInputs`, `PipelineResult` e `parse_inputs` com carregamento tardio |
| [`__main__.py`](../../src/aema/__main__.py) | Entrada do módulo | Permite `python -m aema` |
| [`cli.py`](../../src/aema/cli.py) | `build_parser`, `main` | Argumentos, comandos, JSON de resumo e códigos de saída |
| [`collector.py`](../../src/aema/collector.py) | `collect_session` | Executa ADB com serial explícito; captura sem reset e publica diretório de sessão |
| [`session.py`](../../src/aema/session.py) | `validate_capture_manifest` | Confere contrato, identidade, UTC, comandos, arquivos e hashes de sessão completa |
| [`acquisition.py`](../../src/aema/acquisition.py) | `describe_inputs` | Obtém hashes e caminhos das três entradas do pipeline |
| [`files.py`](../../src/aema/files.py) | `validate_input_file`, `detect_text_encoding`, `open_text`, `sha256_file` | Arquivo regular, BOM/encoding, leitura estrita e hash em blocos |
| [`errors.py`](../../src/aema/errors.py) | Hierarquia `AemaError` | Erros de domínio usados pelo pipeline, CLI e exportadores |

O coletor host verifica `get-state`, consulta três propriedades do aparelho e executa as
quatro leituras. stdout/stderr e retorno são registrados. Falha de coleta remove o staging
do coletor host e não publica sessão completa. Isso difere do app, que tenta preservar
uma captura frustrada como ZIP de diagnóstico.

## 4.2 Parsing, schemas e normalização

| Módulo | Símbolos principais | Algoritmo/contrato |
|---|---|---|
| [`parsers/__init__.py`](../../src/aema/parsers/__init__.py) | Pacote dos parsers | Organiza implementações por fonte |
| [`parsers/checkin.py`](../../src/aema/parsers/checkin.py) | `CheckinParser.parse_result`, `parse` | Leitura CSV, versão, seleção de tags e contagem de campos |
| [`parsers/battery_report.py`](../../src/aema/parsers/battery_report.py) | `BatteryReportParser.parse_result`, `parse` | Máquina de estados da seção de estimativa, regex de resumo/UID/detalhes |
| [`parsers/packages.py`](../../src/aema/parsers/packages.py) | `PackageUidParser.parse_result`, `parse` | Validação de `package:<nome> uid:<inteiro>` e preservação das relações |
| [`schemas.py`](../../src/aema/schemas.py) | `SUPPORTED_TAGS`, listas de campos e tipos de wakelock | Contrato explícito check-in v9 |
| [`normalization.py`](../../src/aema/normalization.py) | `parse_int`, `parse_float`, `normalize_android_uid`, `normalize_power_key`, `normalize_process_state_key` | Tipos, valores finitos, UID Android e nomes físicos de métricas |

### Check-in CSV

Cada linha começa com versão, UID, categoria e tag. O parser exige um registro `vers`
e rejeita versão diferente de 9 mesmo em modo leniente. Tags não suportadas são contadas,
sem serem interpretadas por um schema aproximado. Linhas suportadas malformadas interrompem
o modo estrito ou geram rejeição explícita no modo leniente.

| Tag | Conteúdo | Regra |
|---|---|---|
| `pr` | Processo, tempos e contagens | Sete campos de dados; nome e seis inteiros |
| `nt` | Rede | 22 campos de dados, com bytes, pacotes e tempo de atividade nas unidades do schema |
| `m` | Atividade global/diversa | 21 campos de dados definidos em `MISC_FIELDS` |
| `pwi` | Atribuição de carga por item | Cinco campos: item, estimativa, flag e duas atribuições adicionais |
| `wl` | Wakelocks | Nome seguido de grupos de seis campos; tipos `f`, `p`, `bp`, `w` únicos |

Uma versão válida não significa que toda tag esteja suportada. Um arquivo pode ser lido
com tags desconhecidas diagnosticadas. As contagens aceitas, rejeitadas e não suportadas
têm significados diferentes e permanecem no manifesto.

### Relatório TXT

O parser localiza `Estimated power use (mAh)`, procura o resumo de capacidade e lê as
atribuições globais e por UID. `Rated` e `Typical` são opcionais; sua ausência não vira
zero. Quando `actual drain` contém um único valor, os limites mínimo/máximo recebem
esse mesmo valor. O parser requer resumo e pelo menos um registro UID.

Valores assinados e notação científica são aceitos quando numericamente válidos.
`NaN`, infinito e overflow não são aceitos como números físicos. Estados `fg`, `bg`,
`fgs` e `cached` são nomeados explicitamente. Duração textual adjacente não é reinterpretada
como mAh. Linhas de detalhe têm sua proveniência por campo registrada quando disponível.

### Identidades e normalização

O formato `u<usuário>a<índice>` é convertido por:

```text
uid = usuário × 100000 + 10000 + índice
exemplo: u10a42 = 1010042
```

Isso reproduz o espaço de UID tratado pela implementação. Não cria identidade estável
de pessoa ou aplicativo entre aparelhos. As relações de pacote preservam UIDs compartilhados,
em vez de dividir automaticamente a carga entre os pacotes que usam o mesmo UID.

## 4.3 Domínio, adaptação e pipeline

| Módulo | Símbolos principais | Responsabilidade |
|---|---|---|
| [`models.py`](../../src/aema/models.py) | `Unit`, `MeasurementKind`, `Source`, `Provenance`, `CanonicalRecord`, `PackageUidRelation`, `ParseDiagnostics`, `ParseResult`, `PipelineInputs`, `PipelineResult` | Dados tipados, invariantes, serialização e tabelas de compatibilidade |
| [`catalog.py`](../../src/aema/catalog.py) | `CatalogEntry`, `CATALOG`, `CATALOG_BY_FIELD`, `assert_catalog_covers` | 145 campos catalogados, versões, unidade, método e evidência |
| [`adapters.py`](../../src/aema/adapters.py) | `adapt_checkin`, `adapt_battery_report`, `adapt_packages`, `adapt_pipeline`, `CanonicalResult`, `CanonicalDiagnostics` | Converte resultados de compatibilidade para registros e relações canônicos |
| [`pipeline.py`](../../src/aema/pipeline.py) | `run_pipeline`, alias `parse_inputs` | Coordena três parsers e origem das entradas, sem exportar arquivos |

Um registro canônico numérico é criado por métrica, não por linha original inteira.
O catálogo valida entidade, unidade, classe e método. Contextos como processo/wakelock
podem ficar em `payload` no dataset privado. UID zero só é tratado como global na combinação
explícita de categoria `l` e tag `m`; outros contextos preservam a ambiguidade.

O adaptador emite diagnósticos para métricas numéricas não catalogadas e problemas de
relação. O exportador canônico interrompe publicação se houver campo numérico desconhecido.
Uma relação de pacote é uma aresta de identidade e não carrega um valor de consumo.

```text
run_pipeline(entradas, strict):
    interpretar check-in, relatório TXT e relações de pacotes
    calcular hashes e caminhos das entradas
    retornar PipelineResult

export_canonical_result(resultado, destino):
    conferir catálogo e adaptar para registros/relações
    conferir versões, fontes e hashes de proveniência
    escrever artefatos em diretório temporário
    calcular hashes dos artefatos e escrever manifesto
    publicar diretório com nome novo
```

## 4.4 Exportação, importação e ponte Android

| Módulo | Símbolos principais | Responsabilidade |
|---|---|---|
| [`exporters.py`](../../src/aema/exporters.py) | `export_canonical_result`, `export_pipeline_result` | Publicação de CSVs/JSONL/catálogo/diagnósticos; o segundo mantém formato legado |
| [`dataset.py`](../../src/aema/dataset.py) | `load_dataset` | Verifica versões, nomes, lista/hashes de arquivos, tabelas obrigatórias, contagens e proveniência |
| [`mobile.py`](../../src/aema/mobile.py) | `publish_capture` | Completa manifesto, tenta parsing de captura completa e publica ZIP local |
| [`presentation.py`](../../src/aema/presentation.py) | `inspect_metrics` | Exibe metadados e limites das métricas do catálogo |
| [`demo.py`](../../src/aema/demo.py) | `run_demo` | Executa fixture, exporta e reimporta o dataset esperado sem rede |

Os exportadores usam staging e renomeação no mesmo destino para evitar mostrar um
diretório parcial como resultado final. Isso não inclui `fsync` ou garantia de persistência
contra perda súbita de energia. `load_dataset` verifica integridade interna; não autentica
o autor do manifesto nem comprova origem física ou calibração.

No app, coleta e parsing têm estados separados. `mobile.publish_capture` preserva os
brutos quando um erro de domínio impede o parsing. Um ZIP finalizado recebe nome UTC/UUID;
um erro de empacotamento mantém staging quando possível. Interrupção abrupta do processo
ou falta de armazenamento pode impedir a criação de qualquer ZIP final.

## 4.5 Análise de estudo e privacidade

| Módulo | API | O que faz e o que não faz |
|---|---|---|
| [`validation.py`](../../src/aema/validation.py) | `analyze_trials`, `main` | Valida ledger e calcula estatísticas descritivas; não integra corrente nem executa teste de hipótese |
| [`study.py`](../../src/aema/study.py) | `audit_study`, `main` | Confere plano congelado, IDs, condições e exclusões; não comprova anterioridade do congelamento |
| [`study_export.py`](../../src/aema/study_export.py) | `export_total_charge_summary` | Exporta total `computed_drain_mah`, interpretação, limites e hash; não exporta pacotes/UIDs |
| [`privacy.py`](../../src/aema/privacy.py) | `export_pseudonymous_study` | Valida dataset e exporta campos permitidos com HMAC; não garante anonimato |

O token é `HMAC-SHA-256(chave, tipo + ':' + identidade)`, com domínios distintos para
UID e pacote e chave de pelo menos 32 bytes. Payloads, diagnósticos textuais, hashes
de entrada, caminhos e identificadores de aparelho são omitidos. A mesma chave conserva
relações; chaves distintas isolam estudos. O arquivo existente não é sobrescrito.

Como o token de UID não inclui aparelho, a análise não deve fundir UIDs de aparelhos
distintos só por terem o mesmo token. Use separação de contexto e, quando adequado,
chaves distintas por aparelho/estudo. Reuso de UID ao longo do tempo também exige contexto.

## 4.6 Código Android

Os links abaixo apontam para `android/app/src/main/`.

| Arquivo | Métodos/contrato | Responsabilidade |
|---|---|---|
| [`MainActivity.java`](../../android/app/src/main/java/org/aema/capture/MainActivity.java) | Ciclo de Activity, `ready`, `copyAll`, `update` | Interface, autorizações, pasta SAF, ações e estado |
| [`IntervalPlan.java`](../../android/app/src/main/java/org/aema/capture/IntervalPlan.java) | `INTERVAL_MS`, `next` | Próximo slot na cadência de seis horas |
| [`Scheduler.java`](../../android/app/src/main/java/org/aema/capture/Scheduler.java) | `permitted`, `enable`, `arm`, `rearm`, `disable`, `state` | Alarmes e estado persistente |
| [`ScheduleReceiver.java`](../../android/app/src/main/java/org/aema/capture/ScheduleReceiver.java) | `onReceive` | Disparo de captura ou rearmamento após eventos |
| [`CaptureService.java`](../../android/app/src/main/java/org/aema/capture/CaptureService.java) | `onStartCommand`, `collect`, `onTimeout` | Foreground, coleta serial, manifesto, Python, cópia e avisos |
| [`ShellCollector.java`](../../android/app/src/main/java/org/aema/capture/ShellCollector.java) | `execute`, `destroy` | Allowlist de sete comandos, descritor, hashes, stdout/stderr e timeout |
| [`FolderExport.java`](../../android/app/src/main/java/org/aema/capture/FolderExport.java) | `copy`, `all` | Exportação/repetição para pasta SAF; mantém original privado |
| [`IShellCollector.aidl`](../../android/app/src/main/aidl/org/aema/capture/IShellCollector.aidl) | `execute`, `destroy` | IPC; código de transação especial para encerramento do UserService |
| [`AndroidManifest.xml`](../../android/app/src/main/AndroidManifest.xml) | Componentes e permissões | Activity, provider Shizuku protegido, receiver e serviço não públicos |
| [`res/`](../../android/app/src/main/res) | Tema, ícone e regras de extração | Apresentação e exclusões de backup/transferência automática |

Para `agora ≥ âncora`, o próximo horário é:

```text
próximo = âncora + (floor((agora − âncora) / intervalo) + 1) × intervalo
```

Se o relógio voltar a um instante anterior à âncora, `IntervalPlan.next` retorna a âncora.
O rearmamento após boot/atualização trata um horário vencido com uma tentativa posterior;
não gera cópias retroativas dos relatórios que não foram coletados.

## 4.7 Testes, custo de processamento e manutenção

`tests/unit/` verifica contratos e casos de erro; `tests/integration/` exercita o pipeline
e demo; `tests/regression/` fixa hashes e contagens de fixtures publicáveis. Os testes JVM
estão em `android/app/src/test/`; os instrumentados em `android/app/src/androidTest/`.

Os parsers percorrem linhas e retêm registros em memória. Adaptadores expandem linhas em
métricas; o número de registros canônicos pode ser muito maior que o de linhas originais.
Hashes são calculados por leitura de arquivos. Não há pipeline streaming completo, banco
de dados, paralelização de parsing ou limite global de memória garantido para dumps grandes.

Para adicionar uma tag/métrica, é necessário atualizar schema, normalização quando
pertinente, catálogo e testes; o mero reconhecimento de uma coluna não estabelece unidade
ou validade científica. Mude as versões dos contratos afetados quando sua semântica mudar.
Não use dumps privados como requisito oculto para testes em checkout limpo.
