# Checklist de ingestão mensal e do histórico

Este documento reúne, em um único lugar, o que precisa ser feito e reconferido quando novos meses chegam ao projeto (a carga mensal e, em especial, a ingestão do histórico de cerca de 2 anos). Os documentos de cada tabela e página descrevem o estado atual. Aqui ficam o gatilho e a ação.

Todos os números dos documentos são de março/2026, o único mês ingerido até 09/10/2026.

## 1. Antes de subir os arquivos

- [ ] Nome do arquivo no padrão `nome-base_AAAA_MM.extensão`, sem exceção, inclusive os dois pré-processados (`exames_laboratoriais_limpo`, `movimentacoes_limpo`). O `ano_mes` de lote vem do nome (ADR-0018).
- [ ] Anonimização local executada (`python -m src.anonymization.run`).
- [ ] Número de atendimento em texto puro, sem hash (ADR-0017). Conferir também colunas derivadas dele (RQ-013).
- [ ] Para a emergência, usar a fonte curada já tratada pelo projeto `pipeline-analytics-emergencia` nos campos de totem (RQ-009).

## 2. Ordem de execução

Arquivo novo com nome novo é processado como novo pelo Auto Loader. Arquivo com o mesmo nome sobrescrito é pulado, mesmo com conteúdo diferente, então o checkpoint precisa ser limpo.

1. Upload ao Volume.
2. Se for reprocessar um mês: dropar a tabela Bronze afetada e limpar o checkpoint do Auto Loader.
3. `01_bronze_ingestion`.
4. Pipeline `silver_transformations`.
5. Pipeline `gold_transformations` (Full Refresh, se o esquema mudou).
6. `03_process_mining.ipynb`, na ordem do topo, por seção. Só o que mudou precisa rodar de novo, mas a Conformance depende do mês corrente e do histórico (item 3).

## 3. Conferências depois da carga

Cada item tem uma consulta ou critério. Se o resultado divergir do esperado, abrir uma RQ antes de seguir.

- [ ] **Um único `ano_mes` por mês de lote.** `select ano_mes, count(*) from gold_event_log group by 1` deve listar só os meses ingeridos, sem fragmentos (ADR-0018, RQ-015).
- [ ] **Tabelas do notebook com os mesmos meses.** `gold_sna_handover`, `gold_sna_subcontracting`, `gold_variant_analysis` e `gold_conformance` não podem ter mês que não existe no `gold_event_log`.
- [ ] **Conformance.** Com ao menos 12 meses do ano anterior, a referência passa a ser o ano fechado, e fitness e precision passam a medir desvio de verdade (ADR-0019). Conferir o caso de cada fonte. Fitness ou precision exatamente 1,0 é sinal para investigar (RQ-014).
- [ ] **Internações do mês anterior.** Conferir se as 177 jornadas `sem_jornada_classificada` com alta e/ou movimentações ganham a internação nos meses anteriores (RQ-019).
- [ ] **Laboratório e imagem para internados.** Quando a base de laboratório passar a cobrir pacientes internados, conferir o percentual por porta de entrada (RQ-018). O desenho da Página 4 muda sozinho, sem alterar a query.
- [ ] **Reentrada na UTI nas jornadas cirúrgicas.** Com mais meses, as contagens deixam de ser tão pequenas (2, 6 e 7 jornadas). Contar as entradas por paciente depois da cirurgia e decidir se separam UTI pós-operatória esperada de retorno real (RQ-017).
- [ ] **UTI antes da cirurgia eletiva** (12 de 45 pacientes com UTI) e **UTI "durante" a cirurgia** (6 pacientes): reconferir a proporção. A segunda é suspeita de timestamp inconsistente.
- [ ] **Internação Clínica como porta de entrada** (58 jornadas, 14% das internações sem emergência): reavaliar a proporção (RQ-010).
- [ ] **Internados sem alta final registrada** (94 na Emergência, 60 nas demais portas): reconferir se eram internações em curso no corte do mês.
- [ ] **Variantes.** Refazer a distribuição por faixa de frequência e conferir o tamanho da cauda (`variants.md`).
- [ ] **Gargalo `Aviso de Cirurgia → Internação` e ausência de sazonalidade semanal:** reconferir (`bottlenecks.md`).
- [ ] **Fitness de 0,9738 em Movimentações:** investigar a causa (`conformance.md`).
- [ ] **Contagem de linhas** das tabelas do notebook e do dicionário de dados: atualizar o "Volume referência".

## 4. Dashboards

- [ ] **Filtro Período** lista os novos meses (`dim_periodo`). O filtro é multi-select e o bypass é `IS NULL`.
- [ ] **Gráficos de linha da Página 3** passam a desenhar segmentos a partir da segunda ingestão mensal. Conferir se o eixo Y fixo de 0 a 1 continua adequado.
- [ ] **Página 1**: os gráficos de tendência mensal ignoram o filtro Período por desenho.
- [ ] **Página 2**: a curadoria de marcos do DFG é manual (ADR-0016). Conferir se a lista de transições aprovadas continua válida.
- [ ] **Datasets com valores fixos**: `vw_dim_source` (7 fontes) e `vw_dim_especialidade` (6 traduções). Uma fonte ou especialidade nova só aparece depois de ganhar linha ali.
- [ ] **Página 4**: `espinha_arestas` é conferida nas três portas. As posições (x, y) são compartilhadas.

## 5. Documentação depois da carga

- [ ] Dicionário de dados: volumes de referência.
- [ ] CHANGELOG: registrar a carga e qualquer correção.
- [ ] RQ nova para qualquer divergência encontrada.