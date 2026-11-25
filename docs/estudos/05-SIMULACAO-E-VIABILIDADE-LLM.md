# Simulação e viabilidade técnica do fluxo IA — 24/11/2026

Este relatório documenta testes locais, sem uso de dados pessoais. A finalidade é
verificar integração, comportamento, capacidade de ajuste e limites do protótipo.
Artefatos completos da execução ficam em `dist/validation-2026-11-24/` (ignorado pelo
Git): logs, JSONs de métricas e hashes. Os scripts reproduzíveis estão em
[`experiments/`](../../experiments/).

## Resultado que é possível sustentar

O parser/exportador/importador consegue preparar dados sintéticos para o consumidor
da IA; o Qwen3-0.6B quantizado executa a leitura offline pelo processo nativo e fluxo
Android real; uma adaptação LoRA curta pode alterar a seleção de evidências em máquina
com GPU. A predição numérica sintética favoreceu um Ridge atualizado com os últimos
28 dias sobre baselines simples neste gerador. **Não medimos previsão real de bateria,
generalização para uso futuro, economia, compatibilidade em telefone físico de 6 GB,
nem aprendizado pessoal.**

## Testes de integração e comportamento

| Camada | Procedimento | Resultado / alcance |
|---|---|---|
| Python | Suite completa do projeto, incluindo parsing, validação e contratos LLM | 202 passaram; cobertura global 92,74% (piso configurado: 90%). |
| Formatação | Ruff check e format | Passaram após a correção. |
| Build Android | APK debug e APK AndroidTest | Build Gradle passou. |
| Android instrumentado | Emulador API 35, Android 15, x86_64, 6 GB; fluxo controlador/serviço/modelo/validador e cenários sintéticos | 8 no total: 7 passaram, 1 teste de alarme foi ignorado e zero falharam. A matriz de 8 cenários × 3 repetições (24 inferências) passou sem rejeições em 328,4 s. Os pesos oficiais Qwen3-0.6B Q8_0 são necessários. Emulador não comprova consumo elétrico ou desempenho no S25 Plus. |
| Modelo | 1 captura cumulativa feita pelo próprio emulador | Inadequada para treinar: sem delta/reset verificável e sem rótulo independente de seis horas. Nenhuma janela utilizável foi contada. |

A primeira matriz encontrou seleções em que o texto de ação gerado pelo LLM não
correspondia à evidência escolhida. A correção desta versão restringe a geração a IDs
de fatos; o aplicativo valida esses IDs e deriva a recomendação de uma regra local
associada ao fato positivo. Assim, o modelo continua escolhendo **qual evidência merece
atenção**, mas não redige/inventa a ação. Na matriz corrigida, todas as 24 leituras
foram aceitas. O teste verificou que sugestões correspondiam a ações suportadas por
fatos positivos e que valores zero não geravam sugestões. Também incluiu empate,
estimativa negativa, UID sem resolução e UID compartilhado. O teste usa valores
sintéticos; não avalia precisão futura nem qualidade de recomendações a usuários.

## Simulação de previsão numérica

`battery_validation.py` cria cinco séries independentes por semente, cada uma com 112
dias e quatro intervalos diários de seis horas. Componentes e UIDs são alvos separados.
Há padrão horário/semanal, fatores de uso compartilhados e uma mudança de padrão após
o dia 80. Para cada semente: 56 dias para treino, 14 para seleção de Ridge, 42 para
teste cronológico; 216 janelas de treino, 56 de validação e 168 de teste. A versão
congelada, a média por horário, persistência e valor do dia anterior são baselines. O
Ridge móvel usa só rótulos que já estariam disponíveis nos 28 dias anteriores.

No gerador sintético desta execução, o erro absoluto médio do total (mAh modelados) foi
aproximadamente 196 para persistência, 63 para valor do dia anterior, 61 para Ridge
congelado, 64 para média do horário e 55 para Ridge móvel de 28 dias, agregado entre
sementes. O detalhe por semente, MAE dos alvos, ranking do maior componente/UID, WAPE,
RMSE, paridade da exportação e salvaguardas contra vazamento está em `simulation.json`.
Esses números descrevem apenas a distribuição inventada no script; não são estimativas
da precisão ou erro do produto. Testes de mutação de atributos futuros, atualização de
rótulos atrasados e paridade numérica de exportação passaram.

## Ajuste LoRA demonstrativo

`lora_feasibility.py` ajusta Qwen3-0.6B em alvos de seleção de evidência sintéticos,
criados por regras e então divididos em treino/validação/teste (96/14/21). Usa LoRA
rank 8 em `q_proj` e `v_proj`, BF16, microbatch 1 com acumulação 2 e 60 passos. O
relatório `lora-result.json` registra revisão/hash do modelo, versões, hardware, picos
de VRAM/RAM, tempos, losses, gerações e recarga de adapter. Nesta execução, 60 passos
levaram 105,8 s; o pico de memória alocada pelo PyTorch foi 1,80 GB. A loss média de
teste caiu de 0,555 no modelo base para 0,000059 após o ajuste; a loss de validação
ajustada foi 0,000058. O computador medido tem RTX 3080 de 10 GB; isso não é o telefone alvo.
Em uma geração greedy de oito casos de teste, o adapter respondeu exatamente ao rótulo
sintético nos oito; o artefato foi recarregado com diferença de loss 0. Isso só mostra
aprendizado/reprodução de um pequeno padrão sintético. Os exemplos são pequenos e repetem
uma regra de rótulo; loss baixo ou acerto no conjunto de teste não prova generalização. O
adapter não foi convertido para GGUF, quantizado, instalado no app nem comparado com
treino em rótulos reais.

Treinar um LLM generativo em telefone não é requisito do protótipo: o app atualmente
faz inferência. O ensaio demonstra apenas que o ajuste PEFT é tecnicamente possível
no computador de referência com recursos mensurados. Para a previsão final, priorizar
um modelo numérico tabular/temporal e comparar contra baselines; usar o LLM pequeno
para explicar fatos validados é uma hipótese de arquitetura, ainda por avaliar.

## Reprodução e fontes

Na raiz do repositório, com Python/dependências do projeto instalados:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python experiments/battery_validation.py --output dist/validation-2026-11-24
python -m pytest
```

O ensaio LoRA requer ambiente separado com `torch==2.9.1+cu128`, `transformers==4.57.1`,
`peft==0.18.0`, `psutil==7.1.3`, GPU CUDA disponível, cache local do modelo e a revisão
exata registrada em `base-model-revision.txt`; o comando executado e versões constam
em `lora-training-final.log`/`lora-result.json`. Os testes instrumentados exigem SDK,
emulador e pesos locais; ver workflow Android e log final na pasta de artefatos.

Fontes primárias de implementação/ferramentas consultadas:

- [Cartão oficial Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) — arquitetura,
  licença e requisito de Transformers compatível.
- [Documentação PEFT LoRA](https://huggingface.co/docs/peft/main/package_reference/lora)
  — adaptadores e parâmetros de ajuste.
- [Instalação de versões anteriores PyTorch](https://pytorch.org/get-started/previous-versions/)
  — distribuição PyTorch/CUDA usada no ensaio.

O relatório completo é deliberadamente local porque logs de emulador e modelos grandes
são artefatos de teste; publique o código, protocolo e resultados resumidos, não dumps
de uso ou pesos fora de suas condições de licença.
