# 2. Modelos pequenos e execução Android

[Índice](README.md) · [Dados e treinamento](03-DADOS-TREINAMENTO-E-VALIDACAO.md) · [Fontes](FONTES.md)

**Consulta: 24/11/2026.** Tamanhos e capacidades abaixo são declarados pelos produtores;
não são medições do AEMA. A seleção é uma lista curta fundamentada, não um ranking
exaustivo de todos os modelos disponíveis.

## Candidatos

| Candidato / fonte | Escala declarada | Papel candidato | Restrição decisiva |
|---|---:|---|---|
| [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) [F11] | 0,6B | Primeiro explicador a avaliar; também braço de previsão direta. | Qualidade real em português e no domínio ainda desconhecida. |
| [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) [F12] | 0,8B, modelo de linguagem; há encoder visual | Concorrente mais recente na faixa sub-1B. | Arquitetura híbrida e conversão/runtime específicos; usar só texto. |
| [Gemma 3 270M IT](https://huggingface.co/google/gemma-3-270m-it) [F13] | 270M | Testar especialização extremamente compacta. | Não inferir qualidade em português a partir da família; precisa teste. |
| [FunctionGemma 270M](https://huggingface.co/google/functiongemma-270m-it) [F14] | 270M | Selecionar ações por identificadores estruturados. | Fabricante indica especialização posterior e não recomenda diálogo direto. |
| [Gemma 3 1B IT](https://huggingface.co/google/gemma-3-1b-it) [F15] | 1B | Alternativa de comparação na faixa de 1B. | Mais pesos; justificar o ganho com medição local. |
| [SmolLM2 360M Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) [F16] | 360M | Controle pequeno para geração/sumarização. | Model card informa foco principal em inglês; português é risco de seleção. |
| [Chronos-Bolt Tiny](https://huggingface.co/amazon/chronos-bolt-tiny) [F17] | 9M | Concorrente temporal numérico, não LLM conversacional. | Atribuição e recomendações exigem outros módulos; portabilidade não verificada. |

[F11]: FONTES.md#f11
[F12]: FONTES.md#f12
[F13]: FONTES.md#f13
[F14]: FONTES.md#f14
[F15]: FONTES.md#f15
[F16]: FONTES.md#f16
[F17]: FONTES.md#f17

As revisões exatas dos sete repositórios estão em [fontes.json](fontes.json).
Nenhum desses model cards demonstra especialização em BatteryStats do AEMA.
Chronos-Bolt possui sucessor, mas sua variante Tiny foi mantida na triagem pelo tamanho;
isso não presume que seja a melhor solução temporal atual. [F17](FONTES.md#f17)

### Ordem proposta

Qwen3-0.6B é o primeiro candidato por combinar tamanho pequeno, pesos Apache 2.0 e
suporte documentado a uso local. Desabilitar o modo de raciocínio prolongado e limitar
a resposta é uma configuração a avaliar, não garantia de custo ou qualidade.
[F11](FONTES.md#f11)

Qwen3.5-0.8B deve ser comparado no mesmo corpus; o model card o direciona também a
ajuste específico e alerta sobre loops no modo de raciocínio. Não adotar seu contexto
máximo como orçamento móvel. [F12](FONTES.md#f12)

FunctionGemma é uma alternativa distinta: transformar fatos em uma ação do catálogo,
como `review_background_app`, e preencher a explicação por texto fixo. Essa hipótese
de uso é nossa; não exige que o modelo tenha acesso a comandos do sistema.
[F14](FONTES.md#f14)

### Triagem de famílias mais recentes e maiores

A família Gemma 4 inclui E2B, mas o card diferencia parâmetros efetivos de parâmetros
totais com embeddings. Por isso “E2B” não deve entrar na conta de memória como apenas
dois bilhões de pesos. Não é prioridade para a primeira faixa de 6 GB; pode servir
como comparador posterior. [F23](FONTES.md#f23)

O catálogo oficial Qwen foi consultado para verificar novidades. Modelos de outra
tarefa, como ASR ou moderação, e variantes grandes não entram na lista de assistentes
pequenos apenas por serem mais recentes. Não se afirma inexistência de outros modelos
adequados. [F24](FONTES.md#f24)

## Memória: estimativa de pesos não é RAM de execução

Para uma conta inicial, `bytes_pesos ≈ número_de_parâmetros × bits / 8`.
Valores decimais aproximados, usando os tamanhos nominais; não incluem metadados,
embeddings extras, tensores mantidos em outra precisão nem encoder visual.

| Escala nominal | Pesos ideais FP16 | Pesos ideais em 4 bits |
|---:|---:|---:|
| 270M | 540 MB | 135 MB |
| 360M | 720 MB | 180 MB |
| 0,6B | 1.200 MB | 300 MB |
| 0,8B | 1.600 MB | 400 MB |
| 1B | 2.000 MB | 500 MB |

Um arquivo GGUF Q4 ou um pacote `.litertlm` terá tamanho diferente dessa conta.
Na execução somam-se tokenizer, cache KV/estado recorrente, buffers, backend CPU/GPU,
interface, Python/Chaquopy/pandas já presentes, e eventualmente cópias de pesos.
RAM total de 6 GB não equivale a 6 GB livres para o AEMA.

O benchmark deve registrar tamanho do arquivo, PSS/RSS de todos os processos envolvidos,
memória de GPU quando disponível, pico de carregamento e comportamento sob pressão.
Falha por memória deve resultar em relatório por texto fixo, não em carregamentos
repetidos. Não usar os valores ideais como requisito mínimo de RAM.

## Runtimes a comparar

| Runtime | Evidência primária consultada | Avaliação proposta no AEMA |
|---|---|---|
| llama.cpp | Documentação Android apresenta binding nativo e importação de GGUF. [F18](FONTES.md#f18) | Primeiro caminho para protótipo CPU com JNI; medir integração e suporte do modelo exato. |
| LiteRT-LM | Documentação descreve execução Android e backends acelerados. [F19](FONTES.md#f19) | Comparar se houver artefato compatível e vantagem no hardware testado. |

Os benchmarks publicados pelo runtime não são resultados para o S25 Plus do autor,
nem para um Android genérico de 6 GB. Suporte a “Qwen” ou “Gemma” como família também
não comprova suporte a qualquer revisão, quantização e arquitetura dessa família.

Não instalar PyTorch/Transformers inteiros no telefone como pressuposto de produção.
O computador pode usá-los para experimentos; o app poderá consumir apenas o artefato
convertido e um runtime nativo. Árvores e regressões precisam de uma representação
portável com resultados equivalentes ao computador. Chronos exige prova própria de
conversão e execução; seu pequeno número de pesos não resolve isso automaticamente.

## Licenças e distribuição

Os cards consultados registram Apache 2.0 para Qwen3, Qwen3.5, SmolLM2 e Chronos-Bolt;
os três candidatos Gemma registram licença Gemma e acesso condicionado no hub.
As revisões e os estados de acesso estão no registro de fontes. [F11–F17](fontes.json)

Antes de distribuir pesos, registrar licença do modelo e da conversão, avisos exigidos,
origem e hashes. O estudo não aceita termos em nome do usuário nem baixa pesos gated.
Quantizar não remove condições de redistribuição. A escolha definitiva exige conferir
os termos do artefato distribuído; esta página não substitui essa conferência.

## Orçamento inicial proposto, sujeito ao piloto

| Item | Limite candidato de engenharia, ainda não aprovado por ensaio |
|---|---|
| Contexto do explicador | Até 1.024 tokens, incluindo regras e fatos; saída até 128 tokens. |
| Arquivo do explicador | Preferencialmente até 750 MiB; medir pacote final, não estimar só pelos pesos. |
| Memória | Pico agregado de PSS do app e auxiliares até 1,5 GiB no aparelho de 6 GB; registrar GPU separadamente. |
| Latência | Resposta completa p95 até 10 s no corpus definido; carga fria contabilizada à parte. |
| Energia | Medir mAh/Wh por relatório e excesso diário; só aprovar após orçamento definido no piloto. |

Esses números são limites candidatos para comparação, não medições nem promessa de
que qualquer candidato os cumpre. A quantidade de RAM por si só não resolve ABI,
versão mínima do Android, drivers, instruções de CPU ou restrições do fabricante.
O mínimo atual do coletor é API 26; o mínimo do futuro módulo de IA dependerá do runtime.

## Protocolo de benchmark físico

1. Fixar artefato/hash, runtime/commit, quantização, backend, threads e configuração.
2. Separar carga fria e quente; testar o mesmo corpus português com entradas pequenas,
   ausentes, conflitantes e fora de distribuição. Realizar piloto com dez repetições
   por configuração, ampliando a amostra se a variabilidade exigir.
3. Medir duração, primeiro token, p50/p95, falhas, memória, temperatura e energia;
   alternar a ordem das configurações e estabilizar brilho, rede, bateria e temperatura.
4. Repetir com aplicativos comuns abertos e sob pressão de memória; incluir aparelho
   real de 6 GB e outra família de SoC, além do S25 Plus. Emulador não substitui energia.
5. Publicar erros, dados ausentes e intervalo de incerteza. Reavaliar quantização com
   as mesmas perguntas e rótulos; comparar sempre com texto fixo sem LLM.

Nenhuma dessas execuções ocorreu nesta entrega documental. O pacote de treinamento,
os pesos, o hardware e os resultados continuam pendentes.
