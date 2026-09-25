# Modelo de referência fixo vs. recalculado — o que aprendi

## O que é

Em qualquer sistema que compara "o que está acontecendo agora" contra "o
que deveria acontecer", existem duas arquiteturas possíveis para o "deveria
acontecer": ele pode ser **recalculado a cada comparação**, a partir do
próprio dado sendo comparado, ou pode ser um **modelo de referência fixo**,
definido uma vez e reusado em várias comparações subsequentes.

Isso não é exclusivo de Process Mining, é o mesmo par de arquiteturas por
trás do padrão champion/challenger em MLOps: um modelo "campeão" fica fixo
em produção, servindo de referência estável, enquanto "desafiantes" são
testados contra ele antes de substituí-lo. A pergunta de fundo é sempre a
mesma: a régua de comparação deve se mover junto com o que está sendo
medido, ou deve ficar parada para que a medição signifique algo estável ao
longo do tempo?

## O problema do self-referential

Na primeira versão do Conformance Checking do projeto, o Process Tree de
cada fonte era descoberto a partir do próprio mês sendo testado, o mesmo
log servia de base para o modelo e de log de teste contra esse modelo.
Isso produz uma métrica válida sobre "o quão bem um modelo pode descrever
esse comportamento", mas não sobre "o quanto esse comportamento desviou do
esperado", porque não existe "esperado" nenhum fixo, o esperado se
redefine a cada execução, sempre próximo do que está sendo medido.

**Lição:** um modelo descoberto a partir do próprio dado testado tende a
se ajustar bem a ele quase por definição. Isso é adequado para Discovery
(a pergunta é "qual é o processo real?"), mas inadequado para Conformance
(a pergunta é "o processo real desviou do esperado?"), usar a mesma fonte
para as duas coisas confunde as duas perguntas.

## Modelo de referência não elimina a decisão de "qual referência"

Trocar para um modelo de referência fixo não é só "usar um mês diferente", 
é decidir explicitamente qual unidade de tempo representa "o processo
esperado". A decisão tomada no projeto foi o ano civil fechado (12 meses),
não uma janela móvel de N meses, porque um ano fechado produz o mesmo
modelo para todos os meses daquele ano corrente (descoberto uma vez,
reusado repetidamente), enquanto uma janela móvel redescobre o modelo a
cada mês, reintroduzindo parte do mesmo problema que motivou a mudança.

**Lição:** "ter uma referência" e "ter uma referência estável" não são a
mesma coisa. Uma janela móvel ainda é uma referência, mas uma que se move
junto com o tempo, vale perguntar explicitamente se isso é desejável
antes de escolher.

## Bootstrap não é um caso especial, é o mesmo caso com histórico zero

A tentação inicial foi tratar "ainda não tenho histórico suficiente" como
uma exceção separada da regra principal. Na prática, a regra final não
precisou de um caminho de código diferente para isso, "usa tudo que
existir antes do mês corrente" já cobre naturalmente o caso de não existir
nada (resultado: log vazio de "tudo antes", cai no caso seguinte da mesma
cadeia de decisão, "usa o próprio mês"). O bootstrap é só o primeiro ponto
da mesma curva, não uma lógica à parte.

**Lição:** ao desenhar uma regra que "melhora conforme mais dado chega",
vale testar se o caso de dado zero é tratado naturalmente pela regra geral
antes de escrever um `if` especial só para ele, geralmente é sinal de que
a regra geral está bem desenhada quando isso acontece sem esforço extra.

## A checagem de "existe dado suficiente" também precisa da granularidade certa

O erro mais caro desta implementação não foi a decisão arquitetural em si, 
foi implementar a checagem de disponibilidade de histórico numa
granularidade errada (a tabela inteira, quando deveria ser por fonte
individual). Uma fonte com dado contaminado (ver nota sobre `ano_mes` por
evento) fazia a checagem global "pensar" que existia histórico disponível
para todas as fontes, quando na verdade só 3 das 7 tinham qualquer
fragmento, e a maioria desses fragmentos era ruído, não histórico real.

**Lição:** ao implementar uma condição que vai decidir o comportamento de
um laço `for` sobre múltiplas entidades (fontes, neste caso), a própria
condição precisa ser avaliada na mesma granularidade das entidades, uma
condição global aplicada dentro de um laço por entidade é um padrão fácil
de errar silenciosamente, porque o código "parece" certo até alguém
comparar os números com atenção.