# 08 — Roadmap técnico

Este plano é uma proposta de recuperação, não trabalho já realizado. A ordem privilegia validade científica antes de arquitetura, desempenho ou interface. Complexidade é relativa (`B` baixa, `M` média, `A` alta) e não representa prazo.

## Fase 0 — Decisão e preservação

| ID | Objetivo / problema resolvido | Escopo | Dependências | Comp. | Critério objetivo de conclusão | Testes/evidências |
|---|---|---|---|---|---|---|
| R-001 | Definir pergunta científica e impedir escopo contraditório | Documento de requisitos/TCC | Proprietário e orientador | M | Uma grandeza primária, população de dispositivos e hipótese aprovadas | Checklist de consistência dimensional |
| R-002 | Localizar o projeto Android e histórico que podem estar ausentes | Repositórios, backups, branches | Proprietário | B | Busca documentada; origem/cópia autenticada ou ausência aceita | Hashes e `git fsck/log` somente se houver repositório |
| R-003 | Preservar dados brutos e privacidade | `stats.*`, `packageUID.txt`, política de dados | R-001 | B | Cópia somente-leitura, hashes, classificação de dados e retenção | Verificação SHA-256; teste de restauração |
| R-004 | Definir “0,001 mA” metrologicamente | Protocolo | R-001 | M | Declaração se é resolução/incerteza, faixa e confiança | Revisão dimensional e orçamento preliminar de incerteza |

## Fase 1 — Reprodutibilidade da coleta

| ID | Objetivo / problema resolvido | Arquivos/módulos futuros | Dependências | Comp. | Critério objetivo de conclusão | Testes necessários |
|---|---|---|---|---|---|---|
| R-101 | Criar manifesto de ambiente/sessão | módulo de aquisição + schema | R-003 | M | Toda captura contém device/build/tempo/comandos/hashes/estado | Schema tests; campos ausentes falham |
| R-102 | Automatizar coleta não destrutiva | scripts ADB versionados | R-101 | M | Um comando gera artefatos e log sem reset implícito | Integração com device fake e físico |
| R-103 | Versionar dependências host | `pyproject.toml`/lock | Nenhuma | B | Instalação limpa reproduz parser | CI em versão Python declarada |
| R-104 | Anonimizar com reversibilidade controlada quando necessária | filtro de pacotes/UID | R-101 | M | Exportações de estudo não expõem pacotes pessoais | Testes de vazamento e mapeamento autorizado |

## Fase 2 — Correção do pipeline existente

| ID | Objetivo / problema resolvido | Arquivos envolvidos | Dependências | Comp. | Critério objetivo de conclusão | Testes necessários |
|---|---|---|---|---|---|---|
| R-201 | Corrigir schema check-in v9 | `csv_parser.py`, novo schema | R-003, R-103 | M | Contagens esperadas 819/491/65/1 na fixture atual; UID/tag preservados | Unit/golden por tag; versão desconhecida falha |
| R-202 | Corrigir semântica e unidade do bloco de potência | `txt_parser.py`, `translation.py` | R-001 | M | Nenhuma coluna de mAh usa sufixo `_time`; total e componentes preservados | Testes dimensionais contra linhas 37152+ |
| R-203 | Corrigir UIDs multiusuário/shared UID | `txt_parser.py`, `uid_parser.py` | R-201 | B | Fórmula AOSP e relação muitos-para-muitos | Casos `u0`, `u10`, UID de sistema e shared UID |
| R-204 | Integrar resultados num modelo canônico | novos modelos/exportador, `main.py` | R-201–203 | A | Uma sessão consultável com fonte/unidade/método/proveniência | Integridade referencial e reconciliação |
| R-205 | Falhar com diagnóstico em vez de silêncio | parsers/orquestração | R-201–204 | M | Relatório de linhas aceitas/rejeitadas e escrita atômica | Arquivos truncados, encoding/schema inválidos |

## Fase 3 — Validação científica das métricas

| ID | Objetivo / problema resolvido | Escopo | Dependências | Comp. | Critério objetivo de conclusão | Testes necessários |
|---|---|---|---|---|---|---|
| R-301 | Classificar cada campo por método | catálogo de métricas | R-204 | M | Todos têm unidade, fonte e classe medido/estimado/proxy | Revisão cruzada com AOSP e fixture |
| R-302 | Quantificar erro BatteryStats total | protocolo + analisador externo | R-004, R-101 | A | Erro, repetibilidade e incerteza publicados por condição | Ensaios repetidos, baseline, referência calibrada |
| R-303 | Avaliar 1 µA | gauge/externo | R-004, R-302 | A | LSB, ruído, offset e incerteza suportam ou rejeitam a meta | Zero, linearidade, deriva, taxa de atualização |
| R-304 | Validar atribuição por componente | workload e rails disponíveis | R-301–303 | A | Componentes aceitos têm método identificável e sinal acima da incerteza | A/B controlado, correlação temporal, repetição |
| R-305 | Decidir viabilidade de RAM | ODPM/rail/plataforma específica | R-304 | A | “RAM medida”, “proxy” ou “indisponível” decidido com evidência | Workloads de memória isolados e baseline |

## Fase 4 — Arquitetura, desempenho e produto

| ID | Objetivo / problema resolvido | Escopo | Dependências | Comp. | Critério objetivo de conclusão | Testes necessários |
|---|---|---|---|---|---|---|
| R-401 | Separar aquisição, parse, domínio, análise e exportação | módulos host/app conforme decisão | R-204, R-301 | M | Dependências unidirecionais e contratos tipados | Unit + integração + golden |
| R-402 | Garantir sincronização/overhead controlado | coletor, buffers, timestamps | R-302 | A | Overhead medido e dentro de limite definido | Perfetto/benchmarks e teste de perda |
| R-403 | Criar interface honesta | CLI/UI | R-301–305 | M | Toda métrica mostra unidade, método e incerteza/limite | Testes de apresentação e acessibilidade |
| R-404 | Exportar dataset analisável | formato tabular + metadados | R-401 | M | Schema versionado, sem dados órfãos, importável | Validação schema e round-trip |

## Fase 5 — TCC e demonstração

| ID | Objetivo / problema resolvido | Escopo | Dependências | Comp. | Critério objetivo de conclusão | Testes/evidências |
|---|---|---|---|---|---|---|
| R-501 | Executar estudo final | protocolo congelado | R-302–404 | A | Todas as execuções e exclusões seguem protocolo | Auditoria de logs, análise estatística |
| R-502 | Redigir resultados sem extrapolação | texto acadêmico | R-501 | M | Resultados distinguem medida/modelo/proxy e reportam incerteza | Revisão por tabela de rastreabilidade |
| R-503 | Preparar demonstração reproduzível | pacote/roteiro | R-501 | M | Execução limpa gera resultado esperado e fallback documentado | Ensaio em ambiente limpo e sem rede |

## Marcos de decisão

- Após R-001: escolher **um** eixo principal; RAM e corrente não devem permanecer metas vagas simultâneas.
- Após R-303: aceitar ou rejeitar formalmente 1 µA. Se rejeitado, redefinir uma meta compatível com o instrumento.
- Após R-305: decidir se RAM é objeto mensurável no hardware escolhido ou apenas workload/proxy.
- Somente depois de R-301–305 priorizar interface e otimização.
