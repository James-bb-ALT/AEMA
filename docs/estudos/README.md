# Estudos de IA para previsão de bateria

**Pesquisa consultada em 24/11/2026 · Pesquisa histórica 1.0.2 · Software atual 2.0.1.**

**Implementação posterior:** as releases 2.0.0 e 2.0.1 acrescentam
[leitura local por LLM e debug](../android/LLM-E-DEBUG.md), usando pesos Qwen3 sem ajuste
pessoal. Este caderno preserva o recorte original da pesquisa. Previsão de seis horas,
treinamento pessoal e experimentos de economia continuam como trabalho proposto.

O objetivo final informado pelo autor é um assistente pessoal que preveja o consumo
das próximas **seis horas**, identifique componentes e aplicativos mais consumidores
e sugira mudanças. As previsões devem funcionar **no telefone, sem internet**, mirando
aparelhos com **pelo menos 6 GB de RAM**. O treinamento inicial e os reajustes maiores
podem acontecer no computador, com transferência local dos arquivos. O primeiro caso
é um **Samsung S25 Plus com One UI 9**, conforme informado pelo autor; ainda não houve
inspeção do aparelho, confirmação do Android/API nem benchmark físico.

## Conclusão provisória

Recomenda-se comparar um **preditor numérico personalizado + regras de recomendação +
LLM pequeno opcional para explicação** com um LLM que faça a previsão diretamente.
Os dados podem alimentar ambos os experimentos. Não é necessário convertê-los todos
em texto nem atualizar pesos de um LLM para que o sistema aprenda com o telefone.
Essa é uma proposta de engenharia fundamentada na revisão abaixo, não um resultado
experimental do AEMA. A literatura apresenta resultados divergentes para LLMs em
previsão temporal: [LLMTime](https://arxiv.org/abs/2310.07820),
[ablação de Tan et al.](https://arxiv.org/abs/2406.16964) e
[estudo de Qiu et al.](https://arxiv.org/abs/2602.14744).

O primeiro LLM candidato a benchmark é **Qwen3-0.6B**, em 4 bits e com geração curta.
**Qwen3.5-0.8B** entra como concorrente. **FunctionGemma 270M** merece um experimento
separado para selecionar ações estruturadas após especialização, não para conversa
livre. Nenhum foi medido ou treinado no projeto. A escolha final depende de português,
fidelidade aos dados, memória, tempo e energia no aparelho de 6 GB.

## Documentos

| Estudo | Conteúdo |
|---|---|
| [1. LLMs e previsão](01-LLMS-E-PREDICAO.md) | O que treinar, trabalhos relacionados e por que comparar uma arquitetura híbrida. |
| [2. Modelos e execução local](02-MODELOS-E-EXECUCAO-LOCAL.md) | Sete candidatos, triagem de alternativas, memória, licença e runtimes Android. |
| [3. Dados, treinamento e validação](03-DADOS-TREINAMENTO-E-VALIDACAO.md) | Rótulos, deltas, prevenção de vazamento, personalização, hipóteses e critérios experimentais. |
| [4. Arquitetura e plano experimental](04-ARQUITETURA-E-PLANO-EXPERIMENTAL.md) | Fluxos offline, artefatos, recomendações e etapas de implementação propostas. |
| [Fontes e método de pesquisa](FONTES.md) | Fontes primárias, versões consultadas, alcance da leitura e limites da revisão. |
| [5. Simulação e viabilidade técnica](05-SIMULACAO-E-VIABILIDADE-LLM.md) | Testes sintéticos, inferência Android, protótipo LoRA e limites de generalização. |

O [registro estruturado das fontes](fontes.json) facilita atualizações futuras.
As referências da infraestrutura e dos estudos elétricos anteriores continuam no
[capítulo 7 do manual](../projeto/07-REFERENCIAS-E-GLOSSARIO.md).

## Decisões registradas

| Tema | Estado em 24/11/2026 |
|---|---|
| Horizonte inicial | Confirmado pelo autor: próximas 6 h. |
| Alvos | Confirmado: componentes e aplicativos. Não são duas parcelas a somar. |
| Execução | Confirmado: inferência local, offline; treinamento maior permitido no computador. |
| Plataforma | Meta de compatibilidade: Android com 6 GB ou mais; não é garantia universal. |
| Coleta de 6 h | Implementada como snapshots; preservar os ZIPs e estudar amostragem adicional. |
| Modelo, frequência adicional e margens de erro | Propostas deste estudo; ainda sem ensaio de seleção. |
| Mudanças em configurações | Escopo atual: sugerir. Não há autorização de execução automática implícita. |

## O que existe e o que este estudo acrescenta

O AEMA 1.0.0 coleta, interpreta e exporta dados. O campo `snapshot_semantics` em
[`mobile.py`](../../src/aema/mobile.py) registra explicitamente que cada captura é
acumulada desde o reset do Android, não um delta de seis horas. O
[`catálogo`](../../src/aema/catalog.py) distingue estimativas e proxies. **Não há
modelo de IA, gerador de janelas, treinamento ou recomendador implementado.**

Esta edição acrescenta pesquisa e desenho experimental. Não apresenta dumps pessoais
como dataset validado, não informa uma precisão inexistente e não muda o APK.
O estudo de [validação elétrica](../projeto/02-METODOLOGIA.md) permanece necessário
para avaliar consumo físico. A nova linha de previsão amplia o objetivo de produto;
não transforma as hipóteses anteriores em resultados já obtidos.

## Como manter os próximos estudos

1. Criar uma página datada com pergunta, método, fontes, resultado e limitações.
2. Identificar separadamente evidência publicada, evidência local e proposta.
3. Citar a fonte junto da afirmação e adicioná-la ao registro de fontes.
4. Registrar aparelhos, versões, dados e comandos para qualquer experimento executado.
5. Atualizar este índice e o histórico de decisões sem apagar conclusões anteriores.

Modelos e documentação externa mudam. As revisões de model cards foram registradas
quando disponíveis; nenhuma disponibilidade futura de conversão/runtime é garantida.
