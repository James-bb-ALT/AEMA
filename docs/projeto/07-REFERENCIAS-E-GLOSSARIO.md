# 7. Referências e glossário

[Índice](../README.md) · [Anterior](06-OPERACAO-VALIDACAO-E-LIMITES.md)

Fontes consultadas em **24/11/2026**. Esta é uma bibliografia técnica e metrológica inicial,
não uma revisão sistemática da literatura nem uma afirmação de originalidade científica.
Versões efetivamente usadas estão no build, no pacote e no capítulo de arquitetura.

## 7.1 Fontes primárias do próprio projeto

| Fonte | Uso documental |
|---|---|
| [`src/aema/`](../../src/aema) | Contratos e comportamento dos parsers, adaptadores, exports e analisadores |
| [`android/app/`](../../android/app) | Implementação Android, privilégios, ciclo de vida e armazenamento |
| [`pyproject.toml`](../../pyproject.toml) e [Gradle](../../android/app/build.gradle) | Versões, dependências, requisitos e configuração |
| [`tests/`](../../tests) e [testes Android](../../android/app/src/androidTest) | Casos executáveis, fixtures e alcance das verificações |
| [Release 1.0.0](https://github.com/James-bb-ALT/AEMA/releases/tag/v1.0.0) e [CI](https://github.com/James-bb-ALT/AEMA/actions/runs/45420908322) | Evidência publicada do software-base |
| [R-001](../roadmap/R-001-SCOPE.md) e [R-004](../roadmap/R-004-DECISION.md) | Escopo científico e indefinição da meta de corrente |
| [R-302](../roadmap/R-302-PROTOCOL.md), [R-303](../roadmap/R-303-PROTOCOL.md), [R-304](../roadmap/R-304-PROTOCOL.md), [R-305](../roadmap/R-305-DECISION.md) e [R-402](../roadmap/R-402-PROTOCOL.md) | Protocolos preliminares e limites de avaliações futuras |

## 7.2 Android, Shizuku e runtime

| Referência | Por que importa |
|---|---|
| Android Open Source Project. [Power profiles for Android](https://source.android.com/docs/core/power) | Fundamenta a distinção entre atividade/perfil do sistema e validação elétrica independente |
| Android Open Source Project. [Power stats HAL](https://source.android.com/docs/core/power/power-stats-hal) | Contextualiza contadores/rails e suporte dependente do dispositivo |
| Android Developers. [Schedule alarms](https://developer.android.com/develop/background-work/services/alarms) | Regras das APIs usadas no agendamento e suas permissões |
| Android Developers. [Foreground service types](https://developer.android.com/develop/background-work/services/fgs/service-types) | Contrato `dataSync` e restrições relevantes ao ciclo de vida |
| RikkaApps. [Shizuku API: developer guide](https://github.com/RikkaApps/Shizuku-API) | UserService, Binder, permissões e identidade shell/root |
| Chaquopy. [Gradle plugin](https://chaquo.com/chaquopy/doc/current/android.html) | Empacotamento do Python, source sets, ABIs e bibliotecas Android |

Essas referências justificam escolhas de integração. Elas não constituem evidência de
que o AEMA tenha sido ensaiado em todos os dispositivos ou de que seu overhead seja baixo.

## 7.3 Metrologia e planejamento científico

JCGM. **Evaluation of measurement data — Guide to the expression of uncertainty in
measurement**, JCGM 100:2008. [DOI oficial](https://doi.org/10.59161/JCGM100-2008E).
Acesso pelo [portal de publicações JCGM/BIPM](https://www.bipm.org/en/committees/jc/jcgm/publications/).
É referência para o orçamento de incerteza proposto, não uma funcionalidade já implementada.

O portal consultado também relaciona emenda de 2026 sobre não linearidade e outros
documentos da família GUM. O protocolo final deve identificar a edição e os documentos
aplicáveis ao modelo realmente adotado; a bibliografia não prova conformidade metrológica.

As fórmulas descritivas desta documentação correspondem ao código em `validation.py`.
A escolha de teste inferencial, procedimento de equivalência, cálculo amostral e nível
de abrangência ainda deve receber fundamentação específica no protocolo final. Esta
documentação não inventa um teste estatístico executado nem um resultado experimental.

## 7.4 Glossário

| Termo | Significado no AEMA |
|---|---|
| ADB | Interface host/dispositivo usada pelo coletor do computador |
| AIDL | Linguagem do contrato de comunicação Binder entre app e UserService |
| APK | Pacote instalável do app Android |
| AOSP | Implementação aberta de referência do Android |
| Atribuição | Valor associado pelo Android a UID/componente segundo suas regras; não necessariamente leitura física isolada |
| BatteryStats | Serviço/estatísticas Android que constituem a principal fonte dos relatórios |
| Binder | Mecanismo de comunicação entre processos Android |
| Build fingerprint | Identificação de software do aparelho; informação de contexto e potencial identificador |
| Catálogo | Inventário versionado de campos e sua interpretação |
| Carga elétrica | Grandeza integrada da corrente; expressa aqui em mAh |
| Dataset canônico | Representação comum com métrica, valor, unidade, método, origem e identidade contextual |
| Delta | Diferença entre observações; requer comparabilidade e não é calculado automaticamente entre snapshots |
| Erro assinado | Diferença Android menos referência para um par compatível |
| Evidência estimada/proxy | Classificação conservadora da natureza da informação; não uma medida de incerteza |
| Fixture | Entrada pequena e controlada para testar comportamento de software |
| Foreground service | Serviço com requisitos e visibilidade Android para trabalho em andamento |
| Hash SHA-256 | Resumo de bytes usado para conferir integridade, sem provar autoria |
| HMAC | Função autenticada por chave; usada aqui para derivar pseudônimos, não para assinar as capturas |
| Incerteza padrão | Parâmetro expresso na forma de desvio-padrão; a referência informa seu valor no ledger |
| Incerteza expandida | Incerteza combinada multiplicada por fator declarado; ainda não calculada pelo AEMA |
| Ledger | Tabela que registra ensaios, condições, referências e exclusões |
| Overhead | Efeito adicional da própria coleta sobre os recursos e grandezas observadas |
| PFD | ParcelFileDescriptor, descritor de arquivo transportado entre processos |
| Proveniência | Relação entre um valor e sua fonte, hash e linha quando disponível |
| Pseudonimização | Substituição de identidades explícitas por tokens mantendo possibilidade de correlação/reidentificação contextual |
| Rail | Caminho de alimentação cujo escopo físico precisa ser conhecido para interpretar contadores de energia |
| Repetibilidade | Dispersão observada sob condições de repetição declaradas; não é sinônimo de exatidão |
| Resolução | Menor variação distinguível sob condições definidas; casas decimais não bastam para estabelecê-la |
| SAF | Storage Access Framework, seletor/provedor Android para a pasta escolhida pelo usuário |
| Shared UID | UID associado a mais de um pacote; não autoriza repartir ou duplicar automaticamente a carga |
| Shizuku | Serviço autorizado que permite executar o UserService sob identidade shell/root disponível |
| Snapshot | Captura do estado/contadores em certo momento; pode conter acumulação anterior |
| Staging | Local temporário antes da publicação do resultado final |
| UTC | Referência civil de tempo usada em manifestos e ledger |
| UID | Identificador numérico Android, dependente de usuário/aparelho e contexto temporal |
| Wake lock | Mecanismo que mantém CPU ativa por período limitado; pode alterar o sistema observado |

## 7.5 Como atualizar esta documentação

Toda nova conclusão deve apontar a código, teste, dado ou fonte. Separe resultado de
proposta e indique o ambiente em que uma afirmação foi verificada. Ao atualizar software,
revise especialmente versões, schemas, catálogo, comandos, exemplos e a matriz de
compatibilidade. Preserve as auditorias antigas como histórico, com seu escopo temporal.
