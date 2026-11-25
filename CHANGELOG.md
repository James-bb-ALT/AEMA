# Changelog

## 2.0.1 — 2026-11-24

Correção incremental na seleção de evidências da leitura local.

- O Qwen agora seleciona somente IDs de evidência; ações/sugestões vêm de regras locais
  revisadas, associadas aos fatos positivos selecionados.
- Matriz sintética ampliada com 8 cenários e repetição no modelo real; veja o relatório
  de validação e as limitações registradas no caderno de estudos.
- Testes host, cenários nativos e documentação atualizados.

Notas: [`docs/releases/2.0.1.md`](docs/releases/2.0.1.md).

## 2.0.0 — 2026-11-24

Nova etapa de release: leitura local por LLM e debug.

- Qwen3 GGUF por llama.cpp fixado por revisão/hash; execução CPU em processo separado.
- Tela de leitura, modelo incluído opcional, importação atômica e verificação SHA-256.
- Fatos de captura verificada, limites de ZIP, prompt sem nomes de pacotes e saída
  restringida por gramática, com validação posterior de evidência e ações.
- Cancelamento, prazos, limite de tokens, relatório local e exportação de debug JSON.
- Debug de coleta/inferência com etapas, hashes, tokens, tempos e memória; sem prompts ou brutos.
- Licenças do runtime/modelo incluídas, builds com/sem pesos e testes nativos com modelo real.
- GPU e anotação `[energy consumption]` compatíveis com a captura real Android 15;
  catálogo 1.2 com importação retrocompatível de datasets 1.1.
- Versões do app/pacote/documentação sincronizadas; schemas de captura/registro/dataset
  e dependências existentes preservados.

Não inclui treinamento pessoal, previsão futura validada ou execução automática de sugestões.
Notas: [`docs/releases/2.0.0.md`](docs/releases/2.0.0.md).

## Documentação 1.0.2 — 2026-11-24

Melhoria incremental documental; app e pacote AEMA permanecem em 1.0.0.

- Estudo exploratório sobre LLMs, modelos numéricos e previsão de consumo em seis horas.
- Requisitos confirmados: inferência offline, meta de 6 GB, componentes e aplicativos,
  treinamento maior no computador por transferência local; S25 Plus/One UI 9 como caso inicial declarado.
- Comparação de sete candidatos, runtimes Android, pesos versus memória real e licenças.
- Proposta de rótulos, janelas sem vazamento, personalização, recomendações e testes físicos.
- Fontes primárias datadas, revisões de model cards e registro estruturado de 24 fontes.
- Índices e objeto de estudo ligados à nova linha, sem declarar IA ou validação elétrica implementadas.

Notas: [`docs/releases/docs-1.0.2.md`](docs/releases/docs-1.0.2.md).

## Documentação 1.0.1 — 2026-11-24

Melhoria incremental da documentação; software AEMA 1.0.0 preservado.

- Manual completo com objeto de estudo, objetivos e hipóteses candidatas, sem apresentá-las como aprovadas.
- Metodologia implementada e proposta, controles, fórmulas, incerteza, overhead e limites de generalização.
- Mapa de todos os módulos Python e componentes Android, tecnologias, versões, arquivos e contratos.
- Catálogo documental dos 145 campos gerado do catálogo executável 1.1.
- Instruções de reprodução, exemplos sintéticos de ledger/protocolo, referências e glossário.
- Navegação central e distinção explícita entre implementação, verificação, proposta e histórico.

Notas: [`docs/releases/docs-1.0.1.md`](docs/releases/docs-1.0.1.md).

## 1.0.0 — 2026-11-24

Nova etapa de release, conforme a classificação do projeto: app Android e evolução ampla.

- App Android offline com Shizuku, captura inicial/manual e novos ZIPs a cada seis horas.
- Núcleo Python do host incorporado diretamente por Chaquopy; sem parsers duplicados.
- Coleta somente de leitura, hashes, proveniência, relógios e preservação de brutos em falhas.
- Diagnóstico de coleta inicializa sem pandas; estado da cópia privada é registrado antes da exportação SAF.
- Pasta local selecionável pelo Android e reexportação das cópias privadas.
- Suporte ao resumo AOSP sem Rated/Typical e com um único valor de actual drain.
- Pseudonimização HMAC por estudo, exportação por lista de campos permitidos e testes de vazamento.
- Importação exige hashes de ambas as tabelas canônicas; testes de adulteração do manifesto.
- Instalação Python corrigida, cobertura acima de 90%, testes Android e CI.
- Regressão ampliada de energia usa fixture sintética publicável, sem depender de dumps privados no CI.
- README, privacidade, compatibilidade, estado e instruções atualizados e versionados.

Dependências do host e versões de schemas/catálogo não alterados são preservadas. O APK
usa suas próprias versões de bibliotecas Android, documentadas na matriz de compatibilidade.

## 0.1.0 — baseline anterior

Versão existente do pacote host-side. As melhorias locais anteriores de coleta ADB,
dataset canônico, catálogo e estudos foram preservadas e integradas nesta entrega.
Auditorias e protocolos anteriores permanecem como evidências históricas, não como
descrições do app 1.0.0.
