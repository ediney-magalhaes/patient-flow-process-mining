# ADR-0002: Adoção da Arquitetura Medallion (Bronze/Silver/Gold)
 
## Status
 
**Aceito**
 
**Data:** 2026-04-26  
**Decisores:** Ediney Magalhães (Analytics Engineer)  
**Sprint:** 0  
**Relacionado a:** [ADR-0001](0001-why-lakehouse.md)
 
---
 
## Contexto
 
Decidido o uso de Lakehouse (ADR-0001), precisamos definir a **organização 
lógica das camadas de dados**. Os dados do projeto têm características 
distintas em diferentes estágios:
 
- Logs brutos exportados do HIS (Excel/CSV) — formato instável, possíveis 
  inconsistências
- Dados validados e enriquecidos para análise técnica
- Dados modelados para consumo por dashboards, ML e Process Mining
Sem uma estratégia clara de camadas, o risco é construir um "data swamp" — 
dados misturados sem propósito definido, dificultando manutenção, debugging e 
reprocessamento.
 
---
 
## Decisão
 
**Adotaremos a Arquitetura Medallion com três camadas claramente delimitadas: 
Bronze (raw), Silver (validated), Gold (business-ready).**
 
```
Excel/CSV → 🥉 Bronze → 🥈 Silver → 🥇 Gold → Consumo
```
 
### Definições
 
**🥉 Bronze — "raw landing zone"**
 
- Cópia fiel dos dados brutos
- Schema flexível (schema evolution habilitado)
- Append-only com metadata de ingestão
- Imutável — dados da Bronze nunca são alterados
**🥈 Silver — "validated single source of truth"**
 
- Dados limpos, deduplicados, enriquecidos
- Schema rígido com validações de qualidade
- Vocabulário controlado, tipos canônicos
- Dimensões historizadas quando aplicável
**🥇 Gold — "business-ready"**
 
- Modelado para consumo específico (Process Mining, BI, ML)
- Agregações e métricas pré-calculadas quando útil
- Múltiplas tabelas Gold para múltiplos casos de uso
---
 
## Alternativas Consideradas
 
### Alternativa A — Modelo Inmon (3NF + Data Marts)
 
**Prós:** consistência teórica forte, governança clara
 
**Contras:** excessivamente normalizado para Lakehouse; performance ruim em 
queries analíticas; pouco aderente a casos de Process Mining
 
**Por que não escolhida:** modelo concebido para DW relacional clássico; 
inadequado para workloads modernos que combinam SQL, Python e ML.
 
### Alternativa B — Kimball puro (Star Schema direto)
 
**Prós:** excelente para BI dimensional clássico
 
**Contras:** não comporta dados semi-estruturados; sem camada de raw para 
auditoria; reprocessamento custoso
 
**Por que não escolhida:** ausência de camada Bronze elimina capacidade de 
recuperação e reprocessamento — crítico para projeto que recebe dados de 
fonte instável (Excel manual).
 
### Alternativa C — Medallion (Bronze/Silver/Gold) ✅
 
**Prós:**
 
- Padrão consolidado pela Databricks e adotado amplamente na indústria
- Separação clara de responsabilidades por camada
- Permite reprocessamento a partir da Bronze
- Múltiplas Gold para múltiplos casos de uso
- Compatível com dimensões historizadas (SCD2)
- Adota o melhor de Inmon (raw histórico) e Kimball (Gold dimensional)
**Contras:**
 
- Maior consumo de storage (mitigado por compressão Delta)
- Latência ligeiramente maior do que single-layer (irrelevante neste projeto)
---
 
## Consequências
 
### Positivas
 
- ✅ Reprocessamento sempre possível a partir da Bronze
- ✅ Auditoria clara: cada camada tem responsabilidade definida
- ✅ Desacoplamento: mudanças em Gold não afetam Silver
- ✅ Padrão da indústria — facilita colaboração e onboarding
### Negativas
 
- ⚠️ Storage triplicado (mesmo dado em 3 camadas)
- ⚠️ Necessidade de pipelines em 2 saltos (Bronze→Silver, Silver→Gold)
### Trade-offs aceitos
 
- Maior complexidade inicial em troca de manutenibilidade a longo prazo
---
 
## Implementação
 
- [ ] Criar schemas no Unity Catalog: `bronze_fluxo`, `silver_fluxo`, `gold_fluxo`
- [ ] Definir convenção de nomenclatura: `<camada>_<entidade>_<sufixo>`
  - Ex: `bronze_emergencia_raw`, `silver_event_log`, `gold_variants_summary`
- [ ] Definir política de retenção por camada
---
 
## Referências
 
- [Medallion Architecture — Databricks](https://www.databricks.com/glossary/medallion-architecture)
- [Best practices for the Medallion Architecture](https://docs.databricks.com/en/lakehouse/medallion.html)
- Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit* (3rd ed.). Wiley.
---
 
## Histórico
 
| Data | Mudança | Autor |
|---|---|---|
| 2026-04-26 | Criação | @ediney-magalhaes |
