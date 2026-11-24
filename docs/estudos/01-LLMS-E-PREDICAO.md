# 1. LLMs, previsão numérica e aprendizado pessoal

[Índice dos estudos](README.md) · [Modelos](02-MODELOS-E-EXECUCAO-LOCAL.md) · [Fontes](FONTES.md)

**Estado:** revisão exploratória e proposta, 24/11/2026. Nenhum modelo foi treinado ou
comparado com dados reais do AEMA nesta pesquisa.

## Pergunta e objeto

Como prever, com baixo custo de execução, a carga consumida e o ranking de recursos
nas próximas seis horas de uso de um telefone, personalizar o modelo e transformar
previsões em sugestões verificáveis?

O objeto proposto passa a incluir o **erro de previsão futura**, a qualidade da
atribuição por componente/aplicativo, o ganho da personalização e o custo energético
da própria IA. A validação elétrica do manual continua como linha de sustentação.
Uma previsão consistente com BatteryStats não comprova consumo físico verdadeiro.

## Quatro perguntas que exigem evidências diferentes

| Pergunta | Método candidato | Limite |
|---|---|---|
| O que mais consumiu no período passado? | Deltas válidos e ranking das atribuições do Android. | É descrição retrospectiva, não previsão. |
| O que deve consumir mais nas próximas 6 h? | Modelo supervisionado/temporal com dados disponíveis na origem. | Depende do comportamento futuro e da qualidade dos rótulos. |
| Quanto economizaria ao alterar uma configuração? | Ensaio controlado ou modelo causal validado. | Correlação e importância de variável não identificam economia causal. |
| Como explicar o resultado? | Texto por modelo fixo ou pequeno LLM ancorado em fatos. | Fluência não comprova exatidão nem causalidade. |

O telefone inteiro e os aplicativos oferecem dois eixos de análise do mesmo consumo.
Somar “CPU + tela + aplicativo A” pode contar duas vezes o trabalho do aplicativo A.
Um UID compartilhado também não permite dividir automaticamente sua carga entre todos
os pacotes. Essas restrições vêm dos contratos locais, em
[`models.py`](../../src/aema/models.py) e [dados do projeto](../projeto/05-DADOS-E-CONTRATOS.md).

## O que significa alimentar e ensinar um modelo

| Estratégia | O que muda | Uso proposto |
|---|---|---|
| Contexto no prompt | A entrada da execução; não modifica pesos. | Enviar resumo de previsões e ações permitidas ao explicador. |
| Consulta a memória local | Recupera fatos/regras; não equivale a treinar. | Preferências, limitações e histórico de intervenções. |
| Treinamento supervisionado numérico | Coeficientes, árvores ou pequena rede. | Aprender a relação entre histórico e carga futura observada. |
| Fine-tuning supervisionado do LLM | Pesos ou adaptadores. | Aprender formato, vocabulário e seleção de recomendações fundamentadas. |
| Aprendizado incremental | Atualiza um estimador quando chega o resultado real. | Personalizar com controle de deriva e possibilidade de voltar à versão anterior. |

Não se propõe pré-treinar um LLM do zero usando um telefone: a coleta pessoal tem outra
escala e outro propósito. O núcleo preditivo poderá começar sem pesos pessoais, usar
um baseline simples e ser ajustado conforme surgem janelas válidas. “Melhorar com o
tempo” será demonstrado por avaliações futuras, não presumido por ter mais registros.

## Estudos relacionados

### Consumo e recomendação antes dos LLMs

**PowerBooter/PowerTutor (Zhang et al., 2010)** constrói modelos a partir de estados de
componentes e atividade, com caracterização específica do aparelho. Isso sustenta a
necessidade de calibrar por hardware, em vez de transferir coeficientes de CPU e tela
como universais. O trabalho antecede o Android atual; não comprova compatibilidade ou
exatidão no S25 Plus. [F04](FONTES.md#f04)

**Carat (Oliner et al., 2013)** relaciona observações de dispositivos a diagnóstico e
recomendações com incerteza. Serve de antecedente para recomendações baseadas em
evidência e comparação de perfis. Sua arquitetura colaborativa e seus resultados não
são evidência de que um único telefone offline alcançará o mesmo benefício.
[F03](FONTES.md#f03)

### Evidência a favor de investigar LLMs

**LLMTime (Gruver et al., NeurIPS 2023)** representa séries como números em texto e
avalia previsão sem ajuste específico. O trabalho também aponta a influência da
tokenização e da calibração. Justifica incluir um braço experimental de previsão
direta; não demonstra o resultado para um modelo sub-1B nem para bateria Android.
[F05](FONTES.md#f05)

**Qiu et al. (2026, preprint, versão 2)** relatam benefícios em avaliação de grande
escala, incluindo mudanças de domínio, e discutem alinhamento entre dados temporais e
LLMs. Os autores contestam conclusões negativas amplas. O volume e as condições desse
estudo diferem muito de dados de um telefone; a revisão aqui consultou o resumo e os
metadados, não reproduziu seus experimentos. [F07](FONTES.md#f07)

### Evidência para baselines menores

**Tan et al. (NeurIPS 2024)** fazem ablações de três métodos temporais baseados em LLMs;
remover ou simplificar o LLM frequentemente preserva ou melhora desempenho no recorte
avaliado. O resultado exige comparar custo e ganho, sem concluir que nenhum LLM possa
funcionar em qualquer cenário. [F06](FONTES.md#f06)

**Grinsztajn et al. (2022)** encontram forte desempenho de árvores em benchmarks de
dados tabulares. A telemetria com atributos agregados justifica esse baseline, mas o
benchmark não é de bateria nem comprova superioridade atual para o AEMA.
[F08](FONTES.md#f08)

## Alternativas experimentais

| Braço | Modelo | Função e razão da comparação |
|---|---|---|
| B0 | Persistência e média histórica por faixa horária | Revelar quanto do resultado já é explicado por hábitos. |
| B1 | Regressão regularizada ou incremental | Pequeno custo; adaptação pessoal e inspeção de coeficientes. |
| B2 | Árvores com boosting limitadas em tamanho | Não linearidades e interações; comparar com B1 antes de portar. |
| B3 | Rede temporal pequena ou Chronos-Bolt Tiny | Explorar dependências temporais; não é um assistente de linguagem. |
| B4 | LLM pequeno com saída numérica estruturada | Testar a hipótese original diretamente, com o mesmo corte de dados. |

O explicador é outro experimento: modelo de texto fixo versus LLM com os mesmos fatos.
Separar experimentos evita atribuir ao LLM um ganho produzido pelo preditor numérico.
Não se exige testar toda combinação antes do piloto: B0/B1 precedem os braços caros.

## Recomendação técnica e condições para revê-la

Começar com B0/B1 e dados íntegros. Comparar B2 quando houver diversidade de janelas.
Executar o explicador apenas quando solicitado ou ao atualizar o relatório, com
limites de tokens e liberação de memória ao terminar. A personalização inicial deve
ajustar o preditor, não reescrever diariamente os pesos do LLM.

Se B4 demonstrar erro menor, saídas válidas, consumo compatível e estabilidade em
aparelhos de 6 GB, ele poderá assumir mais responsabilidades. Se o LLM não melhorar
a compreensão das sugestões, manter texto fixo é um resultado válido do estudo.
Essa decisão é inferência de engenharia, não conclusão direta de um artigo.

## Hipóteses candidatas

| ID | Hipótese que o protocolo poderá testar |
|---|---|
| H-IA-01 | O melhor preditor reduz o erro de 6 h frente ao melhor baseline temporal no teste futuro. |
| H-IA-02 | A adaptação pessoal reduz erro frente ao mesmo modelo congelado, sem usar resultados futuros. |
| H-IA-03 | Um LLM pequeno melhora compreensão/adequação da explicação sem inventar fatos ou elevar demais o custo. |
| H-IA-04 | Recomendações selecionadas reduzem consumo em comparações controladas, preservando a utilidade escolhida. |
| H-IA-05 | O pipeline mantém seus limites de erro e recursos em aparelhos não usados no ajuste. |

Margens, tamanho amostral e regras de parada devem ser definidos após o piloto e antes
do teste final. Não há evidência atual para aceitar essas hipóteses ou prometer uma
porcentagem de precisão.
