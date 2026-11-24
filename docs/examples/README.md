# Exemplos didáticos de análise

**Todos os dados desta pasta são sintéticos. Não são resultados de um aparelho ou instrumento.**

[`ensaios-sinteticos.csv`](ensaios-sinteticos.csv) demonstra o ledger de seis ensaios
planejados: três de repouso e três de carga de CPU. Um ensaio de repouso é excluído por
um motivo previsto no [`protocolo-sintetico.json`](protocolo-sintetico.json). Sobram dois
pares válidos de repouso e três de CPU. IDs, hashes, calibração, horários e cargas foram
inventados apenas para exercitar o formato e a matemática.

O JSON tem `status: frozen` porque essa é uma precondição da API de auditoria. Isso não
aprova o estudo do AEMA. O campo adicional `purpose` e o identificador deixam explícita
a natureza demonstrativa. Copiar esse arquivo não cria protocolo real aprovado; substitua
o desenho, obtenha aprovação e preserve evidência temporal antes de coletar dados reais.

Na raiz do repositório, com o pacote instalado:

```powershell
python -m aema.validation docs/examples/ensaios-sinteticos.csv
python -m aema.study docs/examples/protocolo-sintetico.json docs/examples/ensaios-sinteticos.csv
```

O resultado descritivo esperado, derivado somente dos números inventados, é:

| Condição sintética | Válidos | Excluídos | Erro médio em mAh | Erro absoluto médio em mAh |
|---|---:|---:|---:|---:|
| `idle_sintetico` | 2 | 1 | 0 | 0,2 |
| `cpu_sintetico` | 3 | 0 | 1 | 1 |

Não interprete a diferença entre essas linhas como evidência sobre repouso ou CPU reais.
Os hashes são valores hexadecimais fictícios, sem arquivos brutos correspondentes; o
analisador valida seu formato e não certifica a existência ou a calibração de uma fonte.
