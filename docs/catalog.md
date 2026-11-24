# Catálogo canônico R-204.1

> Registro histórico da etapa R-204.1. O catálogo atual do software 1.0.0 é a versão
> **1.1**, documentada no [inventário completo](CATALOGO-COMPLETO.md) e nos
> [contratos atuais](projeto/05-DADOS-E-CONTRATOS.md). O texto abaixo preserva o estado
> anterior; suas exceções e versão não devem ser usadas como descrição atual.

Versão `1.0`. O catálogo em `src/aema/catalog.py` inventaria, por DataFrame, cada coluna atualmente exportada.
Cada entrada mapeia campo para entidade, métrica/valor, unidade, classe de medição, origem e proveniência.

Identificação: `uid`, `uid_text`, `package_name`, `process_name`, `wakelock_name`, `power_item`.
Metadados: tags, categorias, versão, tipo de registro, linha, unidade e classificação.
Métricas: contagens, tempos, bytes, pacotes e cargas `mAh`.

Exceções justificadas: campos numéricos do check-in não trazem unidade na fonte; permanecem com unidade `None`.
`uid_text` preserva representação textual sem tratá-la como métrica. `measurement_kind` é nativo apenas no
relatório de potência; demais campos não recebem classificação científica inventada. `input_sha256` aponta
para o manifesto atual, pois não existe coluna de hash nos CSVs legados. Colunas novas falham no teste de cobertura.
