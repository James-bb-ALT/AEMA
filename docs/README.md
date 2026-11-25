# Documentação do projeto AEMA

**Edição da documentação: 2.0.2 · Software documentado: 2.0.1 · 24/11/2026.**

O AEMA é uma infraestrutura de coleta, interpretação e análise offline de dados Android
BatteryStats. O app usa Shizuku para criar capturas locais a cada seis horas; o computador
permite inspecionar, verificar, exportar e analisar os dados com o mesmo núcleo Python.
O estudo científico proposto investiga o erro das estimativas de carga total em mAh em
relação a uma referência externa calibrada. A infraestrutura está implementada; o estudo
com referência externa ainda não foi executado.

O objetivo final de produto foi ampliado pelo autor para **previsão personalizada de
consumo e recomendações**, com execução offline no telefone. O
[caderno de estudos de IA](estudos/README.md) documenta essa linha, os requisitos
confirmados, as alternativas e as fontes. A comparação elétrica continua como estudo
de sustentação. A versão 2.0.0 implementa leitura por LLM e sugestões limitadas aos
fatos de uma captura. A correção 2.0.1 limita o papel do modelo à seleção de evidências;
ações são associadas localmente. Previsão treinada e aprendizado pessoal permanecem propostos.
Ver [guia da IA e debug](android/LLM-E-DEBUG.md).

## Roteiro de leitura

| Documento | Pergunta respondida |
|---|---|
| [Objeto, objetivos e hipóteses](projeto/01-OBJETO-E-HIPOTESES.md) | O que será estudado, por quê e quais hipóteses serão avaliadas? |
| [Metodologia científica](projeto/02-METODOLOGIA.md) | Como coletar, controlar, comparar e interpretar os ensaios? |
| [Arquitetura e tecnologias](projeto/03-ARQUITETURA-E-TECNOLOGIAS.md) | Como Android, Shizuku e Python trabalham juntos e por que foram usados? |
| [Código e algoritmos](projeto/04-CODIGO-E-ALGORITMOS.md) | Qual é a responsabilidade de cada módulo e quais transformações ele executa? |
| [Dados e contratos](projeto/05-DADOS-E-CONTRATOS.md) | O que significam os arquivos, campos, unidades, versões e diagnósticos? |
| [Operação, validação e limites](projeto/06-OPERACAO-VALIDACAO-E-LIMITES.md) | Como reproduzir o funcionamento, verificar resultados e reconhecer limitações? |
| [Referências e glossário](projeto/07-REFERENCIAS-E-GLOSSARIO.md) | Quais fontes fundamentam o projeto e o que significam seus termos? |
| [Catálogo completo](CATALOGO-COMPLETO.md) | Quais são os 147 campos catalogados, suas unidades e classes? |
| [Estudos de IA e previsão](estudos/README.md) | Como investigar modelos leves, aprendizado pessoal e recomendações offline, e quais fontes sustentam as escolhas? |
| [Leitura LLM e debug implementados](android/LLM-E-DEBUG.md) | Como instalar o modelo, analisar, cancelar, exportar e reproduzir a integração 2.0.1? |
| [Simulação e viabilidade](estudos/05-SIMULACAO-E-VIABILIDADE-LLM.md) | O que passou nos testes, o que aprendeu o LLM sintético e o que falta validar com dados reais? |
| [Alternativas ultraleves](estudos/06-MODELOS-ULTRALEVES-E-REDES-NEURAIS.md) | Como substituir o custo do LLM por regressão ou rede pequena, e qual o papel de Indra/EmbeddingGemma? |

Para instalar e usar o app, consulte o [guia Android](android/README.md). Para compartilhar
resultados, leia a [política de privacidade](study/PRIVACY.md). Para preparar a redação
científica, use o [modelo de resultados](study/RESULTS-TEMPLATE.md), sem preencher conclusões
que ainda não tenham dados experimentais.

## Como interpretar as afirmações

| Classificação | Significado nesta documentação |
|---|---|
| Implementado | Há código correspondente no repositório. Isso não comprova desempenho físico. |
| Verificado | Há execução de teste ou evidência identificada, com ambiente e alcance declarados. |
| Proposto | Decisão metodológica candidata; não foi aprovada nem executada como estudo final. |
| Pendente | Falta decisão, hardware, dado ou implementação necessária à conclusão. |
| Histórico | Registro de uma etapa anterior; não deve substituir a descrição atual. |

A infraestrutura original foi documentada a partir da release [1.0.0](https://github.com/James-bb-ALT/AEMA/releases/tag/v1.0.0),
commit-base `6c0ae26`. A camada LLM e debug acrescentada em 2.0.0 tem contratos,
código e verificações próprios no guia correspondente e nas notas de release.
As referências externas estão datadas no capítulo 7. Não há expansão formal da sigla AEMA
registrada no pacote; esta documentação não atribui um nome por extenso sem decisão do autor.

## Versões e organização

A etapa funcional publicada mantém app e pacote Python em **2.0.1**. A documentação
atual é **2.0.2**, conforme a classificação do projeto. Contratos não alterados permanecem:
captura 1.0, registro canônico 1.0 e manifesto de dataset 2.0. O catálogo avança para
1.2 com GPU; datasets 1.1 continuam importáveis quando não contêm as novas métricas.
Ver [notas da release](releases/2.0.1.md); edições documentais anteriores permanecem históricas.

A edição documental **2.0.2** acrescenta estudo de alternativas ultraleves e inspeção
do tamanho dos APKs. App e pacote permanecem 2.0.1; ver
[notas documentais](releases/docs-2.0.2.md).

O [estado atual](STATUS.md) resume a entrega. Os arquivos em `audit/` e `refactoring/`
preservam avaliações anteriores. O [plano de implementação](roadmap/IMPLEMENTATION-PLAN.md)
contém atualizações e uma matriz histórica; não use o baseline antigo como inventário atual.
Os protocolos R-302 a R-402 continuam úteis como propostas e condições para ensaios futuros.

## O que ainda não pode ser concluído

Não existem resultados de erro elétrico, exatidão, incerteza expandida, consumo exclusivo
de RAM, precisão de 1 µA ou generalização para todos os aparelhos. A coleta de seis horas
produz snapshots acumulados, não seis horas isoladas de medição. Esses limites orientam
as hipóteses e o desenho experimental, em vez de serem preenchidos por estimativas inventadas.
