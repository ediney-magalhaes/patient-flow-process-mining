# ADR-0003: Motor de Transformação — Lakeflow Declarative Pipelines
 
## Decisão

**Adotar Lakeflow Declarative Pipelines (anteriormente Delta Live Tables / DLT) 
como motor declarativo principal de transformação.**

Validação realizada em 25/05/2026: Lakeflow funciona na Free Edition com 
compute serverless. Pipeline `silver_transformations` criado e executado com 
sucesso, materializando a tabela `silver_altas` no Unity Catalog com 
expectation `atendimento_valido` via `@dlt.expect_or_drop`.
 
---
 
## Contexto
 
Definida a arquitetura Medallion (ADR-0002), precisamos escolher o **motor 
de transformação** que materializa os dados entre as camadas. As opções no 
ecossistema Databricks são variadas, e cada uma tem implicações em qualidade, 
observabilidade, manutenibilidade e velocidade de desenvolvimento.
 
Requisitos do projeto:
 
- Validação automatizada de qualidade de dados
- Lineage automático entre camadas
- Suporte a dimensões historizadas (SCD Tipo 2)
- Recuperação automática de falhas em pipelines
- Compatibilidade com PySpark e SQL
- Baixo boilerplate
---
 
## Decisão (proposta)
 
**Adotar Lakeflow Declarative Pipelines (anteriormente Delta Live Tables / DLT) 
como motor declarativo principal de transformação.**
 
> ⚠️ Esta decisão depende de validação de disponibilidade na Free Edition. 
> Se indisponível, a alternativa é notebooks PySpark com validações manuais 
> (ver Alternativa A). A decisão sobre uso complementar de dbt-databricks 
> será tomada separadamente.
 
---
 
## Alternativas Consideradas
 
### Alternativa A — Notebooks PySpark puros + Workflows
 
**Prós:**
 
- Máxima flexibilidade e controle total
- Funciona em qualquer tier do Databricks
- Sem dependência de features específicas
**Contras:**
 
- Imperativo (mais código operacional)
- Validação de qualidade manual
- Lineage manual
- Recuperação manual de falhas
**Posição:** alternativa de fallback caso Lakeflow não esteja disponível na 
Free Edition.
 
### Alternativa B — dbt-databricks como única ferramenta
 
**Prós:**
 
- Familiar para a equipe (já usa dbt no BigQuery)
- Excelente para transformações SQL
**Contras:**
 
- Limitado para Python/PySpark
- Não suporta streaming nativamente
- SCD2 menos elegante
- Sem validações nativas equivalentes a expectations
**Posição:** pode complementar o motor principal para modelagem SQL pura em 
Gold. Decisão a ser tomada no Sprint 1/2.
 
### Alternativa C — Lakeflow Declarative Pipelines ✅ (proposta)
 
**Prós:**
 
- Declarativo (foco no "o quê", não no "como")
- Validações de qualidade nativas (expectations)
- Lineage automático no Unity Catalog
- SCD2 declarativo (APPLY CHANGES INTO / AUTO CDC)
- Recuperação automática de falhas
- Suporta PySpark e SQL na mesma pipeline
**Contras:**
 
- Lock-in mais forte na Databricks
- Disponibilidade na Free Edition não confirmada
- Debugging menos direto que notebooks
---
 
## Consequências (se confirmada)
 
### Positivas
 
- ✅ Qualidade de dados como cidadã de primeira classe (expectations)
- ✅ Lineage automático sem custo de manutenção
- ✅ Menos código operacional, mais foco em lógica de negócio
- ✅ Recuperação automática reduz operação manual
### Negativas
 
- ⚠️ Lock-in maior na Databricks (mitigado: Delta Lake é open source, lógica de transformação é portável)
- ⚠️ Se indisponível na Free Edition, requer reescrita para notebooks puros
### Trade-offs aceitos
 
- Troca de controle granular por produtividade — aceitável no contexto
---
 
## Validação realizada (Sprint 1)

- [x] Confirmar se Lakeflow Declarative Pipelines está disponível na Free Edition
- [x] Testar criação de pipeline simples com expectations
- [x] Status atualizado para "Aceito"
---
 
## Referências
 
- [Lakeflow Declarative Pipelines Documentation](https://docs.databricks.com/en/delta-live-tables/index.html)
- [Expectations (data quality)](https://docs.databricks.com/en/delta-live-tables/expectations.html)
- [APPLY CHANGES INTO / AUTO CDC](https://docs.databricks.com/en/delta-live-tables/cdc.html)
---
 
## Histórico
 
| Data | Mudança | Autor |
|---|---|---|
| 2026-04-26 | Criação (status: proposto) | @ediney-magalhaes |
| 2026-05-25 | Validado na Free Edition, status atualizado para Aceito | @ediney-magalhaes |
