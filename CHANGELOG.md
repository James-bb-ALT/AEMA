# Changelog

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
