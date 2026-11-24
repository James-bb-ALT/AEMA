# 05 — Auditoria de código

## Achados priorizados

### Críticos — validade dos resultados

**C-01 — Parser check-in nunca reconhece a amostra.** [`csv_parser.py`, linhas 21–25](../../csv_parser.py) lê a tag em `parts[2]`; a amostra usa `l` nessa posição e `pr/wl/nt/m` em `parts[3]`. Comportamento executado: DataFrame `(0, 0)` e CSV de 2 bytes. Impacto: 819 processos, 491 wakelocks, 65 redes, 1 misc e demais registros são perdidos. Correção futura: adaptador versionado pelo `CHECKIN_VERSION`, preservando UID/categoria/tag. Validação: fixtures reais por tag, contagens e golden files.

**C-02 — Valores mAh são publicados como tempo.** [`txt_parser.py`, linhas 57–65 e 69–82](../../txt_parser.py) e [`translation.py`, linhas 50–65](../../translation.py) convertem os campos sob “Estimated power use (mAh)” em `CPU_foreground_time`, `Screen_on_time`, `Audio_time` etc. Impacto: análise dimensional falsa e conclusões científicas inválidas. Correção futura: nomes `*_energy_estimate_mah`/`*_charge_estimate_mah`, modelo canônico com unidade e origem. Validação: checagem dimensional e comparação com `pwi`/proto oficial.

**C-03 — Não há proveniência experimental.** [`main.py`, linhas 10–34](../../main.py) usa nomes fixos e grava apenas tabelas; não registra comando, serial, modelo, build, intervalo, hashes, timezone, estado de alimentação ou versão do parser. Impacto: resultados não são reproduzíveis nem comparáveis. Correção futura: manifesto de sessão imutável. Validação: schema obrigatório e reprodução por hash.

**C-04 — Meta de corrente não tem instrumentação.** Nenhum fonte usa BatteryManager, PowerStats, Perfetto, sysfs ou instrumento; buscas no código retornam zero. Impacto: 0,001 mA e corrente por componente não podem ser avaliados. Correção futura depende primeiro de protocolo e hardware, não de formatação. Validação: comparação calibrada.

### Altos

**H-01 — Schema check-in também está deslocado internamente.** Após a tag, os dados começam em `parts[4]`, mas as linhas 28–80 começam em `parts[3]` e omitem UID. `wl` tem estrutura variável. Impacto: trocar apenas um índice produziria dados corrompidos. Validação futura deve cobrir versão 9 observada.

**H-02 — Resumo global não é parseado.** [`txt_parser.py`, linhas 25–33](../../txt_parser.py) espera `Computed drain:` e `Actual drain:` no início de linhas separadas; na amostra ambos aparecem dentro da linha `Capacity:`. Resultado: uma string composta e duas colunas ausentes. Validar 4700/1377/1269–1363 separadamente.

**H-03 — UID multiusuário calculado incorretamente.** [`txt_parser.py`, linhas 43–51](../../txt_parser.py) usa escala 10.000 para usuários >0; AOSP usa 100.000. A amostra só tem usuário 0, portanto é risco confirmado no código, não falha observada nos dados. Testar `u10a358 -> 1010358` conforme `UserHandle`.

**H-04 — Tokenização destrutiva.** [`txt_parser.py`, linha 76](../../txt_parser.py) remove sinal e notação exponencial. Impacto: valores negativos/exponenciais podem mudar de significado sem erro. Correção: regex ancorado e parser de unidade; falhar fechado.

**H-05 — Identidade e total de UID são perdidos.** O total após `UID u0a382: 251` é ignorado; o parser check-in não preserva UID; e [`main.py`](../../main.py) nunca une os 791 pacotes às 173 estimativas. Impacto: atribuição incompleta e ambígua para UIDs compartilhados. Validação: integridade referencial muitos-para-muitos e reconciliação de totais.

### Médios

**M-01 — Linhas inválidas são descartadas silenciosamente.** `continue` e `except ValueError` sem contadores em [`csv_parser.py`, linhas 20–27](../../csv_parser.py) e [`uid_parser.py`, linhas 15–28](../../uid_parser.py). Resultado vazio é tratado como sucesso. Adicionar diagnóstico e limiares de completude.

**M-02 — Saída pode ser parcial ou colidir.** [`utils.py`, linhas 9–11](../../utils.py) tem precisão de um segundo e `exist_ok=True`; [`main.py`](../../main.py) grava arquivos sequencialmente. Duas execuções no mesmo segundo podem sobrescrever; uma falha intermediária deixa sessão parcial. Usar ID único, diretório temporário, manifesto e promoção atômica.

**M-03 — Formato humano e idioma são frágeis.** `startswith` em inglês e indentação removida acoplam o parser à apresentação do Android/OEM. Preferir proto/check-in versionado; manter texto apenas como diagnóstico.

**M-04 — Dependências e execução não são declaradas.** Não há `requirements.txt`/`pyproject.toml`; a `.venv` contém Python 3.13.9 e pandas 2.3.0, enquanto `python` global é 3.10.6. Resultado fora da máquina não é reproduzível.

**M-05 — Carga integral do texto.** [`txt_parser.py`, linhas 20–21](../../txt_parser.py) materializa 59.588 linhas antes de processar. A amostra de 8,2 MB é tolerável, mas dumps maiores elevam memória sem necessidade. Um parser streaming/estado é recomendável após estabilizar o schema.

**M-06 — Privacidade sem controle.** Entradas e saídas expõem 791 pacotes e padrões de uso de apps. Não há política de retenção, anonimização ou aviso. Não há transmissão de rede ou execução de comando no código, portanto não foi observado risco de exfiltração ativa.

### Baixos/documentais

**L-01 — Marcadores de citação inválidos.** Comentários `:contentReference[oaicite:…]` não resolvem para fonte alguma em [`csv_parser.py`](../../csv_parser.py), [`txt_parser.py`](../../txt_parser.py), [`uid_parser.py`](../../uid_parser.py) e [`translation.py`](../../translation.py).

**L-02 — Nomenclatura mistura CSV/formato e domínio.** `CsvParser` e `TxtParser` descrevem o recipiente, não a versão/protocolo. Isso facilita suporte acidental a schemas incompatíveis.

## Arquitetura, concorrência e lifecycle

Não há concorrência, lifecycle Android, buffers assíncronos ou estado persistente. Logo, races Android não se aplicam ao código entregue. O problema de sincronização é experimental: três snapshots não carregam timestamps comuns comprovando que foram coletados juntos.

## Risco residual

Mesmo com parsers corrigidos, BatteryStats continuaria sendo uma combinação de métricas de atividade e modelos/atribuições. Corrigir software não transforma estimativa em medição direta. Essa distinção deve ser requisito de aceitação.
