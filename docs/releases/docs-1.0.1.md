# Documentação AEMA 1.0.1

Edição documental de 24 de novembro de 2026 para o software **AEMA 1.0.0**.
Classificação: melhoria incremental; a edição documental avança de 1.0.0 para 1.0.1.
App, pacote Python, dependências, schemas e catálogo permanecem nas versões existentes.

## Conteúdo

- Objeto de estudo, perguntas, objetivos, hipóteses candidatas e decisões ainda abertas.
- Métodos implementados e protocolo proposto de comparação pareada em mAh, controles,
  incerteza, amostragem, overhead, componentes/RAM e meta secundária de 1 µA.
- Arquitetura, tecnologias, versões, responsabilidades de todos os módulos Python e
  componentes Android, contratos de arquivos e interpretação de diagnósticos.
- Inventário completo dos 145 campos do catálogo, com unidades e classes de evidência.
- Operação reproduzível, exemplos sintéticos executáveis, evidências de validação,
  ameaças à validade, limites de privacidade e referências oficiais.

Ponto de entrada: [`docs/README.md`](../README.md). Os exemplos são demonstrativos e
não constituem ensaios reais. A documentação não aprova hipóteses pelo orientador, não
declara validação elétrica e não implementa novos métodos de análise.

## Verificação

Foram conferidos os 27 módulos Python e todos os componentes Java principais contra o
mapa de código. Foram validados 115 links locais em 15 páginas, os blocos de código
delimitados, o demo e os dois exemplos de análise/auditoria. Os seis ensaios sintéticos
foram auditados com uma exclusão prevista, preservando dois pares de repouso e três de CPU.

A suíte Python passou com **167 testes e 92,16% de cobertura**. Esta edição não altera
código de runtime; não foi gerado um novo APK nem repetido o ensaio instrumentado por
uma mudança exclusivamente documental. Os cenários Android citados pertencem à evidência
registrada na release 1.0.0 e continuam identificados como tal.

O arquivo ZIP documental reúne o manual e os exemplos. Para navegar também pelos links
de código-fonte, use o checkout completo ou o arquivo de fontes oferecido pelo GitHub.
