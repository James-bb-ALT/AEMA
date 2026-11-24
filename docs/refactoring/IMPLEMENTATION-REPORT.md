# Relatório de implementação da refatoração

Data da validação: 20 de setembro de 2026.

## Escopo executado

A implementação monolítica de seis arquivos na raiz foi convertida em um pacote instalável
`src/aema`. A coleta de dados Android, a questão científica do TCC e os relatórios históricos
da auditoria ficaram fora da alteração. Os três dados brutos e todos os diretórios `parsed_*`
anteriores permaneceram intocados.

Como o diretório não possui repositório Git, os seis fontes originais foram copiados sem
alteração para `backup/pre-refactor-20260920/`. O manifesto dessa pasta registra os SHA-256.

## Arquitetura anterior e nova

Antes, `main.py` fixava entradas e persistência; cada parser abria seu arquivo diretamente e
devolvia um DataFrame; tradução, validação, encoding e erros não tinham contratos separados.
O diretório de saída baseado apenas em segundos podia colidir e era criado antes da conclusão.

Agora as responsabilidades são:

| Responsabilidade | Implementação |
|---|---|
| CLI e código de saída | `src/aema/cli.py`, `src/aema/__main__.py` |
| Orquestração sem I/O de saída | `src/aema/pipeline.py` |
| Check-in v9 | `src/aema/parsers/checkin.py` |
| Relatório estimado em mAh | `src/aema/parsers/battery_report.py` |
| Relações pacote/UID | `src/aema/parsers/packages.py` |
| Modelos e diagnósticos | `src/aema/models.py` |
| Schemas suportados | `src/aema/schemas.py` |
| Conversões puras | `src/aema/normalization.py` |
| Arquivos, encoding e hash | `src/aema/files.py` |
| Exportação transacional | `src/aema/exporters.py` |

O pipeline produz `PipelineResult` em memória. O exportador grava primeiro em diretório
temporário, inclui manifesto e somente então publica por renomeação atômica em um nome com
timestamp UTC e UUID. Uma falha remove o temporário e não anuncia sucesso.

## Correções implementadas

### Check-in CSV

- A tag passou da coluna 3 incorreta para a coluna 4 do registro (índice 3).
- `checkin_version`, UID, categoria, tag e linha de origem são preservados.
- Há schema próprio para `pr`, `wl`, `nt`, `m` e `pwi`.
- `wl` aceita grupos variáveis de seis campos e valida os tipos `f`, `p`, `bp` e `w`.
- `pr` preserva ANRs e crashes; `nt` preserva os 22 campos; `m`, os 21 campos; `pwi`, os
  cinco campos após a base.
- Versão diferente de 9, truncamento, valor inválido, tipo de wakelock desconhecido ou grupo
  duplicado geram erro explícito no modo estrito.
- Tags não implementadas são contadas em diagnósticos e não são declaradas como suportadas.

As definições foram verificadas contra `BatteryStats.java` do AOSP, incluindo a unidade de
`mobile_active_time_us` e a ordem dos campos da versão 9:
<https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/os/BatteryStats.java>.

### Relatório TXT

- Capacidade, drenagem computada e faixa de drenagem real são valores numéricos separados.
- O total atribuído a cada UID foi preservado.
- UIDs `u<usuário>a<índice>` seguem `usuário * 100000 + 10000 + índice`; `u10a42`, por
  exemplo, vira `1010042`.
- Sinais e notação científica são aceitos sem limpeza destrutiva.
- Totais globais, totais por UID, estados e componentes usam nomes terminados em `_mah`.
- `unit=mAh` e `measurement_kind=estimated_or_attributed` impedem interpretação como tempo,
  corrente, potência, energia ou medição elétrica direta.
- Texto de duração entre parênteses não é reinterpretado como carga.

### Pacotes e UIDs

- O formato completo `package:<nome> uid:<inteiro>` é validado.
- Vários pacotes com o mesmo UID e o mesmo pacote observado em linhas distintas não são
  condensados; relações muitos-para-muitos permanecem representáveis.
- Entradas vazias e inválidas falham no modo estrito; duplicatas exatas recebem diagnóstico.

## Arquivos alterados e adicionados

- Alterados: os seis módulos Python da raiz, agora fachadas/entrada de compatibilidade.
- Adicionados: `pyproject.toml`, `.gitignore`, `README.md`, `src/aema/**`, `tests/**`, o backup
  recuperável e este relatório.
- Não alterados: `stats.csv`, `stats.txt`, `packageUID.txt`, `docs/audit/**` e `parsed_*`.

## Testes

A suíte contém testes unitários, integração, golden e regressão. As fixtures pequenas cobrem
schemas, unidades, UIDs numéricos e multiusuário, UID compartilhado, sinais, notação
científica, UTF-8/UTF-16 com BOM, entradas vazias, truncadas, malformadas, ausentes, versão
incompatível, diagnósticos lenientes, colisão de saída e limpeza após falha de exportação.

O teste integral percorre `entrada → parsing → normalização → exportação`. O teste dos dados
reais não usa os CSVs antigos como resultado esperado.

## Resultados da validação final

Executado no Windows com Python 3.13.9 no ambiente de desenvolvimento:

| Verificação | Resultado |
|---|---|
| Suíte pytest completa | 30 aprovados de 30; nenhum skip |
| Integração e golden tests | aprovados dentro da suíte completa |
| Cobertura de linhas/branches | 93,21% total; limite configurado em 90% |
| Ruff lint | `All checks passed!` |
| Ruff format | 30 arquivos já formatados |
| Pipeline nos dados existentes | 1.785 check-in, 174 power report, 791 pacotes |
| Contagens check-in | `pr=819`, `wl=491`, `nt=65`, `m=1`, `pwi=409` |
| Hashes das entradas após a execução | iguais aos valores preservados |
| Instalação isolada | pacote 0.1.0 importado e CLI carregada em Python 3.10.6 |

Comandos executados:

```powershell
.venv\Scripts\python -m pytest --cov=aema --cov-report=term-missing --cov-report=xml
.venv\Scripts\ruff check --no-cache src tests csv_parser.py txt_parser.py uid_parser.py translation.py utils.py main.py
.venv\Scripts\ruff format --check --no-cache src tests csv_parser.py txt_parser.py uid_parser.py translation.py utils.py main.py
.venv\Scripts\aema --checkin stats.csv --battery-report stats.txt --packages packageUID.txt --output-root outputs
```

O resultado integral foi publicado em
`outputs/parsed_20260921T011341Z_5665875c/` (timestamp em UTC). A conferência posterior leu
os três CSVs e confirmou respectivamente 1.785, 174 e 791 registros, sem UID vazio nas tabelas
check-in e pacote. O manifesto contém os hashes, diagnósticos e tags deliberadamente não
suportadas.

A validação isolada instalou o wheel construído pelo `pyproject.toml` em um destino separado
da `.venv`, importou AEMA/pandas e abriu `python -m aema --help`. O pip global informou
conflitos preexistentes de outros pacotes do usuário; eles não afetaram o destino isolado nem
o pacote AEMA.

## Preservação verificável

| Entrada | SHA-256 esperado |
|---|---|
| `stats.csv` | `2529A96F3FAFFA75FEF7FC879525E3A63638EED67BA601AB7BA69D5FB99EC12D` |
| `stats.txt` | `3ADF138A7173FF4CA529EF0E59A47C5359F420F0E1D84FCBF0CB177A961086F6` |
| `packageUID.txt` | `C6D00A19EA39F7D34E0A54364738FFFDE57B82EA95AAD43D050A4C1708487C4A` |

## Limitações restantes

- Tags check-in fora de `pr`, `wl`, `nt`, `m` e `pwi` continuam fora do escopo e aparecem
  como não suportadas.
- Somente a seção `Estimated power use (mAh)` do relatório humano é interpretada.
- A publicação atômica depende de temporário e destino estarem no mesmo sistema de arquivos;
  o exportador garante isso criando ambos sob o mesmo diretório raiz.
