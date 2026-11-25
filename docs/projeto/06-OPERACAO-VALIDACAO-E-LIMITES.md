# 6. Operação, validação, manutenção e limites

## Operação e evidências da etapa 3.0.0

A previsão Ridge experimental, treino no computador e demonstração estão implementados.
[Guia operacional](../android/PREVISAO-LEVE.md) e [simulação documentada](../estudos/08-IMPLEMENTACAO-E-SIMULACAO-RIDGE.md)
registram os comandos, exclusões, testes e limites. O modelo pessoal exige novos dados
válidos; o exemplo sintético não é instalado como preditor pessoal. Aprendizado automático
no telefone, ensaios elétricos, economia e generalização permanecem pendentes.

Nova etapa de release: app/pacote/documentação 3.0.0. Dependências e contratos existentes
não alterados são preservados. A classificação do proprietário orienta esse incremento.

[Índice](../README.md) · [Anterior](05-DADOS-E-CONTRATOS.md) · [Próximo](07-REFERENCIAS-E-GLOSSARIO.md)

## 6.1 Preparar o host

Execute os comandos a partir da raiz do repositório. Python 3.10+ é requisito do
pacote; Python 3.13 é necessário para reproduzir a build Android atual.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m aema --help
```

O modo editável vincula o ambiente a `src/`, evitando continuar a usar uma cópia antiga
do pacote instalada em `site-packages`. Depois de mudar metadados/dependências, reinstale
o pacote. Confirme a origem com `python -c "import aema; print(aema.__file__)"`.

## 6.2 Demonstração reproduzível, sem dados privados

```powershell
.venv\Scripts\python -m aema demo --fixtures tests/fixtures --output-root demo-output
.venv\Scripts\python -m aema.validation docs/examples/ensaios-sinteticos.csv
.venv\Scripts\python -m aema.study docs/examples/protocolo-sintetico.json docs/examples/ensaios-sinteticos.csv
```

O demo padrão interpreta cinco registros check-in, três registros TXT e três relações
de pacotes, resultando em 88 métricas canônicas. Ele exporta e reimporta o dataset e
declara `scientific_validation: false`.

Os dois últimos comandos usam números inventados para demonstrar a interface. O protocolo
sintético usa o estado exigido pela API apenas para exercitar a auditoria; não representa
aprovação do estudo final nem resultados de um instrumento. Ver [instruções dos exemplos](../examples/README.md).

## 6.3 Coleta e análise de arquivos reais

No host, com ADB e aparelho autorizado:

```powershell
aema collect --serial SERIAL --output-root captures
aema --checkin caminho/stats.csv --battery-report caminho/stats.txt --packages caminho/packageUID.txt --output-root outputs
aema inspect --metric computed_drain_mah --source power
```

O comando de parsing usa modo estrito por padrão. `--lenient` serve para exploração com
rejeições registradas; não permite aceitar versão check-in desconhecida. O app utiliza
o fluxo estrito da versão atual. Erros de domínio na CLI retornam código 2; argumentos
inválidos são tratados pelo argparse.

No telefone, instale o [APK atual](https://github.com/James-bb-ALT/AEMA/releases),
inicie/autorize Shizuku, escolha pasta local, autorize alarmes e notificações e ative
a automação. A primeira captura é imediata. Coleta manual não redefine a âncora automática;
pausar preserva os dados e uma captura já iniciada pode terminar normalmente.

Para transferir, copie os ZIPs da pasta escolhida ao computador e preserve os originais.
Extraia um ZIP confiável em uma pasta de análise. Leia primeiro o manifesto de captura;
somente use `parsed_directory` como dataset quando o parsing tiver passado. Exemplo de API:

```python
import json
from pathlib import Path
from aema.dataset import load_dataset

capture = Path("captura-extraida")
metadata = json.loads((capture / "capture_manifest.json").read_text(encoding="utf-8"))
if metadata.get("status") != "complete" or metadata.get("parse_status") != "complete":
    raise ValueError("Captura não contém dataset completo; examine o diagnóstico")
records, relations, manifest = load_dataset(capture / metadata["parsed_directory"])
```

Não misture totais UID, totais globais e componentes como se fossem observações
independentes aditivas. Também não una dados de aparelhos distintos apenas por UID.
Para compartilhar, use a política e os comandos de [Privacidade](../study/PRIVACY.md).

## 6.4 Testes e evidências registradas

Baseline histórico da release 1.0.0, datado de 24/11/2026. Para a camada LLM em
2.0.0, consulte [verificações da release](../releases/2.0.0.md) e
[operação e debug](../android/LLM-E-DEBUG.md).

| Verificação | Evidência | O que não demonstra |
|---|---|---|
| Python local | 167 testes; cobertura 92,16%, acima do mínimo 90% | Exatidão elétrica ou ausência de todos os defeitos |
| Lint/formato Python | Ruff aprovado | Validade científica do dado |
| Checkout limpo no CI | Python 3.10 e 3.13 aprovados | Todos os sistemas/versões Python possíveis |
| Android build/lint | APK assinado e lint sem erros; build limpo no CI | Compatibilidade com todos os fabricantes |
| JVM | Três testes de cadência e relógio | Um ciclo físico de seis horas no telefone |
| Instrumentado: pipeline | Mesma fixture no APK com exportação/reimportação | Todos os formatos Android |
| Instrumentado: Shizuku/alarme | Coleta real fora da tela, ZIP, próxima cadência e preservação após pausa | Confiabilidade estatística de longo prazo |
| Instrumentado: falha | Shizuku parado gera diagnóstico; parsing não é declarado completo | Recuperação de toda interrupção abrupta |

O [CI da release](https://github.com/James-bb-ALT/AEMA/actions/runs/45420908322) registra
as verificações hospedadas. Os testes instrumentados foram executados localmente em
emulador Android 15; o workflow atual executa build, testes JVM e lint, não esses cenários
instrumentados com Shizuku. Não existe evidência de validação em aparelho físico do usuário
ou execução contínua de seis horas em tempo real.

### Reexecutar as verificações

```powershell
.venv\Scripts\python -m pytest --cov=aema --cov-report=term-missing
.venv\Scripts\ruff check --no-cache src tests
.venv\Scripts\ruff format --check --no-cache src tests
android\gradlew.bat -p android assembleDebug testDebugUnitTest lintDebug
android\gradlew.bat -p android connectedDebugAndroidTest
```

JDK 21, SDK 35 e build-tools 36.0.0 são os requisitos da build documentada. No Linux,
use `bash android/gradlew`. O teste de alarme assume Shizuku ativo/autorizado e alarmes
permitidos; o teste de falha assume Shizuku indisponível. São cenários opostos e podem
ser ignorados por suas precondições em uma mesma execução. Para exercitar ambos, rode-os
separadamente no ambiente adequado. Não interprete um teste ignorado como cenário validado.

## 6.5 Problemas operacionais e resposta

| Situação | Verificação | Conduta |
|---|---|---|
| Importação usa módulo antigo/ausente | Origem de `aema` e instalação do ambiente | Reinstalar `-e ".[dev]"` no ambiente correto |
| Shizuku indisponível | Serviço iniciado e AEMA autorizado | Iniciar/autorizar; após reboot via ADB pode ser necessário iniciar novamente |
| Nenhum ZIP no horário | Telefone ligado, automação, permissões e restrições | Registrar lacuna; abrir o app e conferir próximo alarme; não reconstruir dado inexistente |
| ZIP privado existe, pasta não recebeu cópia | Grant SAF, espaço e provedor | Reescolher pasta e usar “Copiar todos os ZIPs”; manter original privado |
| Coleta completa, parsing incompatível | `parse_error`, schema/versão e diagnósticos | Preservar brutos; não editar silenciosamente o relatório para aparentar sucesso |
| Importador rejeita hash/contrato | Arquivos completos, manifesto e versão do software | Reobter cópia íntegra; não recalcular manifesto para esconder adulteração |
| Armazenamento cheio | Espaço e cópias já transferidas | Transferir com verificação e aplicar retenção aprovada; o app não faz limpeza automática |

Evite colocar dumps privados em issues públicas. Para relatar um novo formato, forneça
trecho mínimo anonimizado, SDK/build relevante e a mensagem de erro, preservando uma
cópia original privada para o responsável pelo estudo.

## 6.6 Ameaças à validade

**Validade de construção:** atribuição de carga, drenagem reportada, carga física, energia,
corrente e RAM usada são grandezas/indicadores distintos. O catálogo ajuda a diferenciá-los;
não elimina erro de definição do que se pretende medir.

**Validade interna:** temperatura, alimentação USB, clocks não alinhados, reset de
estatísticas, carga de fundo, ordem dos ensaios e overhead podem explicar diferenças.
Controle e registre esses fatores antes de atribuir causalidade ao workload.

**Validade estatística:** poucas repetições, snapshots dependentes, exclusões escolhidas
depois dos resultados e pooling de dispositivos podem produzir conclusões frágeis.
O analisador não implementa um modelo inferencial para resolver esses problemas.

**Validade externa:** emulador, um aparelho e um build não representam a população Android.
Wheels nativos, versões de fabricantes, páginas de 16 KiB e permissões precisam de
avaliação no alvo. Ver [matriz de compatibilidade](../android/COMPATIBILITY.md).

**Integridade e privacidade:** hash consistente não comprova autenticidade; pseudônimo
não garante anonimato; um arquivo chamado `frozen` não prova anterioridade do protocolo.
Essas evidências dependem também da governança do estudo.

## 6.7 Próximos marcos científicos e técnicos

| Marco | Entrega necessária para fechar |
|---|---|
| Aprovação do estudo | Pergunta, hipóteses, margem, população e protocolo formalizados |
| Aceite físico do app | Captura manual, série de seis horas, retomada e falhas no aparelho real |
| Comparação primária | Referência calibrada, janelas pareadas, repetições e resultados em mAh |
| Sincronização/overhead | Evidência de relógios, perdas e comparação com/sem coletor |
| Extensões RAM/componentes/1 µA | Hardware apropriado, escopo, unidade e critério de decisão próprios |

A integração 2.0.0 acrescenta leitura por LLM e diagnóstico, não executa os marcos de
validação elétrica, treinamento ou previsão. O estado científico deve ser atualizado
quando novas evidências existirem.

## 6.8 Manutenção e publicação

Código do app/pacote, contratos e documentação têm responsabilidades distintas. As edições
documentais 1.0.1/1.0.2 preservaram o software 1.0.0. A nova funcionalidade de leitura LLM
altera app e pacote; a etapa 2.0.0 sincroniza essas versões com a documentação, preservando
os schemas não alterados. Uma atualização apenas de texto não exige um novo APK idêntico.

Na classificação adotada pelo proprietário: melhoria incremental incrementa `x.y.Z`;
mudança grande incrementa `x.Y.0`; nova etapa incrementa `X.0.0`, zerando campos à direita.
Atualize os componentes realmente afetados, descrições, changelog e notas. Preserve
registros históricos, dependências não alteradas, chaves e dados privados.

Antes de publicar, confira diff, links e exemplos; execute os testes pertinentes e
registre os resultados. Commits/push não devem usar force-push. Builds release assinadas
usam a chave privada fora do Git, conforme o [guia Android](../android/README.md).
