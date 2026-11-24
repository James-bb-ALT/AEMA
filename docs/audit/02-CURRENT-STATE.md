# 02 — Estado atual

## Inventário

| Artefato | Papel observado | Estado |
|---|---|---|
| [`main.py`](../../main.py) | Orquestra três parsers e grava três CSVs em pasta temporal | Implementado; executa, mas não valida entradas nem resultados |
| [`csv_parser.py`](../../csv_parser.py) | Tenta ler quatro tipos do formato check-in | **Quebrado com a amostra atual:** retorna DataFrame `(0, 0)` |
| [`txt_parser.py`](../../txt_parser.py) | Extrai resumo global e itens `UID` do texto | Parcial e semanticamente incorreto |
| [`uid_parser.py`](../../uid_parser.py) | Lê `package:<nome> uid:<n>` | Funcional para a amostra; 791/791 linhas lidas |
| [`translation.py`](../../translation.py) | Renomeia campos | Parcial; nomes induzem erro de unidade |
| [`utils.py`](../../utils.py) | Cria `parsed_YYYYMMDD_HHMMSS` | Funcional, sem prevenção de colisão por segundo |
| `stats.txt` | Dump legível BatteryStats, 59.588 linhas | Dado bruto único, UTF-16 LE |
| `stats.csv` | Check-in BatteryStats, 4.218 registros | Dado bruto único, UTF-16 LE; versão de check-in 9 |
| `packageUID.txt` | Inventário pacote→UID, 791 linhas | Dado bruto único, UTF-16 LE |
| `parsed_*/*.csv` | Resultados de duas execuções/cópias | Idênticos; check-in vazio, texto 174 linhas, UID 791 linhas |

## Funcionalidades implementadas

- Entrada hardcoded pelos nomes `stats.csv`, `stats.txt` e `packageUID.txt` ([`main.py`, linhas 9–34](../../main.py)).
- Criação de pasta de saída com timestamp em segundos ([`utils.py`, linhas 4–11](../../utils.py)).
- Leitura UTF-16 das três fontes.
- Exportação pandas para CSV UTF-8, sem índice.
- Extração de 173 UIDs do bloco de potência textual, mais uma linha global.
- Associação de 791 pacotes a 653 UIDs; 14 UIDs são compartilhados por múltiplos pacotes, comportamento Android legítimo que exige relação muitos-para-muitos.

## Parcial ou enganoso

- `stats_txt_parsed.csv` contém valores de **carga estimada em mAh**, mas colunas como `CPU_foreground_time`, `Screen_on_time` e `Audio_time` sugerem duração. A origem está explicitamente sob “Estimated power use (mAh)” no dump.
- O valor total depois de `UID` (por exemplo, `251` para `u0a382`) é descartado; apenas subcomponentes são preservados.
- `Battery_capacity` armazena a linha inteira `4700, Rated: ..., Computed drain: ...`, não um número. `Computed_drain` e `Actual_drain` ficam ausentes porque aparecem na mesma linha e o parser usa `elif` ([`txt_parser.py`, linhas 23–33 e 90–99](../../txt_parser.py)).
- O mapeamento UID→pacote é exportado separadamente e nunca unido às estimativas.
- Todos os valores do check-in permanecem strings antes do `concat`; não há unidade, tipo de registro, UID ou timestamp na saída projetada.

## Quebrado

- O check-in usa a quarta coluna como tag (`pr`, `wl`, `nt`, `m`) e a terceira como categoria (`i`/`l`). O parser testa `parts[2]` ([`csv_parser.py`, linhas 21–25](../../csv_parser.py)). Resultado validado: arquivo de 2 bytes contendo somente quebra de linha.
- Mesmo trocando apenas o índice da tag, os campos continuam deslocados: o UID está na coluna 2 e a tag na 4; dados começam na 5. O código começa em `parts[3]` e omite UID/categoria.
- `wl` é um registro de grupos variáveis (nome seguido de trios tipo/tempo/contagem), não as seis posições fixas assumidas nas linhas 35–45.
- `nt` e `m` da amostra têm mais campos e schema distinto do pressuposto. A amostra contém 65 `nt`, 1 `m`, 819 `pr` e 491 `wl`, todos perdidos.

## Ausente

- Aplicativo Android, Manifest, níveis de API, permissões e lifecycle.
- Coleta automatizada via ADB e captura de metadados do dispositivo.
- BatteryManager, Perfetto/System Trace, PowerStats HAL, procfs/sysfs ou instrumento externo no código.
- Amostragem de corrente, tensão, potência ou memória RAM.
- Persistência com timestamp de amostra, unidade, dispositivo, sessão e condições experimentais.
- Requisitos Python reproduzíveis, CLI, logs, validação de schema e testes.
- Análise estatística, calibração e protocolo acadêmico.

## Planejado versus não identificado

Nada está marcado no repositório como plano futuro. RAM, corrente de 0,001 mA e decomposição por componente são intenções informadas pelo proprietário, não backlog recuperado. A implementação atualmente comprovada não demonstra essas metas.
