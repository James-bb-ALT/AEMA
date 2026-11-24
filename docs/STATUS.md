# Estado atual — AEMA 2.0.0

Atualizado em 24 de novembro de 2026. Este arquivo descreve o estado atual; documentos
de auditoria/refatoração e o baseline do roadmap são registros históricos.

Documentação completa: [índice do manual](README.md), edição **2.0.0**, cobrindo objeto,
hipóteses propostas, métodos, arquitetura, código e contratos do software **2.0.0**.

O [estudo de IA](estudos/README.md) registra a meta confirmada de previsão das próximas
6 h, componentes/aplicativos, inferência offline e aparelhos com 6 GB ou mais, com
treinamento maior no computador. Inclui fontes e proposta de arquitetura híbrida.
A [leitura de snapshot por LLM e o debug](android/LLM-E-DEBUG.md) estão implementados em
2.0.0. Deltas/janelas de treino, previsão futura, adaptação pessoal e ensaios de economia
**não estão implementados**.

## Implementado

- Qwen3 GGUF por llama.cpp em CPU e processo privado, importação/preparação do modelo,
  seleção de fatos verificados, sugestões revisadas e cancelamento ao sair da tela.
- Debug local limitado, métricas de execução/memória e exportação explícita de JSON.
- Catálogo 1.2 com GPU, importação retrocompatível de datasets 1.1 e parsing da anotação
  `[energy consumption]` observada no Android 15. Formatos desconhecidos preservam os brutos.

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
