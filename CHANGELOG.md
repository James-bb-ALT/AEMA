# Changelog

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
- README, privacidade, compatibilidade, estado e instruções atualizados e versionados.

Dependências do host e versões de schemas/catálogo não alterados são preservadas. O APK
usa suas próprias versões de bibliotecas Android, documentadas na matriz de compatibilidade.

## 0.1.0 — baseline anterior

Versão existente do pacote host-side. As melhorias locais anteriores de coleta ADB,
dataset canônico, catálogo e estudos foram preservadas e integradas nesta entrega.
Auditorias e protocolos anteriores permanecem como evidências históricas, não como
descrições do app 1.0.0.
