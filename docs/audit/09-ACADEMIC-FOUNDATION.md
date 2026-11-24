# 09 — Fundamentação acadêmica

## Base comprovada

O conjunto entregue registra uma sessão BatteryStats e um pós-processador. BatteryStats rastreia estados/tempos e usa perfis de potência para aproximar consumo por componente; não mede diretamente a corrente de cada componente ([AOSP — Power profiles](https://source.android.com/docs/core/power)). O bloco analisado declara a unidade mAh, capacidade 4700 mAh, consumo computado 1377 mAh e faixa “actual” 1269–1363 mAh.

O dump também mostra:

- janela em bateria de 4 h 7 min 13,729 s;
- tela 641 mAh, CPU 406 mAh, modem 108 mAh, Wi‑Fi 16,5 mAh, Bluetooth 16,4 mAh, sensores 13,1 mAh, GNSS 36,1 mAh;
- memória com 0 mAh no registro `pwi`, sem evidência de medição de DRAM;
- `EnergyConsumer` não suportado;
- estimativas por 173 UIDs, sem união final a pacotes.

Esses são dados de **uma captura não controlada**. Não são resultados experimentais generalizáveis.

## Problema científico reconstruído — proposta

Formulação conservadora compatível com o material:

> Avaliar em que medida estatísticas e modelos de energia disponibilizados pelo Android permitem atribuir consumo de bateria a componentes e aplicações, e quantificar suas limitações frente a uma referência experimental.

Essa formulação é proposta, não intenção comprovada do autor. Uma variante focada em RAM só é defensável se hardware e método capazes de isolar energia de memória forem demonstrados.

## Objetivos propostos

**Geral:** caracterizar a validade, granularidade e portabilidade de estimativas Android de consumo por componente/aplicação.

**Específicos:**

1. Catalogar fontes, unidades, modelos e disponibilidade.
2. Comparar estimativa total com referência externa.
3. Medir repetibilidade e erro sob workloads controlados.
4. Avaliar quando atribuição por componente é medida, modelo ou proxy.
5. Testar a hipótese de resolução de 1 µA somente se o sistema de medição a suportar.

## Hipóteses candidatas — ainda não testadas

- H1: estimativas BatteryStats preservam ranking relativo entre workloads, ainda que não tenham exatidão metrológica suficiente para corrente instantânea.
- H2: a diferença entre drain computado e referência varia com componente, build e estado do dispositivo.
- H3: atividade de CPU/rede correlaciona-se com energia total, mas não identifica causalmente uma parcela sem controle de confundidores.
- H4: 1 µA de resolução efetiva não é demonstrável pelo pipeline atual.

H4 é confirmada apenas para **esta implementação**; não é uma impossibilidade física universal.

## Desenho metodológico proposto

### Variáveis

- Independentes: workload, componente ativado, nível/estado, duração, brilho, conectividade.
- Dependentes: carga/energia da referência; corrente média; estimativa BatteryStats; erro absoluto/relativo.
- Controle/confundidores: temperatura, SoC, processos de fundo, sinal, DVFS, brilho/conteúdo, aging, charging, firmware.

### Procedimento

1. Congelar dispositivo/build e registrar metadados.
2. Definir idle baseline e workloads determinísticos separados.
3. Coletar referência externa e Android com marcadores sincronizados.
4. Repetir e randomizar a ordem das condições.
5. Subtrair baseline somente quando a hipótese de aditividade for justificada.
6. Reportar distribuição, intervalo de confiança e orçamento de incerteza.
7. Repetir em dispositivos distintos apenas se a pergunta incluir portabilidade.

### Validade

- **Interna:** atividade concorrente e thermal throttling podem explicar diferenças.
- **Construto:** mAh estimado não é corrente instantânea; tempo ativo não é energia.
- **Externa:** power profiles, rails e firmware variam entre aparelhos.
- **Conclusão:** uma única captura não permite inferência estatística.

## Interpretação da captura atual

O consumo computado (1377 mAh) está 14 mAh acima do limite superior da faixa “actual” (1363 mAh), cerca de 1,0% desse limite; contra o limite inferior, a diferença é 108 mAh. Essa comparação é descritiva, não calibração: a “faixa actual” também é derivada pelo sistema e não há referência externa.

A documentação histórica do próprio Android descreve “Estimated power use (mAh)” como estimativa grosseira e não dado experimental ([fonte AOSP arquivada](https://android.googlesource.com/platform/frameworks/base/+/android-6.0.0_r26/docs/html/tools/performance/batterystats-battery-historian/charts.jd)). Implementações modernas podem incorporar dados medidos quando o HAL fornece, mas o dump desta amostra declara ausência de EnergyConsumer.

## Critérios de afirmação

| Afirmação pretendida | Evidência mínima |
|---|---|
| “O Android reporta X mAh estimados” | Parser validado + campo/unidade + versão |
| “O dispositivo consumiu X” | Referência caracterizada + incerteza + janela |
| “Componente C consumiu X” | Rail exclusivo ou método de atribuição validado |
| “App A causou X” | Isolamento/controle; correlação sozinha é insuficiente |
| “Resolução 1 µA” | LSB efetivo, ruído, taxa, repetibilidade e calibração |
| “Exatidão 1 µA” | Incerteza expandida compatível em toda a faixa declarada |

## Informações ainda necessárias ao TCC

Pergunta aprovada, revisão bibliográfica sistemática, hardware e instrumento, critérios de inclusão/exclusão, tamanho amostral, plano estatístico, protocolo de calibração, ética/privacidade, repositório correto e resultados repetidos. Nenhum desses itens deve ser preenchido retroativamente sem evidência.
