# 03 — Arquitetura

## Visão atual

Trata-se de um script batch monoprocesso, host-side, sem módulos Android. As classes não mantêm estado além do caminho de entrada. Pandas é a única dependência de terceiros observada.

```mermaid
flowchart LR
  A[ADB / coleta externa não versionada] --> B[stats.csv\nBatteryStats check-in]
  A --> C[stats.txt\nBatteryStats legível]
  A --> D[packageUID.txt\npm list packages -U]
  B --> E[CsvParser]
  C --> F[TxtParser]
  D --> G[UidParser]
  H[Translation\nmapeamento de nomes] --> E
  H --> F
  E --> I[pandas DataFrame vazio\nna amostra]
  F --> J[pandas DataFrame\nestimativas mAh mal rotuladas]
  G --> K[pandas DataFrame\npacote ↔ UID]
  L[main.py] --> E
  L --> F
  L --> G
  M[make_timestamp_dir] --> L
  I --> N[stats_csv_parsed.csv]
  J --> O[stats_txt_parsed.csv]
  K --> P[uid_txt_parsed.csv]
```

**Propósito do diagrama:** mostrar a topologia observada e os três fluxos que nunca são integrados. **Fontes:** imports e chamadas em [`main.py`, linhas 1–34](../../main.py), parsers citados acima. **Renderização:** este arquivo Mermaid.

## Sequência de execução

```mermaid
sequenceDiagram
  participant U as Usuário/IDE
  participant M as main.py
  participant FS as Sistema de arquivos
  participant P as Parsers
  participant PD as pandas
  U->>M: python main.py
  M->>FS: cria parsed_<timestamp>
  loop CSV, texto, UID
    M->>P: parse(caminho hardcoded)
    P->>FS: lê arquivo inteiro/linha a linha
    P-->>M: DataFrame
    M->>PD: to_csv(..., index=False)
    PD->>FS: grava saída
  end
```

**Propósito do diagrama:** explicitar ordenação e risco de saída parcial. Se o segundo parser falhar, o primeiro arquivo já foi gravado; não existe transação, manifesto ou rollback.

## Responsabilidades e dependências

| Componente | Responsabilidade real | Acoplamento/problema |
|---|---|---|
| `main` | Coordenação e nomes | Acoplado ao diretório corrente, nomes fixos e três formatos |
| `CsvParser` | Reconhecimento posicional check-in | Acoplado a schema implícito incompatível; mistura entidades heterogêneas |
| `TxtParser` | Busca textual e tokenização | Acoplado ao inglês e à apresentação humana do dump |
| `UidParser` | Parser de duas chaves | Simples; descarta silenciosamente linhas inválidas |
| `Translation` | Aliases de cabeçalho | Mistura normalização com semântica/unidade incorreta |
| `utils` | Nomeação de pasta | Relógio local sem timezone/UUID/manifesto |

Não foram observadas dependências circulares. A coesão interna é razoável por arquivo, mas a separação mascara um problema de domínio: não existe um modelo de dados comum para sessão, métrica, unidade, escopo, UID, componente e método de medição.

## Fluxo de dados e perdas

1. A aquisição ocorre fora do projeto; comandos, horário, serial, modelo, build e estado experimental não são registrados.
2. `stats.csv` possui colunas `versão, UID, categoria, tag, ...`; `CsvParser` desloca o schema e perde tudo.
3. `stats.txt` contém tanto tempos quanto estimativas em mAh. `TxtParser` seleciona o bloco energético, mas renomeia parte dos valores como tempo.
4. O regex remove qualquer caractere que não seja dígito ou ponto ([`txt_parser.py`, linha 76](../../txt_parser.py)); sinais, expoentes e unidades são destruídos.
5. Cada resultado é uma tabela independente. Nenhum identificador de sessão ou hash de entrada segue para as saídas.

## Arquitetura que deve preceder qualquer implementação futura

**Proposta, não implementada.** Separar aquisição, adaptadores versionados de formato, modelo canônico tipado, validação, análise e exportação. O modelo mínimo deve carregar `session_id`, timestamps monotônico e civil, dispositivo/build, fonte, métrica, valor, unidade, escopo, UID/componente, método (`medido`, `estimado`, `proxy`) e incerteza conhecida. Essa direção aparece no roadmap; não autoriza refatoração nesta auditoria.
