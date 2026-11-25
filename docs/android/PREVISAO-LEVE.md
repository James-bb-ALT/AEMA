# Previsão leve offline — AEMA 3.0.0

O app agora tem **Previsão leve (6 horas)**. A inferência Ridge roda em Java, sem Qwen,
Python, JNI ou framework de rede neural nessa etapa numérica. A preparação de capturas
continua usando o parser Python compartilhado; o APK não se tornou um app de poucos KB.
Esta é uma funcionalidade experimental, sem precisão validada em telefone físico.

## Uso no telefone

1. Abra **Previsão leve (6 horas)** e toque em **Executar demonstração sintética** para
   testar instalação e cálculo sem Shizuku, histórico ou pesos de LLM. A tela identifica
   explicitamente dados sintéticos. Isso não instala um modelo pessoal.
2. Para previsão pessoal, transfira os ZIPs do app ao computador, treine conforme abaixo
   e transfira o JSON de volta por arquivo local. Toque em **Importar modelo pessoal JSON**.
   O JSON tem limite de 256 KiB; substituição atômica preserva o modelo anterior em
   importação inválida/interrompida. Modelos declarados sintéticos são recusados nesse fluxo.
3. Mantenha a coleta automática de seis horas. Cada coleta tenta atualizar a previsão;
   sem modelo ou histórico válido há um relatório explícito de abstenção. Também é
   possível usar **Prever com histórico do telefone** com uma captura recente.

O relatório lista tela, CPU, Wi-Fi, rede móvel e os UIDs selecionados no treino.
UID é uma atribuição do Android: um UID compartilhado não permite dividir o consumo
por pacote. O ranking cobre **somente os alvos modelados**, não todos os apps instalados.
A soma exibida é dos quatro componentes, não o total completo da bateria. Componentes
e UIDs se sobrepõem e não são somados entre si. Sugestões são textos locais associados
a valores previstos positivos; não são uma prova de causa ou de economia.

## Treino pessoal no computador

Use um ambiente com o pacote AEMA 3.0.0 e suas dependências. Preserve os nomes originais
dos arquivos coletados pelo app; a ordem de leitura é a ordem lexical dos nomes UTC.
Escolha explicitamente 1–12 UIDs presentes nos relatórios (incluindo perfis Android).
Exemplo de comando; substitua pasta e UIDs pelos seus:

```powershell
python -m aema.forecast_training --captures "D:\AEMA\capturas" --uids 10001 10042 --output "D:\AEMA\ridge-pessoal.json"
```

O comando verifica o mesmo ZIP/dataset e hashes usados pela leitura do projeto, além
de estado de bateria, relógio monotônico, boot e época de reset. Exige pelo menos
64 exemplos rotulados **após** os oito lags iniciais; são necessárias no mínimo 73
capturas sem interrupção (~18 dias), e normalmente mais devido às exclusões. Isso é
um mínimo de engenharia, não garantia de precisão. Aceita no máximo 1.024 capturas.

São reservados os últimos 16 exemplos para teste, os 16 anteriores para validação e
o restante para treino. Alpha é escolhido entre 0,1/1/10/100 na validação. O modelo
exportado é reajustado em treino + validação; os rótulos de teste ficam de fora dos
pesos. O resumo mostra MAE de teste e MAE da quarta janela válida anterior, médios entre alvos.
Não se declara o modelo aprovado para seu uso só porque o comando conseguiu treiná-lo.
Se o resultado não for satisfatório, preserve o baseline e colete mais dados.

O JSON contém pesos FP32 serializados em texto, normalizadores, ordem dos alvos,
contrato de atributos, horizonte, versão, identificação por hash da instalação/build
e métricas. Hash garante integridade rastreável, não autenticidade ou qualidade do
treinamento declarado. Não importa pickle nem executa código fornecido pelo arquivo.
Reinstalação ou mudança de build altera o vínculo; será necessário treinar novamente.

Não há treino automático dos pesos no telefone. Para reajustar, repita o processo no
computador e importe o novo JSON. O app preserva os ZIPs e modelos usados nas previsões
históricas para permitir comparar versões depois.

## Quando o app se abstém

Para cada previsão pessoal nova, são exigidas **oito janelas válidas nos últimos 14 dias**, com todos os alvos disponíveis. São
inspecionadas até as últimas 64 capturas; cada par adjacente deve ser válido por si.
A janela mais recente também deve ser válida. Intervalos rejeitados não são atravessados
nem preenchidos com zero; janelas válidas anteriores podem ser reaproveitadas. São recusados:

- Captura/coleta/parsing incompletos, hashes divergentes, componente ou UID ausente.
  Ausência não vira zero. Estimativas negativas ou duplicadas são recusadas.
- Boot/reset diferente entre os extremos de uma janela, instalação/build diferente do modelo, contadores
  que diminuem ou campo `Start clock time` não reconhecido no relatório.
- Intervalo fora de 5,7–6,3 horas, diferença entre relógios UTC/monotônico acima de
  30 segundos, captura que levou mais de dois minutos ou tempo monotônico ausente.
- Estado de bateria nos extremos diferente de discharging (3) ou not charging (4).
  Isso não prova que não houve carga dentro do intervalo; a época de reset e a
  monotonicidade são verificadas também. A atribuição continua sendo do BatteryStats.
- Última captura futura ou com mais de 30 minutos para gerar uma previsão nova.
  Um relatório já salvo mostra seu período de origem/fim; se encerrado, a tela avisa.
- Modelo ou capturas declarados sintéticos no caminho pessoal.

O manifesto 1.0 ganha o campo aditivo `forecast_boot_count`, obtido do Android; sua
ausência nunca impede salvar a captura. Capturas antigas sem esse campo continuam
legíveis pelo parser/LLM, mas não entram na previsão. Se o fabricante bloquear esse
metadado ou o formato de reset, a previsão se abstém. Coletas manuais em intervalos
curtos invalidam os pares afetados; não alteramos os horários para inventar janelas.
Carga/reboot frequente pode reduzir o número de janelas elegíveis.

Os deltas válidos são normalizados pela duração real para um equivalente de seis horas.
Isso não os transforma em medidas elétricas exatas. O alvo é a estimativa futura do
Android, não corrente/potência medidas por referência externa.

## Contrato e implementação

`aema_ridge_6h/1.0`, atributo `valid_lag1_lag4_mean8_calendar_age_utc_v1`, horizonte 6 h:

- Quatro componentes em ordem fixa (screen, cpu, wifi, mobile_radio), seguidos por
  1–12 UIDs explícitos. Até 16 saídas; `3 × saídas + 5` atributos.
- Última janela, quarta janela anterior, média das últimas oito para cada alvo;
  seno/cosseno de hora UTC, indicador de fim de semana, idade da última janela e
  extensão do histórico em horas. Quarta janela válida não significa necessariamente
  o mesmo horário do dia anterior. Só histórico anterior à
  origem da previsão e calendário conhecido.
- Normalização do treino, intercepto e produto matricial Ridge; saída negativa
  limitada a zero. Entradas, pesos e saídas não finitos são recusados.
- Dados e preparação: [`forecast.py`](../../src/aema/forecast.py).
  Treino: [`forecast_training.py`](../../src/aema/forecast_training.py).
- Android: [`RidgeEngine`](../../android/app/src/main/java/org/aema/capture/RidgeEngine.java),
  [`ForecastModel`](../../android/app/src/main/java/org/aema/capture/ForecastModel.java),
  [`ForecastStore`](../../android/app/src/main/java/org/aema/capture/ForecastStore.java),
  [`ForecastRunner`](../../android/app/src/main/java/org/aema/capture/ForecastRunner.java) e
  [`ForecastActivity`](../../android/app/src/main/java/org/aema/capture/ForecastActivity.java).

## Armazenamento e debug

`forecast-result.json` guarda a última tentativa pessoal; `forecast-demo-result.json`
guarda a demonstração separadamente. Uma previsão pessoal bem-sucedida cria também
`forecasts/forecast_<tempo>_<uuid>.zip`, com `forecast.json` e `model.json`. O relatório
contém período, modelo por hash, hashes de todos os ZIPs usados nas oito janelas, valores previstos e
tempos. É um registro prospectivo: não será reescrito quando chegar o resultado real.

Esse ZIP é copiado para a pasta SAF já escolhida. Falha do provedor mantém o original
privado; **Copiar ZIPs e previsões para a pasta** tenta novamente. Os brutos continuam
nos ZIPs de captura próprios. Modelos e relatórios contêm UIDs e informações privadas;
o provedor da pasta pode sincronizar por conta própria.

**Exportar relatório exibido** exporta o JSON da tela, inclusive sua marcação sintética.
Debug existente registra etapa forecast, motivo de abstenção e tempos. `prediction_ms`
é apenas o produto numérico; `preparation_ms` inclui leitura/verificação de histórico,
mas não a inicialização do runtime Python. O debug não recebe vetor de atributos ou brutos. Exportar
o relatório completo é diferente de exportar debug e inclui previsões por UID.

## Simulação e evidências

[Simulação da integração 3.0.0](../estudos/08-IMPLEMENTACAO-E-SIMULACAO-RIDGE.md) descreve
96 capturas sintéticas pelo parser real, treino/exportação, teste reservado e paridade
no emulador. Demonstração incluída tem 144 pesos/bias (576 bytes em FP32 teórico);
o JSON completo com metadados/entradas ocupa alguns KB. O app não inclui pesos Qwen
na distribuição padrão desta release; a tela LLM opcional continua disponível.

Não houve portabilidade de todos os parsers para Java. O app ainda embute Python/pandas
e bibliotecas nativas existentes; peso do preditor e tamanho total do APK são coisas
diferentes. Não houve validação no S25 Plus, ensaio elétrico, medição de energia,
transferência entre fabricantes ou garantia de precisão com os dados do usuário.
