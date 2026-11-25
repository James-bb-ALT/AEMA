# Compatibilidade e evidências — AEMA 2.0.1

## Evidência adicionada em 2.0.0

Leitura Qwen3/llama.cpp em CPU executada de fato no Android 15 x86_64, em emulador com
6 GB: controlador, processo nativo e validação; cancelamento; preservação do modelo em
importações inválidas/interrompidas. Cinco testes JVM e 203 testes Python passaram,
com cobertura de 92,77%. As métricas de uma execução estão nas [notas](../releases/2.0.0.md).
Isso não prova consumo elétrico, p95 ou desempenho em um telefone físico de 6 GB.

Pipeline offline, captura com Shizuku parado e alarme com Shizuku real foram executados
novamente. A captura ativa revelou GPU e anotação de origem do consumo; catálogo 1.2
e parser receberam fixtures e regressões. Datasets 1.1 compatíveis continuam legíveis.
O quadro abaixo preserva o baseline da infraestrutura 1.0.0; a
[camada LLM/debug](LLM-E-DEBUG.md) tem requisitos e limites adicionais.

Data: 24 de novembro de 2026. Compatibilidade de software não é validação elétrica.

| Camada | Suporte declarado | Evidência |
|---|---|---|
| Host Python | 3.10+; pandas >=2.2,<3 | Suíte local em Python 3.13; CI definido para 3.10 e 3.13 |
| Check-in | Versão 9; pr, wl, nt, m, pwi | Fixtures e regressão; dump AOSP Android 15 processado |
| Resumo TXT | Resumo de capacidade e UID; Rated/Typical opcionais; actual drain único ou intervalo | Fixture histórica e fixture AOSP 15 adicionada após captura real em emulador |
| Pacotes | pm list packages -U; shared UID e multiusuário | Fixtures, testes de normalização e dump de 243 relações do emulador |
| APK | minSdk 26, target/compileSdk 35; ARM64 e x86_64 | APK universal compilado e assinado; execução x86_64 no Android 15 |
| Runtime Android | Python 3.13; pandas 2.1.3; numpy 1.26.2 | Teste instrumentado executa parsing, exportação e reimportação dentro do APK |
| Shizuku | API 13.1.5; UserService com identidade shell | Instalação e inicialização de Shizuku no emulador; comandos reais e ZIP na pasta SAF |
| Agendamento | Alarme exato, intervalo de 6 horas | Verificação via dumpsys alarm; teste instrumentado antecipa um disparo sem alterar o intervalo de produção |

## Critérios de teste

A fixture comum gera 88 registros canônicos e três relações pacote/UID no host e no APK.
A captura real inicial do emulador AOSP gerou 279 registros check-in, dois registros do
relatório de energia e 243 relações pacote/UID no host. O formato de resumo sem Rated e
Typical foi reproduzido em fixture mínima, sem publicar o dump completo do emulador.

O teste do alarme executa com o app fora da tela, verifica coleta/processamento pelo Shizuku,
arquivo novo e próximo horário com cadência de seis horas; também verifica que pausar mantém
o ZIP. A antecipação pertence somente ao teste, não é configuração exposta ao usuário.

O teste com Shizuku parado verifica publicação de um novo ZIP de diagnóstico, coleta
`failed`, parsing `not_attempted` e ausência de permissão de internet. A captura privada
é registrada antes de consultar o provedor da pasta, preservando seu estado mesmo se a
cópia externa falhar. O caminho de diagnóstico inicializa sem carregar pandas/numpy.

Verificações do host: 167 testes aprovados, cobertura 92,16% (mínimo 90%), Ruff lint e
formatação aprovados. Verificações Android:
build release assinado, lint sem erros, três testes JVM de cadência e testes instrumentados
de pipeline offline, alarme com Shizuku e indisponibilidade do Shizuku.

Não houve teste contínuo de seis horas em tempo real nem ensaio físico no aparelho do usuário.
Não se afirma compatibilidade universal com OEMs, versões posteriores, ARM32 ou páginas de
memória de 16 KiB. Os wheels nativos Android precisam de validação específica em 16 KiB.

## Aceite no aparelho físico

1. Registrar modelo, SDK/build e modo Shizuku; iniciar e autorizar. Escolher pasta local.
2. Fazer coleta manual; verificar ZIP completo, hashes e importação das tabelas no host.
3. Ativar coleta, bloquear a tela e verificar o novo ZIP após seis horas, observando atraso.
4. Reiniciar o aparelho, reiniciar Shizuku quando necessário e conferir a retomada; testar
   indisponibilidade do Shizuku e pasta sem permissão, preservando os arquivos anteriores.
5. Registrar o resultado na matriz do estudo sem expor identificadores/dumps privados no Git.

Formatos desconhecidos não são aceitos por heurística. Os brutos permanecem no ZIP com
diagnóstico, permitindo adicionar um schema e uma fixture específica posteriormente.
