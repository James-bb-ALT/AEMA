# AEMA 1.0.0

Coleta e análise offline de exportações Android BatteryStats. O app Android usa Shizuku
para salvar um novo ZIP a cada seis horas. O computador e o app executam os mesmos
algoritmos Python de parsing, normalização, catálogo, diagnóstico e exportação canônica.

Os valores em mAh são estimativas/atribuições do Android. Não são medições diretas de
corrente, potência ou energia. A validação com referência elétrica externa continua pendente.

## App Android

Requisitos: Android 8 ou posterior, dispositivo ARM64 (ou emulador x86_64) e
[Shizuku](https://shizuku.rikka.app/download/) instalado, iniciado e autorizado.

1. Instale o APK da [release](https://github.com/James-bb-ALT/AEMA/releases).
2. Abra o AEMA e autorize Shizuku, escolha uma pasta local, permita alarmes e notificações.
3. Ative a coleta automática. A primeira começa imediatamente; as seguintes seguem a cadência de 6 horas.

Cada execução cria `aema_<UTC>_<id>.zip`, com arquivos brutos, manifesto, hashes SHA-256 e
dataset processado. Uma cópia privada fica no app e outra vai para a pasta escolhida pelo
seletor Android, por exemplo `Documentos/AEMA`. Use essa pasta para transferir os ZIPs
posteriormente. Não há permissão de internet, conta, servidor ou envio automático no app.
Escolha um provedor local: provedores de nuvem do seletor podem sincronizar por conta própria.

As coletas são **snapshots acumulados**, sem reset de BatteryStats. O valor de um snapshot
não representa necessariamente o consumo das seis horas anteriores. O manifesto registra
horário previsto, horário real, atraso e relógio monotônico do Android.

Shizuku parado, telefone desligado, forçar parada e restrições do fabricante podem impedir
coletas. Sem root, normalmente é necessário reiniciar Shizuku após reiniciar o aparelho.
O app rearma o alarme após boot/atualização; não inventa capturas para os horários perdidos.
Uma falha de coleta produz um ZIP de diagnóstico quando o armazenamento está disponível.
Formato incompatível preserva os brutos e registra `parse_status: unsupported_or_invalid`.

[Guia Android e compilação](docs/android/README.md) ·
[Compatibilidade](docs/android/COMPATIBILITY.md) · [Privacidade](docs/study/PRIVACY.md).

## Computador

Python 3.10+; `pandas` é a dependência de runtime. Em um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\aema --checkin stats.csv --battery-report stats.txt --packages packageUID.txt --output-root outputs
```

O modo padrão é estrito. `--lenient` permite ignorar registros malformados e registra os
avisos. Cada execução publica um diretório novo `parsed_<UTC>_<id>` atomicamente.

Comandos adicionais:

```powershell
aema collect --serial SERIAL --output-root captures
aema inspect --metric computed_drain_mah --source power
aema demo --fixtures tests/fixtures --output-root demo-output
aema study-summary --battery-report stats.txt --output-root study-outputs
python -m aema.validation ensaios.csv
python -m aema.study protocolo.json ensaios.csv
```

O dataset contém os três CSVs históricos, tabelas canônicas CSV/JSONL, relações pacote/UID,
catálogo de métricas, diagnósticos e manifesto versionado. `aema.dataset.load_dataset`
verifica versões, arquivos obrigatórios, hashes, contagens e proveniência ao importar.
Para analisar um ZIP do telefone, extraia-o localmente e abra o diretório indicado por
`parsed_directory` no `capture_manifest.json`.

Para compartilhar um estudo por aplicativo, use `aema pseudonymize`; nunca compartilhe o
ZIP bruto como se fosse anônimo. O procedimento e os limites estão em
[Privacidade](docs/study/PRIVACY.md).

## Desenvolvimento

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest --cov=aema --cov-report=term-missing
.venv\Scripts\ruff check --no-cache src tests
.venv\Scripts\ruff format --check --no-cache src tests
```

A cobertura mínima exigida é 90%. GitHub Actions executa Python 3.10/3.13, Ruff e build,
testes JVM e lint Android. As fixtures anonimizadas têm hashes fixos e finais de linha LF.
Os testes de regressão usam essas fixtures publicáveis; dumps privados locais não entram no Git.

Estrutura: `src/aema/` contém o núcleo compartilhado; `android/` contém o app, serviço
Shizuku e agendamento; `tests/` contém testes unitários, integração e regressão;
`docs/` contém instruções, protocolos e evidências históricas.

## Limites atuais

- Check-in versão 9, tags `pr`, `wl`, `nt`, `m` e `pwi`. Tags sem schema são diagnosticadas;
  versões desconhecidas são rejeitadas, sem conversão silenciosa.
- O parser TXT cobre `Estimated power use (mAh)`, não o relatório completo.
- O APK inclui Python 3.13, pandas 2.1.3 e numpy 1.26.2, conforme os wheels Android
  disponíveis. A dependência pandas do host permanece `>=2.2,<3`.
- Compatibilidade de fabricantes, dispositivos ARM64 físicos e páginas de memória de 16 KiB
  exige validação específica. Não há alegação de precisão de 1 µA.

[Changelog](CHANGELOG.md) · [Notas da release](docs/releases/1.0.0.md) ·
[Estado atual](docs/STATUS.md) · [Guia do estudo](docs/study/RUNBOOK.md).
