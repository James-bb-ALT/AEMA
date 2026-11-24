# Fontes e método da pesquisa

[Índice dos estudos](README.md) · [Registro estruturado](fontes.json)

**Data de consulta de todas as entradas: 24/11/2026.** Data de consulta não é data de
publicação. Páginas sem versão fixa podem mudar; revisões disponíveis foram registradas.

## Método e alcance

Revisão exploratória dirigida ao problema do AEMA, não revisão sistemática exaustiva.
Foram buscadas fontes primárias de modelagem de bateria, previsão temporal, adaptação
de modelos e inferência Android. Termos incluíram `small language models on device`,
`Gemma 270M`, `Qwen3.5 0.8B`, `PowerTutor`, `Carat`, `LLM time series forecasting`,
`LoRA`, `QLoRA`, `Chronos-Bolt tiny` e nomes dos runtimes.

Critérios de inclusão: origem do produtor/autor, relação com previsão ou execução
local, identificação suficiente e acesso ao conteúdo pertinente. Discussões sociais,
rankings comerciais e relatos de desempenho de terceiros não fundamentaram a seleção.
Não se assume que os benchmarks de linguagem medem precisão elétrica.

O backend Exa previsto na skill Agent Reach não estava configurado (`Unknown MCP server
'exa'`). A pesquisa continuou pela busca web disponível, leitura de fontes oficiais,
Jina Reader para a página FunctionGemma, API pública do Hugging Face e consultas
somente de leitura via `gh` para revisões de runtime. Não houve importação de cookies,
login em hubs de modelos, aceite de termos gated, instalação de canais ou download de pesos.

Os estudos científicos foram lidos no alcance indicado abaixo. Para F05–F10,
a síntese se baseia nos resumos/metadados consultados; não equivale a auditoria
integral dos métodos e suplementos. Resultados divergentes foram mantidos na revisão.
Não houve reprodução de benchmarks, revisão por pares deste documento ou teste em
telefone físico nesta entrega. As propostas de arquitetura e os limites candidatos
de engenharia são inferências nossas, identificadas como propostas.

## Fundamentos de consumo Android

<a id="f01"></a>
**F01 — Android Open Source Project. Measure power values.**
[Documento oficial](https://source.android.com/docs/core/power/values).
Leitura: relação entre perfis, atividade e atribuição de carga; diferenças de hardware.
Sustenta a distinção entre estimativa Android e referência elétrica. Não certifica o
perfil do fabricante nem a incerteza dos valores produzidos no telefone do autor.

<a id="f02"></a>
**F02 — Android Developers. BatteryManager API reference.**
[Documento oficial](https://developer.android.com/reference/android/os/BatteryManager).
Leitura: propriedades de carga/corrente, unidades, sinal e retorno indisponível.
Última atualização exibida na consulta: 03/08/2026. A existência da API não garante
suporte ou calibração do sensor em todo aparelho.

<a id="f03"></a>
**F03 — Oliner, A.; Iyer, A. P.; Stoica, I.; Lagerspetz, E.; Tarkoma, S. (2013).
Carat: Collaborative Energy Diagnosis for Mobile Devices. UCB/EECS-2013-17.**
[Registro e resumo dos autores na UC Berkeley](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2013/EECS-2013-17.html).
Leitura: resumo e metadados, com diagnóstico/recomendações. Seus resultados não foram
transferidos numericamente ao AEMA. Arquitetura e população diferem do caso offline pessoal.

<a id="f04"></a>
**F04 — Zhang, L.; Tiwana, B.; Qian, Z.; Wang, Z.; Dick, R. P.; Mao, Z. M.; Yang, L.
(2010). Accurate Online Power Estimation and Automatic Battery Behavior Based Power
Model Generation for Smartphones. CODES+ISSS 2010.**
[PDF dos autores em repositório acadêmico](https://www.cs.columbia.edu/~coms6998-8/papers/powertutor_cases2010.pdf).
Leitura: resumo e introdução sobre PowerBooter/PowerTutor. Fonte primária histórica,
hospedada por outra instituição; a página original do projeto retornou erro na consulta.
Não foi reproduzida nem validada para Android atual.

## Previsão e adaptação

<a id="f05"></a>
**F05 — Gruver, N.; Finzi, M.; Qiu, S.; Wilson, A. G. (2023).
Large Language Models Are Zero-Shot Time Series Forecasters. NeurIPS 2023.**
[arXiv:2310.07820v3](https://arxiv.org/abs/2310.07820v3), revisão de 12/08/2024.
Leitura: resumo e metadados. Fundamenta o braço LLM direto e a atenção à tokenização;
não avalia a aplicação AEMA nem prova desempenho de modelos sub-1B.

<a id="f06"></a>
**F06 — Tan, M.; Merrill, M. A.; Gupta, V.; Althoff, T.; Hartvigsen, T. (2024).
Are Language Models Actually Useful for Time Series Forecasting? NeurIPS 2024.**
[arXiv:2406.16964v2](https://arxiv.org/abs/2406.16964v2), revisão de 26/10/2024.
Leitura: resumo/metadados. Ablações motivam baselines e medição de custo; não estabelecem
uma impossibilidade universal de uso de LLMs.

<a id="f07"></a>
**F07 — Qiu, X.; Tong, J.; Sun, Y.; Ma, Y.; Zhang, W.; Shen, X. (2026).
Rethinking the Role of LLMs in Time Series Forecasting.**
[arXiv:2602.14744v2](https://arxiv.org/abs/2602.14744v2), revisão de 02/03/2026.
Leitura: resumo/metadados do preprint. Contraponto favorável em escala e generalização;
estado de avaliação editorial não foi confirmado. Não é ensaio de bateria móvel.

<a id="f08"></a>
**F08 — Grinsztajn, L.; Oyallon, E.; Varoquaux, G. (2022).
Why do tree-based models still outperform deep learning on tabular data?**
[arXiv:2207.08815v1](https://arxiv.org/abs/2207.08815v1), 18/07/2022.
Leitura: resumo/metadados. Motiva a comparação com árvores, sem extrapolar seu ranking
histórico a todo modelo ou dataset atual.

<a id="f09"></a>
**F09 — Hu, E. J. et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models.**
[arXiv:2106.09685v2](https://arxiv.org/abs/2106.09685v2), revisão de 16/10/2021.
Leitura: resumo/metadados. Base conceitual de adaptação de baixa dimensão.

<a id="f10"></a>
**F10 — Dettmers, T.; Pagnoni, A.; Holtzman, A.; Zettlemoyer, L. (2023).
QLoRA: Efficient Finetuning of Quantized LLMs.**
[arXiv:2305.14314v1](https://arxiv.org/abs/2305.14314v1), 23/05/2023.
Leitura: resumo/metadados. Fundamenta ajuste com base quantizada; consumo de treino e
qualidade no AEMA exigem medição própria.

## Modelos candidatos

As revisões abaixo foram obtidas na API pública do hub na data da pesquisa. Elas
identificam o repositório consultado; não são hashes de um GGUF ou de pesos baixados.
As leituras cobriram model cards públicos, avisos de uso e metadados de licença/acesso.

<a id="f11"></a>
**F11 — Qwen. Qwen3-0.6B.**
[Model card](https://huggingface.co/Qwen/Qwen3-0.6B) ·
[revisão consultada](https://huggingface.co/Qwen/Qwen3-0.6B/tree/c1899de289a04d12100db370d81485cdf75e47ca).
Licença declarada Apache 2.0. Peso nominal, uso local e modos de geração foram os
itens relevantes. Não há validação do AEMA nesta fonte.

<a id="f12"></a>
**F12 — Qwen. Qwen3.5-0.8B.**
[Model card](https://huggingface.co/Qwen/Qwen3.5-0.8B) ·
[revisão consultada](https://huggingface.co/Qwen/Qwen3.5-0.8B/tree/2fc06364715b967f1860aea9cf38778875588b17).
Licença declarada Apache 2.0. Consultados arquitetura, escopo e aviso de geração;
compatibilidade do artefato móvel não foi testada.

<a id="f13"></a>
**F13 — Google. Gemma 3 270M IT.**
[Model card](https://huggingface.co/google/gemma-3-270m-it) ·
[revisão consultada](https://huggingface.co/google/gemma-3-270m-it/tree/ac82b4e820549b854eebf28ce6dedaf9fdfa17b3).
Licença declarada Gemma; acesso marcado `manual` na API do hub. Acesso público ao
card não foi tratado como autorização de download de pesos.

<a id="f14"></a>
**F14 — Google. FunctionGemma 270M IT.**
[Model card](https://huggingface.co/google/functiongemma-270m-it) ·
[visão oficial](https://gemma.ai/models/functiongemma/) ·
[revisão consultada](https://huggingface.co/google/functiongemma-270m-it/tree/39eccb091651513a5dfb56892d3714c1b5b8276c).
Licença declarada Gemma, acesso `manual`. Modelo para chamadas de funções; não
confundir com assistente de diálogo nem com autorização para executar ações.

<a id="f15"></a>
**F15 — Google. Gemma 3 1B IT.**
[Model card](https://huggingface.co/google/gemma-3-1b-it) ·
[revisão consultada](https://huggingface.co/google/gemma-3-1b-it/tree/dcc83ea841ab6100d6b47a070329e1ba4cf78752).
Licença declarada Gemma, acesso `manual`. Candidato de comparação, não seleção final.

<a id="f16"></a>
**F16 — Hugging Face Smol Models Research. SmolLM2-360M-Instruct.**
[Model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) ·
[revisão consultada](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/tree/a10cc1512eabd3dde888204e902eca88bddb4951).
Licença declarada Apache 2.0. O aviso de foco em inglês fundamenta o risco de português.

<a id="f17"></a>
**F17 — Amazon. Chronos-Bolt Tiny.**
[Model card](https://huggingface.co/amazon/chronos-bolt-tiny) ·
[revisão consultada](https://huggingface.co/amazon/chronos-bolt-tiny/tree/a0e552de83495b5c28c14c71c374f3e33280b340).
Licença declarada Apache 2.0. Modelo temporal de 9M; não produz explicações conversacionais.
Card aponta sucessor. O estudo não verificou conversão Android nem reproduziu benchmarks.

## Runtimes e avaliação

<a id="f18"></a>
**F18 — ggml-org. llama.cpp, documentação Android.**
[Documento em revisão fixa](https://github.com/ggml-org/llama.cpp/blob/0ce7f213b0749fa4dee4e87d8ae7bf63e621c1ad/docs/android.md).
Consultada documentação de binding e arquivos GGUF. Commit de `master` obtido via API;
nenhum binário foi compilado nesta pesquisa.

<a id="f19"></a>
**F19 — Google AI Edge. LiteRT-LM Overview.**
[Documento oficial](https://developers.google.com/edge/litert-lm/overview) ·
[repositório oficial](https://github.com/google-ai-edge/LiteRT-LM).
Consultados visão geral e tabela de modelos. A revisão de `main` observada foi
`efdf08dd30bc72b1c7f60d1fdd087e3e4c25e6b1`; não se afirma que a página publicada
corresponda exatamente a esse commit. Números de outros aparelhos não foram usados
como projeção para o aparelho do autor.

<a id="f20"></a>
**F20 — scikit-learn. TimeSeriesSplit.**
[Documentação oficial](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
Consultada referência de divisão temporal, especialmente ordem, gap e hipóteses sobre
amostragem. A implementação AEMA ainda terá de tratar janelas, irregularidade e rótulos.

<a id="f21"></a>
**F21 — River. progressive_val_score.**
[Documentação oficial](https://riverml.xyz/latest/api/evaluate/progressive-val-score/).
Referência para avaliar antes de aprender e considerar atraso de resultados;
não implica dependência já adicionada ao AEMA.

<a id="f22"></a>
**F22 — River. ADWIN.**
[Documentação oficial](https://riverml.xyz/latest/api/drift/ADWIN/).
Referência de detecção de deriva. Não foi implementada ou calibrada no projeto.

## Triagem complementar

<a id="f23"></a>
**F23 — Google DeepMind. Gemma 4 model card.**
[Documento oficial](https://gemma.ai/models/gemma-4/model-card/).
Consultada a distinção entre parâmetros efetivos e totais nos modelos E2B/E4B.
Alternativa fora da prioridade inicial; não avaliada em execução.

<a id="f24"></a>
**F24 — Qwen. Catálogo oficial de modelos.**
[Catálogo do produtor](https://huggingface.co/Qwen/models).
Triagem de novidades e de famílias/tarefas. Página dinâmica, não inventário exaustivo
congelado; não sustenta a afirmação de que outro candidato adequado inexiste.

## Evidência local e decisões do autor

- Código inspecionado: [`mobile.py`](../../src/aema/mobile.py),
  [`models.py`](../../src/aema/models.py), [`catalog.py`](../../src/aema/catalog.py),
  [`CaptureService.java`](../../android/app/src/main/java/org/aema/capture/CaptureService.java),
  [`IntervalPlan.java`](../../android/app/src/main/java/org/aema/capture/IntervalPlan.java)
  e metadados do pacote. Base anterior à pesquisa: commit
  `2641a87b3d46a466f07ee983ed69d1072bcee347`.
- Manual existente: [contratos](../projeto/05-DADOS-E-CONTRATOS.md),
  [metodologia](../projeto/02-METODOLOGIA.md) e [estado](../STATUS.md).
- Requisitos do autor, nesta conversa em 24/11/2026: S25 Plus/One UI 9, meta de
  6 GB, componentes e aplicativos, inferência offline, treinamento maior no computador
  por transferência local e horizonte de seis horas. Informações declaradas, não
  características verificadas por ADB ou benchmark.

As datas/versões são um registro da consulta. Uma futura mudança de modelo, coleta,
licença ou objetivo exige atualizar a análise; os resultados anteriores devem ser
preservados com seu contexto.
