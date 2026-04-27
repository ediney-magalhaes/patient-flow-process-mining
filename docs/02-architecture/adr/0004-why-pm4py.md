# ADR-0004: Adoção de PM4Py como Biblioteca de Process Mining
 
## Status
 
**Aceito** (pendente validação de instalação na Free Edition)
 
**Data:** 2026-04-26  
**Decisores:** Ediney Magalhães (Analytics Engineer)  
**Sprint:** 0
 
---
 
## Contexto
 
O coração analítico do projeto é Process Mining — disciplina que descobre 
processos algoritmicamente a partir de event logs. Existem várias ferramentas 
no ecossistema, com perfis distintos (comerciais vs. open source, foco 
acadêmico vs. industrial, GUI vs. programáveis).
 
Requisitos para a ferramenta:
 
- **Open source / custo zero** (alinhado às restrições do projeto)
- **Programável** (integração com pipeline Databricks)
- **Versionável** (código em Git, não cliques em GUI)
- **Reproduzível** (mesma análise gera mesmo resultado)
- **Algoritmos modernos** (Inductive Miner, conformance via alignment)
- **Comunidade ativa** e documentação robusta
- **Compatível com PySpark/Pandas** para integração com Lakehouse
---
 
## Decisão
 
**Adotaremos PM4Py como biblioteca principal de Process Mining, executada 
em notebooks Databricks sobre dados da camada Gold.**
 
> ⚠️ A decisão conceitual está tomada. A validação técnica (instalação via 
> `%pip install pm4py` no compute serverless da Free Edition) será feita no 
> Sprint 3. Se houver incompatibilidade, a alternativa é executar PM4Py 
> localmente com dados exportados do Gold.
 
---
 
## Alternativas Consideradas
 
### Alternativa A — Celonis
 
**Prós:** líder de mercado, UX excepcional, performance enterprise
 
**Contras:** pago (licenciamento alto), proprietário, fechado, modelo SaaS 
não compatível com Databricks Free Edition
 
**Por que não escolhida:** custo incompatível e lock-in alto.
 
### Alternativa B — Disco (Fluxicon)
 
**Prós:** excelente UX, ótimo para descoberta visual rápida
 
**Contras:** não é programável (GUI desktop), não versionável, free limitado
 
**Por que não escolhida:** modelo desktop-GUI não compatível com pipeline 
reproduzível e versionado.
 
### Alternativa C — Apromore Community
 
**Prós:** open source, foco acadêmico forte
 
**Contras:** comunidade menor, menos integração com Python moderno, mais 
voltado a pesquisa que produção
 
**Por que não escolhida:** fit menor com stack do projeto e produção 
analítica contínua.
 
### Alternativa D — PM4Py ✅
 
**Prós:**
 
- Open source (GPL/AGPL)
- Mantido pelo **Fraunhofer Institute** (Alemanha) — credibilidade científica
- API Python pura, compatível com Pandas/PySpark
- Implementa todos os algoritmos modernos:
  - Descoberta: Alpha Miner, Heuristic Miner, **Inductive Miner**
  - Conformance: token replay, **alignment-based**
  - Performance: variant analysis, bottleneck detection
- Suporte nativo a XES (padrão IEEE)
- Documentação extensa com exemplos
- Comunidade ativa no GitHub
**Contras:**
 
- Performance em datasets enormes não é ideal (irrelevante no volume deste projeto)
- Visualizações nativas mais simples que Celonis (compensado por integração 
  com Plotly/Matplotlib)
- Compatibilidade com compute serverless da Free Edition não confirmada
---
 
## Consequências
 
### Positivas
 
- ✅ Custo zero
- ✅ Versionamento total (código em Git)
- ✅ Reproduzibilidade garantida
- ✅ Acesso direto aos algoritmos (não é caixa-preta)
- ✅ Diferencial no mercado brasileiro de saúde — Process Mining programático é raro
### Negativas
 
- ⚠️ Curva de aprendizado da disciplina de Process Mining (não apenas da ferramenta)
- ⚠️ Visualizações precisam de complemento (Streamlit + Plotly)
- ⚠️ Se não instalar na Free Edition, exige fluxo híbrido (dados no Databricks, análise local)
### Trade-offs aceitos
 
- Troca de UX pronta (Celonis/Disco) por flexibilidade e profundidade técnica
---
 
## Implementação
 
- [ ] Validar instalação de PM4Py no compute serverless da Free Edition
- [ ] Adicionar `pm4py` às dependências do projeto
- [ ] Criar notebook de descoberta de processo
- [ ] Definir algoritmos iniciais: Inductive Miner para descoberta, alignment para conformance
- [ ] Documentar conceitos teóricos em `docs/05-process-mining/`
---
 
## Referências
 
- [PM4Py Documentation](https://pm4py.fit.fraunhofer.de/)
- van der Aalst, W. (2016). *Process Mining: Data Science in Action* (2nd ed.). Springer.
- Berti, A., van Zelst, S., & van der Aalst, W. (2019). *Process Mining for Python (PM4Py): Bridging the Gap Between Process- and Data Science*. ICPM Demo.
- [Padrão XES (IEEE 1849-2016)](https://xes-standard.org/)
---
 
## Histórico
 
| Data | Mudança | Autor |
|---|---|---|
| 2026-04-26 | Criação | @ediney-magalhaes |
