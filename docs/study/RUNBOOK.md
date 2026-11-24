# Coleta e demonstracao

## App Android 1.0.0

Para coleta automática de seis horas com Shizuku, use o
[guia Android](../android/README.md). O app salva ZIPs locais com brutos e parsing,
sem reset de BatteryStats. A [política de privacidade](PRIVACY.md) inclui o comando
`aema pseudonymize` para estudos por aplicativo. Abaixo permanece o fluxo de coleta
e análise no computador; coleta ADB e coleta Shizuku não executam ensaios científicos.

## R-101/R-102: captura host-side

Com ADB e dispositivo autorizado, identificar o serial com `adb devices`. O comando abaixo
faz apenas leituras; nao reseta BatteryStats nem altera configuracao do aparelho:

```powershell
aema collect --serial SERIAL --output-root captures
```

Cada diretorio `captures/capture_<UTC>_<id>/` contem `stats.csv`, `stats.txt`,
`packageUID.txt`, `battery_state.txt` e `capture_manifest.json`. O manifesto registra
device/build, intervalo UTC, comandos, status e SHA-256. Verifique o manifesto e preserve
os arquivos brutos. Serial e nomes de pacotes podem identificar pessoas/dispositivos;
O compartilhamento deve seguir `PRIVACY.md`; os exports completos continuam privados.

A captura ADB e sequencial. Ela nao sincroniza automaticamente o inicio/fim de um workload
com instrumento externo e nao substitui o protocolo R-302. Consulte a matriz de
compatibilidade para os testes executados. A validação no dispositivo físico do usuário
e no formato produzido por seu fabricante continua necessária.

## R-501: estudo

O protocolo deve ser aprovado e congelado antes da primeira execucao. `planned_trials`
lista IDs por condicao e `allowed_exclusion_reasons` lista motivos definidos previamente.
Exemplo de estrutura, ainda nao e um protocolo aprovado:

```json
{
  "protocol_id": "id-a-definir",
  "status": "draft",
  "planned_trials": {"idle": ["trial-1", "trial-2"]},
  "allowed_exclusion_reasons": ["clock marker missing"]
}
```

Apos aprovacao, registrar `status: frozen` e preservar hash/versao antes de coletar.
Quando houver ensaios e referencia externa:

```powershell
python -m aema.study protocolo.json ensaios.csv
```

O comando compara IDs, condicoes e exclusoes com o plano e produz estatisticas descritivas.
Ele nao comprova que o protocolo foi congelado no tempo nem que a referencia foi calibrada;
essas evidencias exigem registros externos.

## R-502/R-503: relato e demonstracao

`RESULTS-TEMPLATE.md` e uma estrutura de redacao sem resultados. Para demonstrar apenas
o parser com fixtures locais e sem rede:

```powershell
aema demo --fixtures tests/fixtures --output-root demo-output
```

O demo exporta e reimporta o dataset e informa `scientific_validation: false`.
Uma demonstracao cientifica final depende de R-501 e dados reais.
