# ADR-0001: Adoção de Arquitetura Lakehouse via Databricks
 
## Status
 
**Aceito**
 
**Data:** 2026-04-26  
**Decisores:** Ediney Magalhães (Analytics Engineer)  
**Sprint:** 0
 
---
 
## Contexto
 
O Hospital Santa Rosa precisa de uma plataforma analítica capaz de:
 
- Processar dados de fluxo de pacientes (logs de eventos com timestamps)
- Suportar análises avançadas (Process Mining com PM4Py)
- Permitir Machine Learning futuro (predição de tempo de permanência)
- Servir BI executivo (dashboards e BI conversacional)
- Operar com **custo zero** na fase atual
- Atender requisitos de governança e LGPD para dados de saúde
A stack atual da organização envolve BigQuery + dbt para Data Warehousing 
clássico. Para este projeto, precisamos avaliar arquiteturas que suportem 
workloads diversos (SQL, ML, Process Mining) na mesma plataforma.
 
---
 
## Decisão
 
**Adotaremos arquitetura Lakehouse implementada via Databricks (Free Edition), 
utilizando Delta Lake como formato de tabela e Unity Catalog como camada de 
governança.**
 
---
 
## Alternativas Consideradas
 
### Alternativa A — Data Warehouse puro (BigQuery)
 
**Prós:**
 
- Stack já dominada pela equipe
- Excelente para SQL e BI
- Custo predizível com flat-rate
**Contras:**
 
- Limitado para workloads de Machine Learning
- Não suporta processamento Spark nativo (necessário para PM4Py em escala)
- Pouca flexibilidade para dados semi-estruturados (XES, JSON aninhados)
**Por que não escolhida:** Process Mining e ML futuro exigem flexibilidade que 
DW puro não oferece sem complementos pagos (Vertex AI, BigQuery ML).
 
### Alternativa B — Data Lake puro (S3/GCS + Spark OSS)
 
**Prós:**
 
- Custo extremamente baixo
- Total flexibilidade de formatos
- Open source puro
**Contras:**
 
- Sem ACID nativo (perda de consistência transacional)
- Sem governança nativa (lineage, masking, RBAC fino)
- Manutenção operacional alta (clusters, schedulers, metastore)
**Por que não escolhida:** trade-off de manutenção operacional vs. valor 
entregue não compensa em projeto de escopo definido.
 
### Alternativa C — Lakehouse via Databricks ✅
 
**Prós:**
 
- Une ACID (Delta Lake) com flexibilidade de Lake
- Governança unificada (Unity Catalog) sobre todos os dados
- Suporta SQL, Python, ML, streaming na mesma plataforma
- Free Edition viabiliza custo zero
- Padrão adotado na indústria (Netflix, Comcast, Shell)
**Contras:**
 
- Lock-in moderado na plataforma Databricks
- Curva de aprendizado para quem vem de DW puro
- Free Edition tem restrições non-commercial e quota diária de compute
---
 
## Consequências
 
### Positivas
 
- ✅ Plataforma única para todos os workloads do projeto
- ✅ Lineage automático via Unity Catalog
- ✅ Delta Lake oferece time travel para auditoria e reprocessamento
- ✅ Stack alinhada ao padrão enterprise de mercado
### Negativas
 
- ⚠️ Lock-in moderado (mitigado pelo uso de Delta Lake, que é open source)
- ⚠️ Free Edition exige conformidade com termos non-commercial
- ⚠️ Quota diária de compute pode limitar processamentos maiores
### Trade-offs aceitos
 
- Maior complexidade conceitual em troca de flexibilidade
- Dependência de fornecedor único em troca de produtividade
---
 
## Implementação
 
- [x] Criar conta Databricks Free Edition (AWS)
- [x] Conectar repositório Git ao workspace
- [ ] Configurar Unity Catalog (catálogo e schemas)
- [ ] Documentar padrões de uso de Delta Lake
- [ ] Configurar tags de classificação de dados
---
 
## Referências
 
- Inmon, B., & Levins, M. (2021). *Building the Data Lakehouse*. Technics Publications.
- [Databricks: What is a Data Lakehouse?](https://www.databricks.com/glossary/data-lakehouse)
- [Delta Lake — open source storage layer](https://delta.io/)
- [Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/)
---
 
## Histórico
 
| Data | Mudança | Autor |
|---|---|---|
| 2026-04-26 | Criação | @ediney-magalhaes |
