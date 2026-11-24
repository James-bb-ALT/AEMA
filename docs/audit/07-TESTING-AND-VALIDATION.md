# 07 — Testes e validação

## Ambiente auditado

- Host: Windows; workspace `E:\Pycharm Projects\AEMA`.
- Python global 3.10.6; `.venv` Python 3.13.9; pandas 2.3.0.
- ADB 35.0.2; lista de dispositivos vazia. O servidor ADB iniciado pela consulta foi encerrado ao final.
- Não há Git, ferramenta de build Android, manifesto de dependências ou suíte de testes no projeto.

## Verificações executadas

| ID | Comando/procedimento | Resultado | Classificação |
|---|---|---|---|
| V-01 | `rg --files` com exclusão de `.git/build/.gradle` | Apenas Python, dumps, saídas, `.idea/.venv`; nenhum projeto Android | Executado/aprovado como inventário |
| V-02 | `git status`, `git branch -a`, `git log --all` | `fatal: not a git repository` | Executado/reprovado por ausência de repositório |
| V-03 | Parse AST dos 6 `.py` com Python da `.venv` | 6/6 sintaticamente válidos | Executado/aprovado |
| V-04 | Invocação em memória de `CsvParser.parse()` | Shape `(0, 0)` | Executado/reprovado funcionalmente |
| V-05 | Invocação em memória de `TxtParser.parse()` | Shape `(174, 34)`; unidades/rótulos inconsistentes | Executado/reprovado semanticamente |
| V-06 | Invocação em memória de `UidParser.parse()` | `(791, 2)`, 791 pacotes únicos, 653 UIDs | Executado/aprovado para a amostra |
| V-07 | Execução de `main.main()` com saída redirecionada para diretório temporário | Concluiu; arquivos 2 B/10.915 B/29.522 B; temporário removido | Executado; orquestração aprovada, produto parcial reprovado |
| V-08 | `.venv\Scripts\python.exe -m pip check` | `No broken requirements found` | Executado/aprovado no ambiente local |
| V-09 | `.venv\Scripts\python.exe -m pytest --collect-only -q` | `No module named pytest` | Teste indisponível; framework ausente |
| V-10 | Hash SHA-256 dos dois conjuntos `parsed_*` | Arquivos correspondentes idênticos | Executado/aprovado como consistência histórica |
| V-11 | Análise estrutural do check-in com `csv.reader` | 4.218 registros; tags na coluna 4; 819 `pr`, 491 `wl`, 65 `nt`, 1 `m`, 409 `pwi` | Executado/aprovado como diagnóstico |
| V-12 | `adb devices -l` | Nenhum dispositivo | Executado; validação em hardware indisponível |
| V-13 | Contagem de fences Mermaid e busca por `mmdc` | 2 diagramas balanceados; renderizador local ausente | Sintaxe estrutural verificada; renderização visual indisponível sem instalar ferramenta |

Nenhum arquivo de produto foi modificado e nenhum experimento físico foi executado.

## Comportamento observado estaticamente

- Encoding das três entradas: BOM `FF FE`, UTF-16 LE.
- Hashes SHA-256: `stats.csv` `2529A96F...EC12D`; `stats.txt` `3ADF138A...86F6`; `packageUID.txt` `C6D00A19...7C4A`.
- `stats.txt` tem 59.588 linhas, `stats.csv` 4.218 e `packageUID.txt` 791.
- Há 173 linhas de potência por UID (133 `u0aN`, 40 numéricas), todas do usuário 0.
- EnergyConsumer não suportado no dump; não há base para teste de rail no hardware original.

## Lacunas de teste

Não existem fixtures mínimas, golden files, testes de unidade, integração, propriedades, schema, locale, encoding inválido, arquivo ausente, versão desconhecida, multiusuário, shared UID, valores negativos/exponenciais, saída atômica ou performance. Também faltam testes em múltiplos Android/OEMs.

## Plano reproduzível de validação futura

### Software

1. Congelar schemas por versão e criar fixtures anonimizadas para cada tag.
2. Testar contagens, chaves, tipos e unidades; resultado vazio deve falhar se a entrada contiver tags suportadas.
3. Reconciliar `pws`, soma de `pwi` e resumo textual dentro de tolerância explicada.
4. Testar UIDs numéricos, `u0aN`, usuários secundários e UIDs compartilhados.
5. Golden files para uma sessão conhecida e testes de round-trip do manifesto.
6. Medir memória/tempo com dumps crescentes depois da correção funcional.

### Experimento energético

1. Definir dispositivo/build, workload determinístico, baseline ocioso e variáveis controladas.
2. Desconectar fontes de carga; fixar brilho, rede, temperatura, estado de carga e apps de fundo.
3. Sincronizar marcador de início/fim entre Android e instrumento externo.
4. Repetir condições em ordem aleatorizada, com aquecimento e janela iguais.
5. Capturar dados brutos sem sobrescrever; registrar calibração e incerteza do instrumento.
6. Comparar estimativa BatteryStats, gauge total e referência externa; relatar erro e intervalo de confiança.
7. Para componente, variar um fator por vez e reportar diferença contra baseline; chamar de atribuição somente se o método e a incerteza a sustentarem.

Critério de interrupção: não publicar granularidade de 1 µA nem consumo individual de RAM enquanto a incerteza combinada e a separação do sinal não forem demonstradas.
