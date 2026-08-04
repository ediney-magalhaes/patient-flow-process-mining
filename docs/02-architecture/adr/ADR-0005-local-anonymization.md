# ADR-0005: Anonimização Local de PII Antes do Upload ao Databricks
 
## Status
 
**Aceito**
 
**Data:** 2026-04-26  
**Decisores:** Ediney Magalhães (Analytics Engineer)  
**Sprint:** 0  
**Relacionado a:** [SECURITY.md](../../../SECURITY.md)
 
---
 
## Contexto
 
O projeto trata **dados sensíveis de saúde** (Art. 5º, II, da LGPD), incluindo 
identificadores diretos de pacientes (nome, prontuário, CPF) e indiretos 
(idade, diagnóstico, especialidade).
 
Restrições legais e operacionais aplicáveis:
 
- **LGPD** exige minimização de dados (Art. 6º, III) e segurança proporcional 
  ao risco (Art. 46-49)
- **Termos do Databricks Free Edition** estabelecem uso non-commercial e 
  ausência de DPA (Data Processing Agreement)
- **Política institucional** do Hospital Santa Rosa sobre tratamento de 
  dados clínicos por terceiros
A pergunta arquitetural: **onde realizar a anonimização?**
 
---
 
## Decisão
 
**A anonimização de PII ocorrerá localmente, no ambiente do hospital, 
antes do upload ao Databricks. Dados originais (com PII) NUNCA trafegam 
ou são armazenados no Databricks.**
 
### Mecanismos adotados
 
1. **Hash SHA-256 com salt** para identificadores que precisam manter 
   consistência (mesmo paciente em múltiplos eventos)
2. **Remoção total** de PII direta sem necessidade analítica (nome, 
   endereço, telefone, e-mail)
3. **Generalização** de dados que poderiam reidentificar (idade exata → 
   faixa etária, data de nascimento → ano)
4. **Salt institucional** mantido em variável de ambiente local, **nunca 
   commitado** em Git ou enviado ao Databricks
---
 
## Alternativas Consideradas
 
### Alternativa A — Anonimização no Databricks (camada Bronze)
 
**Prós:** pipeline mais simples, dados originais disponíveis para 
reprocessamento
 
**Contras:** PII trafega em rede e fica em repouso no Databricks; viola 
princípio de minimização; viola termos non-commercial; expansão da 
superfície de risco
 
**Por que não escolhida:** risco regulatório e de violação contratual 
inaceitável.
 
### Alternativa B — Anonimização em zona intermediária (proxy)
 
**Prós:** centraliza a lógica em um ponto auditável
 
**Contras:** adiciona infraestrutura, custo, ponto único de falha
 
**Por que não escolhida:** complexidade desproporcional ao volume e contexto 
do projeto.
 
### Alternativa C — Anonimização local antes do upload ✅
 
**Prós:**
 
- **Defense-in-depth na origem** (princípio mais seguro)
- PII nunca sai do ambiente controlado do hospital
- Compatível com termos non-commercial do Free Edition
- Reduz superfície de exposição ao mínimo
- Permite reuso do dataset anonimizado em outros contextos sem reanonimizar
- Auditável (script versionado, executado por usuário identificado)
**Contras:**
 
- Dependência de execução manual (mitigado por documentação e automação local)
- Reprocessamento exige re-extração na origem se regras mudarem
---
 
## Consequências
 
### Positivas
 
- ✅ Conformidade plena com LGPD (Art. 12 — dado anonimizado fora de escopo)
- ✅ Conformidade com termos do Databricks Free Edition
- ✅ Segurança máxima na fonte (princípio do mínimo privilégio)
- ✅ Independência regulatória da infraestrutura externa
### Negativas
 
- ⚠️ Etapa manual local exige disciplina operacional
- ⚠️ Re-anonimização necessária se mudarmos regras de pseudonimização
- ⚠️ Risco de re-identificação por linkagem com dados externos requer 
  monitoramento contínuo
### Trade-offs aceitos
 
- Troca de comodidade operacional por segurança máxima
---
 
## Implementação
 
- [ ] Criar módulo `anonymization/anonymize.py` com:
  - `pseudonymize(value, salt)` — SHA-256 com salt
  - `generalize_age(age)` — converte idade em faixa
  - `drop_direct_pii(df, columns)` — remove colunas explicitamente
- [ ] Criar `anonymization/config.yml` com mapeamento de colunas e ação
- [ ] Criar `anonymization/.env.example` (template do salt — sem valor real)
- [ ] Adicionar `.env` ao `.gitignore`
- [ ] Criar testes em `tests/test_anonymization.py` validando:
  - Determinismo (mesmo input + salt = mesmo hash)
  - Não-determinismo entre salts diferentes
  - Cobertura: todas as colunas PII listadas são tratadas
- [ ] Documentar uso em `docs/03-data/lgpd-compliance.md`
---
 
## Referências
 
- [Lei nº 13.709/2018 — LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- ANPD. (2023). *Guia Orientativo sobre Anonimização e Pseudonimização*.
- [Databricks Free Edition — Terms of Use](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- van der Aalst, W. (2016). *Process Mining: Data Science in Action* (2nd ed.). Springer.
---
 
## Histórico
 
| Data | Mudança | Autor |
|---|---|---|
| 2026-04-26 | Criação | @ediney-magalhaes |
