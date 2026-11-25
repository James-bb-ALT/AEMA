# AEMA Android 2.0.1

Para a nova leitura local por IA, modelos e diagnóstico, veja [LLM e debug](LLM-E-DEBUG.md).

## Operação no telefone

Instale o APK assinado. Inicie Shizuku e autorize AEMA. Escolha uma pasta local pelo
seletor Android; `Documentos/AEMA` é uma opção. Autorize alarmes exatos e notificações.
Toque em **Ativar coleta a cada 6 horas**. Isso agenda a próxima captura e inicia a primeira.
**Coletar agora** não desloca a cadência automática. **Pausar** cancela o próximo alarme,
preservando arquivos; uma captura que já começou termina normalmente.

O app executa somente `getprop` para modelo/build/SDK, `dumpsys batterystats --checkin`,
`dumpsys batterystats`, `pm list packages -U` e `dumpsys battery` por Shizuku UserService.
Não usa o método obsoleto `Shizuku.newProcess`, não abre shell interativo e não aceita
comandos arbitrários. Saídas grandes passam por descritores de arquivo, fora do limite
de tamanho de transações Binder. Cada comando tem timeout de 120 segundos.

O coletor usa um UUID de instalação como identificador, marcado como tal no manifesto.
Ele não lê o serial físico. Coletas manuais e automáticas são serializadas pelo serviço.
O app não reseta os contadores e não altera configurações de bateria do aparelho.

## Arquivos e transferência

Cada captura produz um ZIP único. Ele contém os quatro arquivos brutos e
`capture_manifest.json`; quando o parsing passa, `parsed/parsed_<UTC>_<id>/` contém
as mesmas tabelas e manifestos do host. `status` descreve a coleta; `parse_status`
descreve o processamento. Nunca trate uma coleta incompleta como dataset válido.

Os ZIPs são mantidos em `files/captures/`, sob o armazenamento privado do app. O app
copia cada ZIP finalizado para a pasta SAF escolhida, primeiro com nome temporário e
depois renomeando. Falha de permissão/provedor mantém a cópia privada e mostra aviso.
**Copiar todos os ZIPs** permite repetir a transferência. Sem espaço, os dados já salvos
não são apagados automaticamente; o erro é exibido. Não existe política de retenção
automática nesta versão. Transfira os dados regularmente e acompanhe o armazenamento.

A desinstalação apaga os dados privados. ZIPs já copiados para a pasta escolhida continuam
lá. Pastas de nuvem selecionadas pelo usuário podem sincronizar independentemente do app.
Android Backup e transferência automática de dados do app estão desativados.

## Agendamento

`AlarmManager.setExactAndAllowWhileIdle` dispara alarmes com cadência de seis horas.
O trabalho roda em foreground service `dataSync` com notificação e wake lock limitado.
Depois do boot/atualização, apenas o alarme é rearmado; não se inicia `dataSync` diretamente
do broadcast de boot. Se um horário foi perdido, agenda-se uma tentativa em dois minutos;
depois retorna à cadência original. Horários perdidos não são reconstruídos.

O sistema e o fabricante podem impedir execução. Forçar parada cancela a automação até
abrir o app novamente. Revogar alarmes exatos remove os alarmes no Android. Inicie o
Shizuku novamente após reboot quando ele roda via ADB. O manifesto guarda UTC previsto,
UTC efetivo, atraso e relógios monotônicos, sem prometer sincronismo com instrumento externo.

## Compilar

Requisitos: JDK 21, Python 3.13, Android SDK com plataforma 35 e build-tools 36.0.0,
NDK 27.2.12479018 e CMake 3.22.1.
Configure `ANDROID_HOME` ou `android/local.properties`. Não versione caminhos pessoais.

```powershell
android\gradlew.bat -p android assembleDebug testDebugUnitTest lintDebug
android\gradlew.bat -p android connectedDebugAndroidTest
```

No Linux, use `bash android/gradlew`. Chaquopy inclui diretamente `../../src`; não há
cópia divergente dos parsers. O APK contém os módulos de análise de ensaios, auditoria,
catálogo, importação e privacidade. A interface expõe coleta, parsing e leitura por LLM;
a análise científica de ensaios permanece no computador.

Para release assinada, defina `AEMA_KEYSTORE` e `AEMA_STORE_PASSWORD`, alias `aema`, e rode
`assembleRelease`. Nenhuma chave ou senha entra no Git. A chave local desta instalação
fica em `%USERPROFILE%\.aema\release.jks`, com configuração privada em `signing.json`.
Faça backup privado dessa chave: atualizações instaláveis precisam da mesma assinatura.

## Referências de implementação

- [Shizuku UserService e permissões](https://github.com/RikkaApps/Shizuku-API)
- [Chaquopy: integração Python/Android](https://chaquo.com/chaquopy/doc/current/android.html)
- [Android: alarmes](https://developer.android.com/develop/background-work/services/alarms)
- [Android: foreground services](https://developer.android.com/develop/background-work/services/fgs/service-types)
