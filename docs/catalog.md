# Catálogo canônico R-204.1

Versão `1.0`. O catálogo em `src/aema/catalog.py` inventaria, por DataFrame, cada coluna atualmente exportada.
Cada entrada mapeia campo para entidade, métrica/valor, unidade, classe de medição, origem e proveniência.

Identificação: `uid`, `uid_text`, `package_name`, `process_name`, `wakelock_name`, `power_item`.
Metadados: tags, categorias, versão, tipo de registro, linha, unidade e classificação.
Métricas: contagens, tempos, bytes, pacotes e cargas `mAh`.

Exceções justificadas: campos numéricos do check-in não trazem unidade na fonte; permanecem com unidade `None`.
`uid_text` preserva representação textual sem tratá-la como métrica. `measurement_kind` é nativo apenas no
relatório de potência; demais campos não recebem classificação científica inventada. `input_sha256` aponta
para o manifesto atual, pois não existe coluna de hash nos CSVs legados. Colunas novas falham no teste de cobertura.
