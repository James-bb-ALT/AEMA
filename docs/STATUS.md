# Estado atual — AEMA 1.0.0

Atualizado em 24 de novembro de 2026. Este arquivo descreve o estado atual; documentos
de auditoria/refatoração e o baseline do roadmap são registros históricos.

Documentação completa: [índice do manual](README.md), edição **1.0.1**, cobrindo objeto,
hipóteses propostas, métodos, arquitetura, código e contratos do software **1.0.0**.

## Implementado

- Núcleo Python compartilhado por host e Android: parsing check-in v9, relatório de
  energia, pacotes/UIDs, normalização, catálogo, modelos e dataset canônicos, verificação
  de importação, análise de ensaios, auditoria de protocolo e exportação.
- App Android com Shizuku UserService, comandos somente de leitura, captura imediata/manual
  e alarmes de seis horas, recuperação após boot/atualização e diagnóstico de falhas.
- ZIP por execução com brutos, UTC/relógio monotônico, hashes e tabelas; pasta local SAF
  escolhida pelo usuário e cópia privada. Sem permissão de internet ou backup automático.
- Export pseudonimizado por HMAC para estudos por aplicativo, com campos permitidos
  explicitamente e sem payloads identificáveis. Política operacional em `study/PRIVACY.md`.
- Instalação editável corrigida, cobertura mínima de 90%, lint e testes automatizados.
  README e instruções de compilação/uso atualizados; documentação passa a ser versionada.

## Limites que continuam reais

O hardware do usuário não estava conectado durante o desenvolvimento. Testes em emulador
comprovam integração de software, não compatibilidade com todos os fabricantes. Ver
`android/COMPATIBILITY.md` para a matriz de evidências e critérios de aceite físico.

Não houve ensaio de seis horas em tempo real, validação elétrica, referência calibrada,
estudo com repetição, medição de overhead ou comprovação de resolução/incerteza de 1 µA.
R-001/R-004 e R-302–305/R-402/R-501–502 mantêm os bloqueios científicos documentados.
R-104 tem implementação técnica de pseudonimização; aprovação de política/consentimento
e análise contextual de reidentificação pertencem ao responsável pelo estudo.

Os dumps são acumulados conforme os resets internos do Android. Não há cálculo automático
de deltas entre snapshots nem reset artificial para transformar capturas em janelas isoladas.
