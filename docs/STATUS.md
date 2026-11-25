# Estado atual — AEMA 3.0.0

Atualizado em 25 de novembro de 2026. App, pacote e documentação: **3.0.0**.

A [previsão leve](android/PREVISAO-LEVE.md) usa Ridge nativo offline para quatro
componentes e 1–12 UIDs. Inclui treino no computador, importação de JSON, verificação
de janelas, atualização após coleta, recomendações locais, arquivo prospectivo e debug.
O [estudo de implementação](estudos/08-IMPLEMENTACAO-E-SIMULACAO-RIDGE.md) registra
simulação sintética e paridade no emulador. Não há precisão pessoal validada.

O [experimento Ridge/MLP](estudos/07-COMPARACAO-RIDGE-MLP.md) fundamentou a escolha:
Ridge teve menor erro de consumo nos regimes sintéticos estudados. A demonstração
não instala modelo pessoal. O treino exige histórico real novo e transferência local.

A [leitura Qwen](android/LLM-E-DEBUG.md) continua opcional; o APK padrão não inclui
seus pesos. Python/pandas e as bibliotecas existentes continuam no aplicativo.

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

Os dumps são acumulados conforme os resets internos do Android. A previsão calcula deltas somente entre pares elegíveis; o app nunca reseta
os contadores nem reconstrói intervalos perdidos. Atribuição BatteryStats não é medida elétrica.
