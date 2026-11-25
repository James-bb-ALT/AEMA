# Experimentos AEMA

Código de pesquisa executado no computador. Os modelos sintéticos desta pasta não
estão instalados no app e não produzem previsões pessoais validadas.

## Comparação ultraleve 1.0.0

Implementação independente do componente app/pacote 2.0.1. NumPy já acompanha as
dependências transitivas do parser; não instala PyTorch, scikit-learn ou pesos externos.

Na raiz, com o ambiente de desenvolvimento do projeto instalado:

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
python -m experiments.ultralight_validation --output dist/ultralight-1.0.0
python -m pytest tests/integration/test_ultralight_experiment.py
```

Para reproduzir o ambiente medido: Python 3.13.9, NumPy 2.5.3 em Windows x86_64.
BLAS/CPU/versões afetam arredondamento e tempos; os testes usam tolerância explícita.
A simulação usa 5 sementes e 2 regimes pareados, 24 atributos, 7 alvos, treino/validação/
teste cronológicos; quatro configurações MLP e quatro regularizações Ridge. O teste
final não escolhe a arquitetura. Os artefatos JSON incluem pesos arredondados para
FP32, normalizadores, ordem dos atributos/alvos e hash. Não são checkpoints de produção.

Saídas: `comparison.json`, dez modelos Ridge e dez MLP, log stdout. `portable_predict`
e `portable_ridge` executam os pesos por listas no host para conferir paridade; não
substituem testes Android. Um arquivo JSON com números FP32 serializados ocupa mais
que o cálculo de bytes de pesos binários. Não são modelos quantizados int8.

Método, resultados e limites: [estudo 7](../docs/estudos/07-COMPARACAO-RIDGE-MLP.md).
Mudanças futuras de gerador/grid exigem nova versão e nova avaliação; não ajustar
hiperparâmetros para melhorar números do teste final já observado.

## Experimentos históricos

- `battery_validation.py`: pipeline sintético, baselines numéricos e dados de seleção
  LLM do [estudo 5](../docs/estudos/05-SIMULACAO-E-VIABILIDADE-LLM.md).
- `lora_feasibility.py`: ensaio LoRA isolado, requer ambiente GPU e dependências
  documentadas no estudo 5. Não é requisito da comparação ultraleve.
