# 10 — Resumo executivo

## O que o projeto é hoje

AEMA, neste diretório, não é um aplicativo Android. É um protótipo Python que lê três arquivos exportados de um aparelho via ADB/BatteryStats e tenta convertê-los em CSV. O material tem valor como ponto de partida e como captura diagnóstica, mas não constitui instrumento científico validado.

## O que funciona

- O programa executa no ambiente existente e cria três arquivos de saída.
- O mapeamento pacote→UID lê as 791 entradas da amostra.
- O parser textual localiza as estimativas BatteryStats de 173 UIDs.
- Os dados brutos preservam informações extensas sobre CPU, rede, wakelocks, sensores e consumo estimado.

## O que está errado ou incompleto

1. O parser do check-in usa a coluna errada e produz arquivo vazio; milhares de registros são descartados.
2. O parser textual chama valores em mAh de “tempo”, comprometendo qualquer análise dimensional.
3. Capacidade/drain são misturados numa string; total por UID é descartado.
4. UIDs e pacotes não são unidos; shared UIDs não são tratados no domínio.
5. Não há metadados de sessão, protocolo, calibração, testes ou dependências reproduzíveis.
6. Não há código Android, coleta em tempo real, RAM, corrente, PowerStats, Perfetto ou instrumento externo.
7. Não há Git; evolução, branches e intenção histórica não puderam ser reconstruídos.

## 0,001 mA

A meta equivale a 1 µA e **não foi demonstrada**. O código não lê corrente. As muitas casas decimais representam apenas saída numérica de estimativas acumuladas em mAh. Mesmo uma API que retorne µA precisa de caracterização do fuel gauge, resolução efetiva, ruído, taxa de atualização e comparação com referência calibrada.

## Consumo por componente

CPU, tela, Wi‑Fi, Bluetooth, modem, sensores, GNSS, câmera, áudio e vídeo têm estimativas BatteryStats. Há atividade que serve como proxy, mas não medição elétrica individual. GPU e armazenamento estão indisponíveis. Memória aparece com estimativa zero, o que não significa consumo zero. O dump declara que contadores EnergyConsumer em microcoulombs não são suportados no aparelho da captura.

## Confiabilidade atual

| Resultado | Situação |
|---|---|
| Pacote→UID da captura | Utilizável com ressalva de shared UID |
| CSV check-in gerado | Inutilizável: vazio |
| CSV textual | Numericamente derivado do dump, mas semanticamente mal rotulado |
| Ranking BatteryStats bruto | Potencialmente recuperável após correção e validação |
| Corrente de 1 µA | Não implementada/não validada |
| Energia de RAM ou GPU | Não disponível |
| Generalização científica | Não permitida pela única captura sem protocolo |

## Caminho recomendado

1. Confirmar a pergunta científica e localizar o eventual repositório Android original.
2. Preservar/anonimizar dados e registrar metadados de sessão.
3. Corrigir e testar os parsers sem mudar a natureza das métricas.
4. Definir protocolo e referência externa; decidir formalmente a meta de 1 µA.
5. Validar cada componente antes de construir interface ou otimizar desempenho.
6. Executar estudo repetível e somente então redigir resultados do TCC.

## Decisões do proprietário

É necessário escolher o foco primário (atribuição por app, componentes, RAM ou corrente), indicar dispositivos/hardware disponíveis, fornecer o repositório/histórico ausente se existir e esclarecer se 0,001 mA é requisito de resolução ou de exatidão.

## Estado da entrega

A auditoria terminou. Foram criados os documentos em `docs/audit/`, executadas apenas verificações não destrutivas e uma execução com saída temporária. Nenhuma refatoração, correção de bug ou funcionalidade foi implementada; nenhum commit ou push foi realizado.
