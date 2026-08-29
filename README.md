# Matching Engine

Sistema de cruzamento de ordens (*order matching system*) para um único ativo, com ordens
*limit*, *market* e *pegged*, prioridade preço-tempo e livro de ofertas mantido em memória.

> **Estado do projeto:** em desenvolvimento. As seções marcadas com _a preencher_ dependem da
> interface de linha de comando, ainda não implementada — ver [ROADMAP.md](ROADMAP.md).

---

## Sumário

- [1. Visão geral](#1-visão-geral)
- [2. Requisitos atendidos](#2-requisitos-atendidos)
- [3. Execução](#3-execução)
- [4. Comandos](#4-comandos)
- [5. Arquitetura](#5-arquitetura)
- [6. Estruturas de dados e complexidade](#6-estruturas-de-dados-e-complexidade)
- [7. Decisões de projeto](#7-decisões-de-projeto)
- [8. Testes](#8-testes)
- [9. Limitações conhecidas](#9-limitações-conhecidas)

---

## 1. Visão geral

Uma ordem representa a manifestação de interesse em comprar ou vender um ativo. Uma *matching
engine* é o componente responsável por cruzar essas ordens de forma determinística, respeitando
regras de prioridade previamente estabelecidas.

Este projeto implementa uma engine para um único ativo, sob as seguintes premissas:

- apenas ordens *limit* e *market*, acrescidas do tipo *pegged*;
- armazenamento volátil, sem persistência em disco;
- operações com complexidade adequada, evitando varreduras lineares;
- escopo restrito à lógica de negócio, sem considerações de infraestrutura.

A abordagem adotada separa três responsabilidades. O `PriceLevel` é uma fila duplamente
encadeada que resolve a prioridade temporal dentro de um mesmo preço. O `OrderBook` guarda e
organiza os níveis, oferecendo acesso direto ao melhor preço de cada lado e à ordem de qualquer
identificador, mas **não cria ordens nem decide nada** — é estrutura de dados. Toda regra de
negócio vive na `MatchingEngine`: o que cruza, a que preço, o que repousa, o que é descartado.

Essa separação é o que permite testar cada camada isoladamente e é o motivo de a interface de
linha de comando não ter acesso a nenhuma estrutura interna: ela conversa apenas com a engine.

---

## 2. Requisitos atendidos

### Requisitos base

| # | Requisito | Situação |
|---|---|---|
| B1 | Inserção de ordens com tipo, lado, preço e quantidade | [x] |
| B2 | Ordens *limit* | [x] |
| B3 | Ordens *market* | [x] |
| B4 | Saída `Trade, price: <preço>, qty: <quantidade>` | [x] |
| B5 | Tratamento definido e justificado para ordens *limit* cruzantes | [x] |

### Requisitos adicionais

| # | Requisito | Situação |
|---|---|---|
| A1 | Visualização do livro | [x] |
| A2 | Respeito à ordem de chegada | [x] |
| A3 | Cancelamento de ordens | [x] engine · falta o comando |
| A4 | Alteração de preço e/ou quantidade | [x] engine · falta o comando |
| A5 | Ordens *pegged* | [ ] em andamento |

---

## 3. Execução

### Requisitos de ambiente

Python 3.11 ou superior. Nenhuma dependência de execução — apenas a biblioteca padrão
(`decimal`, `heapq`, `enum`, `dataclasses`, `itertools`). O `pytest` é usado somente para os
testes.

### Instalação

```bash
python -m pip install -e ".[dev]"
```

O projeto adota o layout `src/`, de modo que o pacote só é importável após a instalação em modo
editável — o que garante que os testes exercitem o pacote instalado, e não os arquivos do
diretório de trabalho.

### Uso

> _A preencher: depende da interface de linha de comando._

### Execução dos testes

A partir da raiz do repositório:

```bash
python -m pytest
```

O `pyproject.toml` já define `pythonpath`, `testpaths` e o padrão de nomes, de modo que nenhuma
configuração adicional é necessária.

---

## 4. Comandos

A engine é operada por comandos textuais lidos da entrada padrão.

| Comando | Sintaxe | Descrição |
|---|---|---|
| Ordem *limit* | `limit <side> <price> <qty>` | Ordem passiva a preço fixo |
| Ordem *market* | `market <side> <qty>` | Executada imediatamente ao melhor preço disponível |
| Ordem *pegged* | `peg <bid\|offer> <side> <qty>` | Acompanha o melhor preço de referência |
| Cancelamento | `cancel order <id>` | Remove a ordem da engine |
| Alteração | _a definir_ | Altera preço, quantidade ou ambos |
| Visualização | `print book` | Exibe o estado do livro |

O argumento `<side>` assume os valores `buy` ou `sell`. Nas ordens *limit*, **o preço precede a
quantidade**.

Na ordem *pegged*, o lado e a referência são informados separadamente, conforme a sintaxe do
enunciado. Como apenas pegs passivos são aceitos (§7.7), o lado é redundante nos comandos
válidos e serve como verificação: `peg offer buy` é rejeitado por contradição.

### Exemplo

> _A preencher: sessão de exemplo com entrada e saída reais._

---

## 5. Arquitetura

Quatro módulos, em camadas, cada um dependendo apenas dos anteriores.

| Módulo | Conteúdo | Responsabilidade |
|---|---|---|
| `order.py` | `Side`, `OrderType`, `PegReference`, `Order`, `validate_order_terms`, `format_price` | Domínio. Define o que é uma ordem e o que a torna válida |
| `price_level.py` | `PriceLevel` | Prioridade temporal dentro de um preço. Fila FIFO duplamente encadeada |
| `order_book.py` | `OrderBook` | Organização dos níveis e acesso indexado. Não cria ordens |
| `engine.py` | `Trade`, `MatchingEngine` | Regras de negócio: cruzamento, repouso, cancelamento, alteração, repreçagem |

A validação é centralizada em `validate_order_terms`, chamada do `__post_init__` do `Order` —
que cobre todo caminho de criação — e do `modify`, que é a única operação capaz de alterar preço
ou quantidade depois que a ordem já existe. Nenhuma ordem inválida chega ao livro por qualquer
caminho.

A formatação de preço é centralizada em `format_price` pelo mesmo motivo: `Decimal("10")` e
`Decimal("10.00")` são iguais e ocupam a mesma chave, mas exibem-se diferente. Todo ponto que
imprime preço — as duas colunas do livro, a saída de negócio e as mensagens da interface —
passa por ela, de modo que o mesmo preço nunca aparece com duas grafias.

### Organização do código

```
src/matching_engine/
    order.py         Side, OrderType, PegReference, Order, validações e formatação
    price_level.py   PriceLevel — fila FIFO duplamente encadeada
    order_book.py    OrderBook — três índices e dois heaps
    engine.py        Trade, MatchingEngine
tests/
    test_order.py        validação e construção de ordens
    test_price_level.py  operações da fila
    test_order_book.py   níveis, melhor preço e preço de referência
    test_engine.py       cruzamento, cancelamento, alteração e invariantes
docs/
    DECISIONS.md                          registro das decisões, D01 em diante
    Matching Engine - Guia de Estudo.pdf   teoria e vocabulário
ROADMAP.md
```

---

## 6. Estruturas de dados e complexidade

Três estruturas, cada uma escolhida para um acesso específico.

**Fila duplamente encadeada** (`PriceLevel`). Cada nível de preço é uma fila com ponteiros para
a cabeça e a cauda. A escolha se justifica pelo cancelamento: remover uma ordem de posição
arbitrária é O(1), porque a ordem guarda referências para a anterior e a próxima e não é preciso
percorrer a fila para encontrá-la. Uma lista Python daria O(N) nessa operação, já que `remove` e
`pop(0)` deslocam os elementos seguintes.

**Dicionários** como índices. `bids` e `offers` mapeiam preço para nível, e `orders` mapeia
identificador para ordem. O segundo é o que torna o cancelamento e a alteração O(1): o
identificador leva direto ao objeto, que por sua vez sabe em que nível está.

**Heaps binários** para o melhor preço. `heapq` implementa apenas *min-heap*, então o lado da
compra armazena os preços negados e a leitura desfaz o sinal. A remoção é **preguiçosa**: um
preço nunca é retirado do meio do heap. Quando o topo aponta para um preço que já não existe no
dicionário de níveis, ele é descartado na leitura seguinte. Cada preço é empilhado e descartado
no máximo uma vez, de modo que o custo se amortiza.

| Operação | Complexidade | Estrutura responsável |
|---|---|---|
| Inserção de ordem que repousa | O(1), ou O(log P) se criar um nível | `PriceLevel`, heap |
| Cruzamento | O(K + M log P) | `OrderBook`, `PriceLevel` |
| Cancelamento | O(1) | índice `orders`, fila |
| Alteração de quantidade para menos | O(1) | fila, sem sair da posição |
| Alteração de preço | O(1) + custo do cruzamento + O(log P) | fila, heap |
| Consulta do melhor preço | O(1) na leitura, O(log P) amortizado | heap |
| Preço de referência das *pegged* | O(P log P + N) | varredura dos níveis |
| Repreçagem de ordens *pegged* | O(G × (P log P + N + Q)) | varredura e reinserção ordenada |

Notação: `N` denota o número de ordens, `P` o número de níveis de preço distintos, `K` o número
de ordens consumidas em um cruzamento, `M` o número de níveis esvaziados nesse cruzamento, `G` o
número de ordens *pegged* vivas e `Q` o comprimento da fila de destino.

As duas últimas linhas são as operações caras do projeto, e a razão está em §9.

---

## 7. Decisões de projeto

O enunciado determina que o comportamento adotado seja justificado. Esta seção resume cada
decisão; o registro completo, com alternativas descartadas, está em
[docs/DECISIONS.md](docs/DECISIONS.md).

### 7.1 Ordens *limit* cujo preço geraria negócio

**São executadas.** A ordem consome o lado oposto enquanto o preço for aceitável, e a sobra
repousa ao próprio preço limite.

O enunciado permite qualquer um dos dois comportamentos, desde que justificado. A execução foi
escolhida porque é o que mercados reais fazem com uma ordem marcável; porque ignorar a ordem
deixaria o melhor *bid* maior ou igual à melhor *offer*, um livro cruzado, que é estado inválido
para uma engine; e porque unifica o algoritmo — uma ordem a mercado passa a ser o mesmo
procedimento com o teste de preço irrestrito, em vez de um caminho de código separado.
(`D08`)

### 7.2 Ordem *market* sem liquidez suficiente

**A quantidade não executada é descartada**, jamais repousa. Uma ordem repousada precisa ocupar
um nível de preço, e uma ordem a mercado não tem preço — não há nível onde colocá-la.

O enunciado fixa esse comportamento por exemplo: após uma compra a mercado consumir toda a
oferta disponível, uma venda subsequente encontra o livro de compra intacto, o que só se explica
se o excedente da compra não tiver repousado. É o comportamento conhecido como *immediate or
cancel*. (`D09`)

### 7.3 Granularidade da saída de negócios

**Um negócio por nível de preço**, não por contraparte. Uma ordem que consome várias ordens
repousadas ao mesmo preço produz uma única linha; se varrer vários níveis, produz uma linha por
nível.

O exemplo do enunciado fixa isso: uma compra a mercado de 150 contra duas ordens de venda ao
mesmo preço produz uma linha de 150, não duas linhas. Uma bolsa real emitiria um negócio por par
`(agressora, repousada)`, porque cada execução é um contrato entre participantes identificáveis
— mas este modelo não tem participantes, e a distinção não carregaria informação alguma. (`D07`)

### 7.4 Alteração de quantidade e prioridade na fila

**Aumentar perde prioridade, reduzir mantém.** A ordem alterada conserva o identificador em
qualquer caso.

O enunciado especifica a perda de prioridade na mudança de preço, mas nada diz sobre
quantidade. Adotou-se a convenção de mercado: aumentar pede mais do que a posição na fila
reservava, e portanto vai para o fim; reduzir não prejudica ninguém atrás e mantém a posição.
Quantidade zero é tratada como cancelamento — é a afirmação de que a ordem não é mais desejada —
enquanto quantidade negativa é entrada inválida e rejeitada. (`D10`)

### 7.5 Prioridade das ordens *pegged* na repreçagem

**A ordem *pegged* conserva o `seq` original ao ser repreçada**, e por isso é reinserida na
posição correspondente à sua chegada, não na cauda.

O exemplo do enunciado obriga a isso: após a chegada de uma *limit* que estabelece um novo
melhor preço, a *pegged* aparece **à frente** dessa *limit* no novo nível, embora tenha chegado
ali depois. Inserir na cauda produziria a ordem invertida.

Isso não contradiz §7.4. A distinção é quem provocou a mudança: na alteração foi o dono da
ordem, um pedido novo, e a fila cobra por isso com o `seq` renovado; na repreçagem foi a engine,
sozinha, sem que ninguém pedisse — a ordem continua sendo uma ordem que chegou quando chegou.
(`D14`)

### 7.6 Composição do preço de referência das ordens *pegged*

**O preço de referência é calculado ignorando as próprias ordens *pegged*.** Apenas ordens sem
referência de peg contam.

Sem essa exclusão, uma *pegged* sozinha no topo do livro passa a derivar o preço de si mesma. O
efeito é uma catraca: uma ordem comum consegue empurrá-la para cima, porque nesse instante a
referência vem de fora dela, mas nada consegue trazê-la de volta para baixo, porque na descida
ela é o próprio piso que sustenta. O livro passaria a anunciar um melhor preço que nenhum
participante ofereceu.

A exclusão tem uma segunda consequência, estrutural: como repreçar uma *pegged* não altera
referência alguma, não existe efeito em cadeia, e uma única passada de repreçagem basta. (`D11`)

### 7.7 Ordem *pegged* que resultaria em cruzamento

**Não ocorre, por construção.** Apenas pegs passivos são aceitos: compra com referência no
*bid*, venda com referência na *offer*. Uma compra pegada ao *bid* fica no melhor *bid*, e o
invariante melhor *bid* < melhor *offer* já garante que ela não cruza.

O enunciado define a ordem *pegged* apenas nessa forma e não menciona cruzamento em nenhum
momento. Pegs agressivos — comprar colado à *offer*, vender colado ao *bid* — existem em
mercados reais, mas estariam fora do escopo especificado e, nesta engine, executariam
imediatamente sem jamais repousar, o que os tornaria indistinguíveis de uma ordem a mercado.

Decisão relacionada: uma ordem *pegged* só existe enquanto existir referência. Sem referência
disponível no momento da entrada, é rejeitada; se a referência desaparecer depois, é cancelada.
Deixá-la parada ao último preço conhecido reintroduziria exatamente o preço fantasma que §7.6
elimina. (`D12`, `D13`)

### 7.8 Representação do preço

**`Decimal`, sempre construído a partir de uma cadeia de caracteres.** Preços são comparados por
igualdade exata e usados como chave de dicionário, e `float` introduz erro de representação
binária — `0.1 + 0.2 == 0.3` é falso. Com `Decimal` construído de cadeia, a igualdade se
comporta como esperado. (`D01`)

---

## 8. Testes

76 testes, organizados por camada, executados com `pytest`. Cada módulo tem o seu arquivo, de
modo que uma falha aponta diretamente para a camada responsável.

A verificação principal são os **exemplos do enunciado transcritos literalmente**: os quadros do
livro são comparados linha a linha com a saída de `OrderBook.__str__`. É o critério mais
próximo do que será avaliado.

Complementarmente, os testes da engine terminam chamando `assert_book_invariants`, que verifica
quatro propriedades que devem valer após qualquer operação, seja ela qual for:

1. o livro nunca está cruzado — o melhor *bid* é estritamente menor que a melhor *offer*;
2. nenhum nível vazio permanece no dicionário;
3. o `total_qty` de cada nível é igual à soma das quantidades da sua fila;
4. o `seq` é crescente ao longo da fila de cada nível.

O quarto é o que sustenta a prioridade temporal. A ordem da fila e o `seq` são duas
representações da mesma informação, e mantê-las de acordo é o que permite verificar a prioridade
de forma independente da estrutura que a implementa.

| Camada | Objetivo | Situação |
|---|---|---|
| Exemplos do enunciado | Verificar a conformidade com a especificação | [x] parcial — falta o exemplo das *pegged* |
| Invariantes do livro | Verificar a consistência após cada operação | [x] |
| Teste aleatório (*fuzz*) | Explorar sequências não previstas manualmente | [ ] |
| Casos limítrofes | Cobrir cancelamento e alteração em posições diversas | [x] |

---

## 9. Limitações conhecidas

Restrições assumidas deliberadamente, com o motivo de cada uma.

**Um único ativo, tudo em memória.** Não há símbolo, sessão nem persistência. Reiniciar o
processo apaga o livro. É o escopo do enunciado.

**Sem participantes.** Uma ordem tem lado, tipo, preço e quantidade, mas não tem dono. É por
isso que a agregação de negócios por nível não perde informação (§7.3): duas execuções ao mesmo
preço não diferem em nada além da sequência de chegada da ordem consumida. Assim que o modelo
ganhasse participantes, a saída teria de passar a reportar por contraparte, que é o que
compensação e liquidação exigem.

**Sem concorrência.** A engine é de thread única e as operações são síncronas. Não há travas, e
nada impede que dois chamadores simultâneos corrompam os índices. Um sistema real trataria isso
com uma fila de entrada serializada, e não com travas espalhadas pela estrutura.

**Repreçagem de *pegged* é a operação mais cara.** O cálculo do preço de referência ordena os
níveis do lado e percorre filas, e é refeito para cada *pegged* viva ao fim de toda operação que
possa mexer no topo. Enquanto o número de *pegged* for pequeno, como no escopo deste projeto, o
custo é irrelevante. Para escalar, o caminho seria manter o melhor preço não-*pegged* de cada
lado de forma incremental, atualizado nas quatro operações que o alteram, em vez de recalculá-lo
por varredura — a mesma troca de varredura por índice que os heaps já fazem para o melhor preço.

**Sem tipos de ordem além dos três exigidos.** Não há *stop*, *iceberg*, nem validade além da
sessão. Ordens a mercado são implicitamente *immediate or cancel* (§7.2), e não há como pedir
outro comportamento de validade.

**A precisão do preço não é limitada.** `Decimal` aceita qualquer número de casas decimais, e a
engine não impõe um incremento mínimo de preço. Uma bolsa real rejeitaria preços fora da grade
de negociação.
