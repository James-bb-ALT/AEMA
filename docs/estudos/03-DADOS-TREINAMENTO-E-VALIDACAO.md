# 3. Dados, treinamento e validação

[Índice](README.md) · [Plano](04-ARQUITETURA-E-PLANO-EXPERIMENTAL.md) · [Fontes](FONTES.md)

**Protocolo candidato, 24/11/2026.** As estruturas e rotinas desta página são propostas;
não são formatos aceitos pelo software 1.0.0 nem experimentos já executados.

## Definição do problema supervisionado

Na origem `t`, usar apenas informações disponíveis até `t` para prever a carga de
`[t, t + 6 h]`. Há dois casos distintos: previsão de uso habitual, sem conhecer a rotina
futura, e previsão condicional a um cenário declarado, como “continuar o vídeo”.
Não misturar os erros dos dois casos. Um cenário não é garantia de que o usuário o seguirá.

| Saída | Rótulo candidato | Como apresentar a evidência |
|---|---|---|
| Carga total futura | Diferença válida de contador de carga ou integração elétrica. | Separar fuel gauge de referência externa calibrada. |
| Carga por componente | Delta válido da atribuição BatteryStats, onde houver. | “Estimativa segundo o Android”, até validação independente. |
| Carga por aplicativo/UID | Delta de atribuição por UID e mapa de pacotes temporal. | Preservar UID compartilhado; não inventar divisão por pacote. |
| Maior consumidor | Ranking dentro do mesmo eixo e da mesma janela. | Exibir empates e incerteza quando diferenças forem pequenas. |
| Economia por intervenção | Diferença em ensaio controlado com condições comparáveis. | Sem ensaio, descrever possibilidade, sem percentual garantido. |

No AOSP, perfis de componentes podem combinar corrente de referência com tempo de
atividade; dados de chipset também podem participar. Isso não constitui uma medição
externa independente. [F01](FONTES.md#f01)

`BatteryManager` expõe contador de carga em µAh e propriedades de corrente em µA,
com semântica de sinal e valores sentinela para propriedades indisponíveis. A consulta
dessas APIs é **uma extensão proposta**; o AEMA não coleta essas propriedades
numericamente hoje. Verificar suporte, escala, atualizações e comportamento no aparelho.
[F02](FONTES.md#f02)

Quando o contador representar carga restante e a janela for exclusivamente de descarga:

```text
charge_used_mah = (charge_remaining_uah_start - charge_remaining_uah_end) / 1000
average_current_ma = charge_used_mah / duration_hours
```

Uma janela com carga, reset ou correção do fuel gauge exige tratamento específico;
não aplicar a fórmula cegamente nem transformar resultado negativo em zero.
Percentual de bateria é um rótulo grosseiro e não equivale a mAh sem caracterização.
Energia em Wh exige tensão e integração compatíveis; mAh é carga, não potência.

Treinar contra atribuições do Android permite aprender a **prever esse estimador**.
Validar contra os mesmos valores não comprova que o sistema descobriu o consumo físico
de CPU, RAM ou Wi-Fi. Um sensor total tampouco identifica sozinho todas as parcelas.

## Auditoria necessária dos dados existentes

O núcleo atual oferece contagens, tempos, tráfego, wakelocks e estimativas, dependendo
dos campos realmente presentes. O [catálogo completo](../CATALOGO-COMPLETO.md) e a
[semântica dos arquivos](../projeto/05-DADOS-E-CONTRATOS.md) são a referência local.
Não assumir brilho, frequência detalhada de CPU, temperatura, corrente, eventos de uso
ou matriz aplicativo × componente já disponíveis como séries normalizadas.

Antes de treinar, produzir um relatório por aparelho/build: campos presentes, unidade,
missingness, frequência efetiva, período coberto, resets, duplicatas, atrasos, UIDs,
pacotes e significado de cada fonte. Valor ausente permanece ausente, com máscara e
motivo; não é zero. Um `0` atribuído à RAM não comprova ausência de consumo físico.

## Construção de janelas

1. Verificar hashes, schema e parsing da captura; manter rejeições e motivo.
2. Agrupar por instalação/dispositivo, usuário Android, build, métrica e entidade.
   Identificar época de boot e de reset BatteryStats; relógio monotônico isolado não
   identifica todos os resets, e o coletor ainda precisa de marcadores suficientes.
3. Ordenar por tempo, eliminar duplicatas sem criar observações novas e comparar apenas
   contadores compatíveis. Taxas usam a duração real, não seis horas presumidas.
4. Aplicar delta somente a campos classificados como contadores acumulados compatíveis.
   Gauges, níveis, estados e estimativas recalculadas precisam de regra própria.
   Delta negativo, troca de UID, reset ou captura incompatível gera exclusão/segmentação.
5. Formar atributos passados e rótulos futuros separados; registrar origem dos arquivos,
   início/fim efetivos, disponibilidade do rótulo e regra de aceitação.

Nem todo mAh acumulado é monotônico: revisões do estimador podem alterar parcelas.
Rótulos por componente precisam de validação dessa semântica antes da subtração.
Não interpolar uma captura perdida e chamá-la de observação; não preencher lacunas com
texto gerado por LLM. Capturas de comandos distintos também não são simultâneas:
registrar e limitar a defasagem entre fontes.

### Seis horas de arquivo versus frequência de amostragem

O requisito confirmado é salvar novos arquivos a cada seis horas. Isso pode coexistir,
em uma etapa futura, com amostras mais frequentes guardadas dentro desses arquivos.
Essa coleta adicional ainda não foi autorizada como implementação nem adicionada.

Proposta de piloto: comparar o snapshot de 6 h com amostras leves de 5 e 15 minutos,
somente quando o Android permitir, medindo cobertura e overhead. Não manter wakelock
contínuo nem solicitar alarmes exatos a cada amostra por pressuposto. Restrições de
segundo plano, sono e custo podem inviabilizar a frequência pretendida. Evitar executar
um `dumpsys` pesado em cada ponto sem medir seu impacto.

Com quatro pontos regulares por dia, 28 dias fornecem no máximo aproximadamente
112 intervalos de 6 h, antes de falhas e exclusões. Milhares de métricas ou linhas
por UID não viram milhares de janelas independentes. Séries mais frequentes também
continuam correlacionadas. O piloto define necessidade amostral; quatro semanas não
são garantia de suficiência.

## Contrato candidato de dataset de aprendizado

| Grupo | Campos mínimos propostos |
|---|---|
| Identidade contextual | `device_context_id`, usuário, época de UID/pacote, build, versão de coleta/parser. |
| Tempo | `forecast_origin_utc`, início/fim dos atributos, início/fim do alvo, `label_available_at`. |
| Atributos | Valores, unidades, máscaras, durações reais, identificadores de transformações. |
| Rótulos | Valor, unidade, eixo total/componente/UID, método Android/fuel gauge/referência, qualidade. |
| Proveniência | Capturas/hashes, época de contador, exclusões e divisão de treino/validação/teste. |

Treinar com recursos como taxas históricas, tempo de tela conhecido, tráfego passado,
CPU/wakelocks passados, hora/dia, consumo recente e contexto disponível de forma lícita.
Brilho, temperatura, sinal e outros atributos só entram se forem coletados e validados.
Pacote/UID deve ser contextualizado; mesmo UID em outro aparelho não significa o mesmo app.

Evitar vazamento: consumo medido no período futuro, tempo de tela futuro realizado,
ranking do próprio alvo, normalização ajustada no dataset completo e imputação que veja
o futuro não podem ser atributos do preditor habitual. Atribuição passada pode ser
atributo, com identificação explícita do método que a produziu.

## Treinamento no computador

Primeiro, persistência e média por faixa horária. Depois, regressão regularizada com
atributos de histórico. Árvores limitadas em profundidade/tamanho, pequena rede temporal
e os demais braços entram somente se houver dados e vantagem sobre os baselines.
Fixar versões de bibliotecas, semente, partições e orçamento de busca.

Guardar o estimador do computador e a representação exportável. Comparar ambos num
conjunto de vetores de referência antes de carregar no app; tolerância numérica e
tratamento de ausentes são parte do contrato. Não supor que pickle de uma biblioteca
Python seja um formato móvel adequado.

### Especialização do LLM

Se os testes de explicação justificarem fine-tuning, usar pares revisados de fatos e
respostas/ações corretas em português, com casos de dados insuficientes e abstenção.
Os valores devem vir do preditor/regras; não criar “verdade elétrica” por geração.
Exemplos sintéticos ajudam a testar formato, mas não comprovam acurácia em campo.

LoRA aprende uma atualização de baixa dimensão mantendo o modelo-base congelado.
[F09](FONTES.md#f09) QLoRA combina adaptação e base quantizada para economizar memória
de treinamento, mas seus resultados em GPU não estabelecem que o ajuste caberá em
qualquer telefone. [F10](FONTES.md#f10) O treinamento maior foi aceito no computador;
GPU/VRAM disponíveis ainda não foram informadas. Medir a necessidade do candidato real
antes de escolher rank, batch ou prometer horas de treinamento.

Separar exemplos por cenário, período e dispositivo quando aplicável. Não colocar
paráfrases do mesmo caso em treino e teste. Avaliar base, ajuste, quantização e texto
fixo separadamente. Se houver professor maior para gerar exemplos, validar as respostas
e registrar origem/licença; API externa não é requisito nem autorização de envio.

## Aprender com o tempo sem se autoenganar

Na origem, salvar previsão e versão antes de observar o alvo. Ao terminar a janela,
avaliar contra um rótulo válido; só então atualizar o estimador pessoal. A avaliação
progressiva com rótulos atrasados é o padrão conceitual pertinente.
[F21](FONTES.md#f21)

Manter um modelo vigente e um candidato. Comparar o adaptado com uma cópia congelada
nas mesmas origens futuras. Promover o candidato somente após critério registrado,
manter histórico e permitir retorno. Mudanças de build, bateria, hábitos ou versões
dos aplicativos podem causar deriva. Um detector como ADWIN é candidato de pesquisa,
não correção automática ou garantia de melhoria. [F22](FONTES.md#f22)

Atualizações leves podem ser locais, em condição térmica apropriada e com orçamento
limitado; reajustes maiores usam o computador. Isso é arquitetura proposta. Não alimentar
o treino com previsões próprias como se fossem rótulos; feedback “aceitei a sugestão”
não mede mAh economizados. Registrar a intervenção porque ela muda a distribuição futura.

## Avaliação e critérios de sucesso

Divisão temporal, com treino anterior à validação e teste final posterior. Ajustes de
atributos e hiperparâmetros veem somente treino/validação. O corte deve impedir que
um alvo de treino termine depois da origem avaliada; eliminar sobreposição de alvos
no limite e considerar a dependência entre janelas. `TimeSeriesSplit` é referência,
não uma solução automática para timestamps irregulares ou rótulos de 6 h.
[F20](FONTES.md#f20)

| Dimensão | Métricas e cuidados |
|---|---|
| Carga futura | MAE/RMSE em mAh; erro médio assinado; WAPE agregado com denominador não nulo. Evitar MAPE em alvos próximos de zero. |
| Ranking | Acerto do maior consumidor, recall@3 e correlação de ranking por eixo. Definir empates/entidades ausentes antes do teste. |
| Incerteza | Cobertura e largura de intervalos de previsão; não confundir com incerteza do instrumento. |
| Explicações | Validade do formato, fidelidade a números/entidades, ações permitidas, abstenção e avaliação humana em português. |
| Custo e benefício | Memória, tempo, energia da IA/coleta e economia por intervenção controlada; comparar benefício líquido. |

Reportar por aparelho, condição, componente e faixa de uso, não só uma média global.
Comparações pareadas usam as mesmas origens; intervalos por reamostragem precisam
respeitar blocos temporais, por exemplo dias. Bootstrap de linhas por UID como se
independentes produz confiança enganosa. Com poucos dias, declarar o limite.

Como alvo inicial **proposto**, investigar redução relativa de MAE de ao menos 10%
frente ao melhor baseline, com intervalo que sustente melhora e custo compatível.
Esse número não foi alcançado, não define precisão absoluta aceitável e será revisto
no piloto. As tolerâncias de erro em mAh, ranking e economia líquida ainda precisam
ser fixadas antes do teste final. Para explicações, exigir ausência de números ou
ações não fundamentados no corpus de aceite, sem tratar taxa observada zero como
garantia de ausência futura.

O teste no S25 Plus avalia personalização de um caso. “Qualquer telefone com 6 GB”
exige aparelhos reais, fabricantes/SoCs distintos e teste com dispositivos não vistos.
O resultado correto em ambiente não suportado pode ser abstenção ou relatório reduzido.
