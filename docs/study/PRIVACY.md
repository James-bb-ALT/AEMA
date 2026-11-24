# Privacidade — AEMA 1.0.0

## Dados privados

Dumps e datasets completos podem identificar aplicativos, processos, wakelocks, UIDs,
modelo/build, horários e padrões de uso. Guarde ZIPs e brutos sob acesso restrito. O app
não tem permissão de internet, não lê o serial físico e não usa telemetria. O manifesto
identifica o aparelho por UUID de instalação. Android Backup e cópia automática entre
dispositivos estão desativados; a exportação explícita continua disponível.

Escolha uma pasta local no seletor Android. Um provedor de nuvem pode sincronizar arquivos
por conta própria. A pasta exportada não recebe criptografia adicional do AEMA. Compartilhe
ZIPs privados somente com o responsável pela análise, por canal apropriado ao estudo.

## Estudo de carga total

`aema study-summary --battery-report stats.txt --output-root study-outputs` exporta somente
carga total, unidade, método, limitações e hash do arquivo. O hash pode permitir correlação
com um dump conhecido; esse export não é garantia de anonimato.

## Estudo por UID/aplicativo

Crie uma chave aleatória de 32 bytes fora da pasta compartilhada:

```powershell
python -c "import secrets; from pathlib import Path; Path('C:/pasta-privada/estudo.key').write_bytes(secrets.token_bytes(32))"
aema pseudonymize --dataset caminho/parsed_dataset --key-file C:/pasta-privada/estudo.key --output estudo.json
```

O diretório da chave deve existir e ter acesso restrito ao responsável. O arquivo `.key`
é ignorado pelo Git, mas isso não protege contra leitores do sistema: use permissões do
sistema e armazenamento criptografado quando necessário.

O export usa HMAC-SHA-256 com domínios separados para UID e pacote. A mesma chave preserva
relações de UID compartilhado entre datasets; chaves diferentes isolam estudos. O arquivo
contém somente métricas numéricas e metadados de interpretação do catálogo, além de tokens.
Não inclui nomes originais, UIDs originais, payloads, mensagens de diagnóstico, caminhos,
hashes de origem ou identificadores de dispositivo. Um arquivo de saída existente é rejeitado.

Isso é **pseudonimização**, não anonimização. Padrões numéricos e métricas raras podem permitir
reidentificação. O responsável pode recuperar a correspondência recalculando os tokens a
partir dos identificadores nos brutos privados e da chave; o export não contém o mapa.

Antes de distribuir um estudo, registre responsável, destinatários, finalidade e prazo
de retenção. Mantenha chave e brutos separados do export; use uma chave por estudo e revise
os campos e padrões numéricos conforme o consentimento. Ao encerrar, elimine cópias de
chave, brutos e exports conforme a política aprovada. AEMA não apaga automaticamente os dados.

Os testes verificam ausência de identificadores em payloads/export, determinismo com a mesma
chave, isolamento entre chaves, preservação de shared UID, rejeição de chave curta e ausência
de sobrescrita. Isso não substitui a revisão contextual de reidentificação de um estudo real.
