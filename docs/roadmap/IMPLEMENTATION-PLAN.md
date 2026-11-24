# AEMA — baseline e plano de implementação

> Estado atual em 24/11/2026: ver [`../STATUS.md`](../STATUS.md). AEMA 1.0.0 inclui app
> Android/Shizuku, núcleo compartilhado e exportação pseudonimizada. As atualizações e a
> matriz abaixo são históricas; não representam o estado atual da entrega. Os bloqueios
> de validação científica permanecem conforme o estado atual.

Data: 20 de setembro de 2026.

## Atualização de implementação (30 de setembro de 2026)

Revisao das cinco pendencias apos o fim do roadmap:

- R-001: pergunta cientifica proposta em `R-001-SCOPE.md` para carga total em mAh;
  hipotese/populacao ainda dependem de aprovacao do proprietario/orientador.
- R-002: `R-002-RECOVERY.md` corrige o baseline antigo. O Git atual tem 12 commits
  desde 20/09/2026 e nao mostra projeto Android no historico local.
- R-004: `R-004-DECISION.md` registra 1 microampere como meta secundaria indefinida,
  sem afirmacao metrologica.
- R-104: `aema study-summary` publica somente carga total e metadados minimos; exports
  completos permanecem privados. Pseudonimizacao de estudos por UID continua pendente.
- R-302: sem referencia externa nem repeticoes, nenhum erro experimental foi estimado;
  o protocolo foi atualizado com o uso da exportacao minima.

Pausa apos esta revisao. `docs/` continua ignorado pelo Git.

Mais cinco itens avancados nesta rodada, em ordem de dependencia:

- R-101: `session.py` valida manifesto de captura com device/build, intervalo UTC,
  comandos, estado da bateria e hashes dos quatro arquivos.
- R-102: `aema collect --serial` executa leituras ADB sem reset e publica sessao
  atomicamente. Testado com ADB simulado; ensaio em dispositivo fisico pendente.
- R-501: `study.py` audita ledger de ensaios contra protocolo congelado e exclusoes
  predefinidas. O estudo final nao foi executado porque nao ha referencia/ensaios reais.
- R-502: `docs/study/RESULTS-TEMPLATE.md` estrutura resultados e matriz de evidencias,
  sem preencher resultados inexistentes.
- R-503: `aema demo` executa fixtures locais, exporta e reimporta o dataset sem rede.
  E demonstracao tecnica do parser; a demonstracao cientifica final aguarda R-501.

O guia de uso e limites esta em `docs/study/RUNBOOK.md`. Pausa apos esses cinco itens.

Avanco sequencial por cinco fases (R-305, R-401, R-402, R-403, R-404):

- R-305: decisao para a captura atual em `R-305-DECISION.md`: medicao de RAM indisponivel;
  `pwi,memory,0` nao comprova consumo zero. Generalizacao requer outro hardware/ensaio.
- R-401: no host, entrada de arquivos (`acquisition.py`), parsers, dominio/adaptadores,
  analise (`validation.py`) e exportacao estao separados. A coleta Android permanece R-102.
  Testes de regressao e golden preservam o comportamento.
- R-402: `R-402-PROTOCOL.md` define dominios de relogio, marcadores, perdas e comparacao
  com/sem coletor. Pendente de coletor e dispositivo para medir sincronizacao e overhead.
- R-403: a CLI aceita `aema inspect --metric <nome> [--source power|checkin]` e mostra
  unidade, metodo, classe de evidencia e ausencia de incerteza calibrada. A apresentacao
  cientifica final depende dos ensaios R-302–305.
- R-404: exportacao atomica inclui `canonical_records.csv` e `canonical_relations.csv`,
  alem dos JSONL e CSVs historicos. `load_dataset` verifica schema, versoes, hashes,
  contagens e proveniencia na importacao. UIDs sem pacote permanecem explicitos nos
  diagnosticos; nao sao descartados silenciosamente.

As fases 305 e 402 nao receberam resultado experimental; R-401, R-403 e R-404 possuem
implementacao tecnica host-side. Pausa apos R-404 conforme solicitado.

R-304 preparado, nao concluido: `docs/roadmap/R-304-PROTOCOL.md` define comparacoes A/B,
controles, evidencias de rail e categorias de conclusao por componente. A captura real tem
estimativas por componente, mas `EnergyConsumer` nao e suportado no dispositivo amostrado.
Nao ha ensaios repetidos, referencia externa ou resultados de R-302/R-303; portanto nenhuma
atribuicao por componente foi validada. O escopo primario permanece carga total em mAh.

R-303 preparado, nao concluido: `docs/roadmap/R-303-PROTOCOL.md` define os dados e ensaios
necessarios para avaliar 1 microampere, com criterios separados para resolucao e incerteza.
O objetivo principal atual continua carga total em mAh. Nao ha dados de corrente, fuel gauge
identificado, instrumento calibrado ou decisao R-004; R-302 tampouco possui resultados
experimentais. Nenhuma afirmacao de 1 microampere foi adicionada ao parser. A proxima acao
e fixar o significado da meta e o hardware antes de implementar aquisicao ou analisador de
corrente.

R-302 preparado, ainda pendente de ensaios: o objetivo principal foi definido como carga
total em mAh; a meta de 0,001 mA ainda nao tem definicao metrologica. Nao existem repeticoes
com referencia externa calibrada no repositorio. `docs/roadmap/R-302-PROTOCOL.md` descreve
coleta, pareamento e incerteza; `src/aema/validation.py` analisa uma tabela CSV de ensaios
pareados e rejeita metadados incompletos ou misturados. Nenhum erro experimental real,
repetibilidade por condicao ou incerteza final pode ser publicado ainda. Proxima acao para
R-302: executar a coleta conforme protocolo e trazer os arquivos brutos da referencia.

R-301 concluído no escopo do parser: catálogo v1.1 cobre as 145 colunas conhecidas das três
saídas, incluindo 40 métricas de energia presentes na captura real e ausentes na fixture curta.
Cada métrica numérica tem unidade, fonte, método de origem e classe `estimated` ou `proxy`;
nenhuma é declarada medição elétrica direta. O pipeline exporta `metric_catalog.json` e falha
sem publicar saída se surgir coluna não catalogada. A classificação foi confrontada com a
fixture, com os dados brutos do repositório e com AOSP:
<https://source.android.com/docs/core/power>,
<https://source.android.com/docs/core/power/values> e
<https://source.android.com/docs/core/power/power-stats-hal>.
O relatório não determina se um aparelho específico usa energia medida por HAL, perfil de
potência ou uma combinação em cada componente; isso requer proveniência do dispositivo e
validação experimental. R-302–305 continuam dependentes de R-001/R-004 e coleta apropriada.

R-205 concluído após R-204: `canonical_diagnostics.json` e `manifest.json` agora incluem o
mesmo relatório de diagnósticos por fonte, com linhas aceitas/rejeitadas, tags não suportadas,
avisos e problemas de relação UID/pacote. O modo estrito retorna código 2 para versão,
schema, entrada vazia e encoding inválidos sem publicar saída parcial; o modo leniente registra
as linhas rejeitadas. Validação: 99 testes passaram. Próxima fase principal: R-301 (validação
de método, unidade e proxy), dependente das decisões científicas R-001/R-004.

R-204 está integrado ao fluxo padrão da CLI: os três CSVs de compatibilidade são publicados
junto com `canonical_records.jsonl`, `canonical_relations.jsonl`,
`canonical_diagnostics.json` e manifesto versionado. O manifesto inclui caminhos e hashes das
entradas, contagens por entidade e hashes dos artefatos. Detalhes de energia do relatório TXT
guardam a linha de origem de cada métrica sem alterar os CSVs históricos. Os modelos,
adaptadores e exportador já existiam antes desta atualização; a integração e a proveniência
por campo completam o escopo técnico de R-204. A etapa R-204.6, que trata do contrato único de
diagnósticos, segue na fase R-205. A próxima fase principal é R-205; parar antes de iniciá-la.

Verificação atual: 95 testes passaram, Ruff lint e format passaram. O restante deste documento
registra o baseline histórico e o plano original, anteriores a esta atualização.

Este documento registra somente estado e plano. Nenhuma funcionalidade nova foi implementada
nesta execução. Documentos em `docs/audit/` permaneceram inalterados.

## Baseline verificado

### Estado do código

Implementação atual usa `src/aema/` com CLI, pipeline em memória, parsers check-in/TXT/pacotes,
normalização, modelos, schemas, validação de arquivos e exportação atômica. Raiz mantém apenas
fachadas de compatibilidade. Testes estão separados em unit, integration, regression e fixtures.

R-201, R-202 e R-203 estão concluídos na implementação atual. Evidência: schemas v9, contagens
de regressão, fórmulas AOSP para UID e testes correspondentes em `tests/`.

R-103 está concluído no escopo do parser: `pyproject.toml` declara Python >=3.10, dependências,
extras de desenvolvimento, pytest, cobertura e Ruff. Instalação isolada foi validada fora da
`.venv` de trabalho.

R-205 está parcialmente concluído: parsers já produzem diagnósticos, modo estrito/leniente e
exportação atômica. Falta consolidar diagnóstico e proveniência no modelo canônico de R-204.

R-204 está parcialmente concluído: `PipelineResult`, `ParseResult`, `ParseDiagnostics`, hashes
de entrada e manifesto já existem. Ainda não existe um dataset canônico único com contrato
uniforme de `source`, `unit`, `method`, `measurement_kind`, `uid` e proveniência por registro.

### Evidências executadas nesta revisão

| Verificação | Resultado |
|---|---|
| `python -m pytest` | 30 passed, 0 skipped, 0 failed |
| Ruff lint | `All checks passed!` |
| Ruff format | 30 files already formatted |
| Git | `fatal: not a git repository`; nenhum estado Git disponível |
| Preservação | backup de fontes e hashes das entradas registrados no relatório de refatoração |
| Pipeline baseline | 1.785 check-in, 174 power report, 791 pacotes |
| Contagens check-in | `pr=819`, `wl=491`, `nt=65`, `m=1`, `pwi=409` |

Não houve inicialização de Git, commit ou alteração de dados brutos, outputs históricos ou
auditoria.

## Matriz do roadmap

| ID | Estado | Evidência ou motivo |
|---|---|---|
| R-001 | pendente externo | pergunta científica, população e hipótese exigem decisão do proprietário/orientador |
| R-002 | parcial | projeto Android/histórico ausentes; ausência documentada, sem Git local |
| R-003 | concluído | hashes, backup recuperável e teste de regressão |
| R-004 | pendente externo | definição metrológica de 0,001 mA não pertence ao parser |
| R-101 | pendente | ainda não há manifesto de aquisição/device/build/comandos |
| R-102 | fora da execução atual | coleta ADB não é escopo implementado |
| R-103 | concluído | `pyproject.toml` e instalação isolada |
| R-104 | pendente | filtro de privacidade reversível não definido |
| R-201 | concluído | parser v9, schemas, golden/regression tests |
| R-202 | concluído | mAh, total UID, capacidade/drenagem e sinais preservados |
| R-203 | concluído | fórmula AOSP, UIDs compartilhados e testes |
| R-204 | próximo candidato; parcial | infraestrutura existe; contrato canônico ainda falta |
| R-205 | parcial | diagnósticos e atomicidade existem; falta contrato único |
| R-301–305 | pendentes | validação científica exige R-204 e decisões R-001/R-004 |
| R-401–404 | pendentes | dependem de domínio canônico e validação científica |
| R-501–503 | pendentes | dependem das fases anteriores |

## Próximo candidato: R-204

Dependências R-201, R-202 e R-203 estão satisfeitas por código, fixtures e regressão real.
R-204 pode começar sem bloqueio técnico. R-001 e R-004 são bloqueios de decisão para fixar
semântica científica final, mas não impedem desenhar um contrato técnico explicitamente
agnóstico de medição direta.

### Etapas ordenadas

#### R-204.1 — Inventariar campos canônicos

Mapear cada saída atual para `entity`, `metric`, `value`, `unit`, `measurement_kind`, `source`,
`method`, `uid`, `package_name`, `line_number` e `input_sha256`. Marcar campos sem equivalência.

Aceite: catálogo versionado cobre 100% dos campos exportados ou lista exceções justificadas.

Testes: teste de cobertura do catálogo contra colunas de três DataFrames.

#### R-204.2 — Definir schema e invariantes

Adicionar modelo canônico versionado, enums para unidade/método/classe e invariantes para UID,
origem, linha, valor e unidade. Preservar registros específicos por tag como payload auditável.

Aceite: schema rejeita registro sem origem ou unidade quando métrica numérica exigir unidade;
representa resumo global, UID e pacote sem colunas ambíguas.

Testes: schema unit tests, valores nulos, unidades inválidas, UID inválido e round-trip JSON/CSV.

#### R-204.3 — Adaptar parsers ao modelo canônico

Criar adaptadores puros `check-in`, `power report` e `package UID`. Manter parsers atuais como
camada de compatibilidade até golden tests passarem.

Aceite: uma sessão produz coleção canônica determinística; nenhuma linha, UID ou pacote se perde.

Testes: golden por fonte, contagens R-201, reconciliação de totais UID e preservação shared UID.

#### R-204.4 — Integrar proveniência e relações

Ligar cada registro a arquivo/hash/linha. Definir relação `package_name <-> uid` sem colapsar
duplicatas legítimas. Emitir diagnóstico de órfãos e duplicatas.

Aceite: toda linha exportada é rastreável à entrada; integridade referencial não cria UID órfão
silencioso.

Testes: arquivo truncado, hash alterado, pacote shared UID, UID sem pacote e pacote sem power.

#### R-204.5 — Exportar dataset canônico

Adicionar saída versionada e manifesto com schema version, contagens por entidade, hashes,
diagnósticos e limitações. Preservar três CSVs atuais durante migração.

Aceite: publicação continua atômica; importação do dataset em ambiente limpo reproduz registros
e metadados; falha não deixa diretório parcial.

Testes: integração entrada-parsing-normalização-exportação, round-trip e injeção de falha.

#### R-204.6 — Fechar R-205

Unificar erros, linhas aceitas/rejeitadas, tags não suportadas e avisos no relatório canônico.

Aceite: modo estrito falha com código não zero; modo leniente nunca silencia erro; manifesto
expõe diagnóstico completo.

Testes: encoding inválido, versão desconhecida, schema truncado, entrada vazia e CLI exit code.

## Próximos itens após R-204

1. R-205.6: fechar diagnóstico canônico e contrato de falha.
2. R-301: catálogo de método/unidade/proxy contra AOSP.
3. R-001/R-004: decisões científicas e metrológicas antes de qualquer interface ou estudo.

## Bloqueios reais

- Sem bloqueio técnico para iniciar R-204.
- Decisão do proprietário/orientador em R-001 bloqueia afirmações científicas finais.
- Definição metrológica de R-004 bloqueia qualquer conclusão sobre 0,001 mA.
- Ausência de Git impede diff/status histórico; não impede implementação, pois backup e hashes
  estão registrados.
