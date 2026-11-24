# 01 — Recuperação do projeto

## Escopo efetivamente encontrado

**Comprovado.** O diretório contém seis arquivos Python (359 linhas), uma `.venv`, configuração PyCharm, três capturas UTF-16 de dados Android e dois conjuntos idênticos de CSVs gerados. Não há `.git`, `AndroidManifest.xml`, Gradle, Java/Kotlin, JNI, código nativo, README, manifesto de dependências ou testes.

O nome do módulo IDE é “AEMA - Android Energy Monitoring Agent” ([`.idea/AEMA - Android Energy Monitoring Agent.iml`](../../.idea/AEMA%20-%20Android%20Energy%20Monitoring%20Agent.iml)). O código declara como entradas:

- `stats.csv`: saída de `dumpsys batterystats --checkin` ([`csv_parser.py`, linhas 4–8](../../csv_parser.py));
- `stats.txt`: saída legível de `dumpsys batterystats` ([`txt_parser.py`, linhas 5–10](../../txt_parser.py));
- `packageUID.txt`: saída de `pm list packages -U` ([`uid_parser.py`, linhas 3–7](../../uid_parser.py)).

Isso demonstra um **pós-processador de BatteryStats executado no computador**, não um agente Android residente.

## Linha de evolução recuperável

| Evidência | O que permite afirmar | Limite |
|---|---|---|
| Fontes e dados têm timestamps locais de 26/06/2025 | Código, capturas e primeiras saídas coexistiam nessa data no sistema de arquivos atual | Timestamp não comprova autoria nem sequência de commits |
| Duas pastas `parsed_20250928_133356` e `parsed_20251002_133345` | Houve ao menos duas cópias nomeadas de resultados | Conteúdo dos três CSVs é byte a byte idêntico; nomes das pastas divergem dos timestamps dos arquivos e não constituem histórico confiável |
| Comentários `:contentReference[oaicite:…]` em quatro fontes | Restaram marcadores de citação não resolvidos | A origem das citações e das decisões não está preservada |
| Ausência de `.git` | Nenhum branch, commit, autor, mensagem ou arquivo removido pode ser auditado | O histórico pode existir em outro local, mas isso não foi demonstrado |

Não é possível reconstruir decisões históricas além desses fatos. Em especial, não há evidência local de app Android anterior, protótipo de coleta em tempo real ou experimentos controlados.

## Objetivo científico: fatos e interpretações

### Comprovado pelo repositório

O pipeline tenta extrair estatísticas de processos, wakelocks, rede, estado geral, estimativas BatteryStats por UID e associação UID→pacote. O dump contém um bloco “Estimated power use (mAh)” ([`stats.txt`, a partir da linha 37152](../../stats.txt)) e o parser textual foi escrito especificamente em torno das linhas `UID` desse bloco.

Classificação mais fiel: **D + F + parte de B** — profiling pós-coleta de processos/aplicações, estimativa de consumo por componente/UID e análise de carga estimada do dispositivo. Não há implementação de A (gerenciamento de RAM), C (energia atribuível à RAM) ou E (medição própria de corrente).

### Inferências plausíveis, não confirmadas

1. **Analisador de consumo por aplicação/componente.** É a hipótese mais forte: `pwi`, UIDs e pacotes estão nos dados, e as colunas finais refletem componentes energéticos.
2. **Etapa exploratória de um futuro “Android Energy Monitoring Agent”.** O nome IDE sustenta a direção, mas não existe agente no material entregue.
3. **Ferramenta para TCC sobre energia e memória.** O contexto fornecido pelo proprietário cita RAM e 0,001 mA, porém o repositório não contém implementação correspondente.

## Reconstrução científica mínima

| Elemento | Identificado | Ainda não identificado |
|---|---|---|
| Problema | Converter estatísticas Android exportadas em tabelas analisáveis | Pergunta científica formal e população/dispositivos-alvo |
| Objetivo geral | Organizar dados BatteryStats por componente e UID | Se o objetivo final é diagnóstico de apps, modelagem energética, corrente ou RAM |
| Variáveis presentes | mAh estimado, tempos/contagens, tráfego, CPU, wakelocks, UID/pacote | Corrente amostrada, tensão sincronizada, potência, energia externa, RAM/DRAM calibrada |
| Metodologia presente | Uma captura acumulada desde a última carga e parsing offline | Protocolo de coleta, repetição, controle, calibração, baseline e análise de incerteza |
| Hipóteses/resultados esperados | Nenhum registrado | Todos dependem do proprietário/orientador |

## Decisões que dependem do proprietário

1. Qual é a pergunta principal: consumo total, atribuição por app, consumo da RAM ou outra?
2. O app Android/branch/repositório original existe em outro local?
3. “0,001 mA” significa resolução exibida, resolução do sensor ou incerteza máxima?
4. Quais dispositivos e versões Android compõem o estudo?
5. Há acesso a equipamento externo, firmware/OEM ou aparelho com ODPM/PowerStats?
6. Qual é a unidade de resultado científico pretendida: mA, mAh, mW, mWh ou J?
7. Qual workload, duração, número de repetições e condições ambientais são aceitáveis?
