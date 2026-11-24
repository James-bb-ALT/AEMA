# Auditoria técnica do AEMA

Auditoria concluída em 2026-09-20 sobre o conteúdo disponível em `E:\Pycharm Projects\AEMA`. Esta pasta documenta o estado observado; não transforma hipóteses em requisitos e não afirma que o repositório Android original foi recuperado.

## Leitura recomendada

1. [10 — Resumo executivo](10-EXECUTIVE-SUMMARY.md)
2. [01 — Recuperação do projeto](01-PROJECT-RECOVERY.md)
3. [02 — Estado atual](02-CURRENT-STATE.md)
4. [03 — Arquitetura](03-ARCHITECTURE.md)
5. [04 — Metodologia de medição](04-MEASUREMENT-METHODOLOGY.md)
6. [05 — Auditoria de código](05-CODE-AUDIT.md)
7. [06 — Compatibilidade Android](06-ANDROID-COMPATIBILITY.md)
8. [07 — Testes e validação](07-TESTING-AND-VALIDATION.md)
9. [08 — Roadmap técnico](08-TECHNICAL-ROADMAP.md)
10. [09 — Fundamentação acadêmica](09-ACADEMIC-FOUNDATION.md)

## Convenções de evidência

- **Comprovado:** observado diretamente em código, dados ou execução registrada.
- **Inferência:** interpretação compatível com as evidências, mas não confirmada pelo autor.
- **Proposta:** recomendação para uma fase futura; não está implementada.
- **Não verificado:** faltam código, dispositivo, histórico ou protocolo para concluir.

Arquivos-fonte são citados por caminho e linhas. Os dumps são dados de um único conjunto disponível, não resultados experimentais reproduzidos. As referências externas são exclusivamente documentação Android/AOSP primária.

## Resultado em uma frase

O material disponível é um protótipo host-side em Python que tenta converter três exportações ADB/BatteryStats em CSV; ele não contém app Android nem instrumentação de RAM/corrente, seu parser check-in produz saída vazia e seu parser textual preserva estimativas em mAh com rótulos de tempo incorretos.
