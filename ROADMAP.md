# Roadmap — Matching Engine

Plano de construção do sistema de cruzamento de ordens solicitado no processo seletivo.

Cada tarefa traz uma linha **Estudar antes**, indicando o conhecimento necessário para
executá-la. As referências no formato *Guia §N* remetem ao documento
`Matching Engine - Guia de Estudo.pdf`, nesta mesma pasta.

**Prazo: 30/08/2026, 23h59.**

---

## Sobre o projeto

Uma *matching engine* é o componente responsável por cruzar ordens de compra e venda de forma
determinística, respeitando regras de prioridade. Este projeto implementa uma engine para um
único ativo, com ordens *limit*, *market* e *pegged*.

Premissas fixadas pelo enunciado:

- um único ativo, sem segmentação do livro por instrumento;
- armazenamento volátil, sem persistência em disco ou banco de dados;
- complexidade preferencialmente O(N), evitando varreduras lineares;
- escopo restrito à lógica de negócio, sem considerações de infraestrutura;
- linguagem e paradigma livres.

---

## Requisitos

### Entrega e avaliação

- [ ] Projeto publicado em repositório no GitHub
- [ ] Commits incrementais, com mensagens que descrevem as decisões tomadas
- [ ] Nenhum commit concentrando parcela desproporcional da implementação
- [ ] Capacidade de explicar integralmente a base de código, incluindo o que foi produzido com
      auxílio de ferramentas de IA
- [ ] Entrega efetuada até 30/08/2026, 23h59

### Funcionais — base

- [ ] **B1** Inserção de ordens com tipo, lado, preço e quantidade
- [ ] **B2** Ordens *limit*, passivas e a preço fixo
- [ ] **B3** Ordens *market*, executadas ao melhor preço disponível
- [ ] **B4** Saída `Trade, price: <preço>, qty: <quantidade>` a cada negócio
- [ ] **B5** Tratamento definido e justificado para ordens *limit* cujo preço geraria negócio

### Funcionais — adicionais

- [ ] **A1** Visualização do livro
- [ ] **A2** Respeito à ordem de chegada das ordens
- [ ] **A3** Cancelamento, com remoção efetiva da engine
- [ ] **A4** Alteração de preço, quantidade ou ambos, com reposicionamento na fila
- [ ] **A5** Ordens *pegged*, acompanhando o *bid* ou o *offer*

As decisões de projeto exigidas pelo enunciado são registradas na seção 7 do `README.md`.

---

## Tarefas

### 1. Preparação do repositório

Estrutura do projeto e início do histórico de versionamento.

**Estudar antes:** comandos básicos de Git; convenções de mensagem de commit; `.gitignore`.

- [ ] Criar o repositório no GitHub e vinculá-lo à pasta local
- [ ] Definir a estrutura de diretórios, separando código-fonte e testes
- [ ] Adicionar `.gitignore`
- [ ] Criar o `README.md` inicial
- [ ] Registrar o primeiro commit

**Pronto quando:** `git log` mostra ao menos um commit, `git status` está limpo, o repositório abre no GitHub exibindo o README, e `git ls-files` não lista nenhum artefato de execução.

### 2. Modelo de domínio

Entidades e representação do preço, antes de qualquer lógica.

**Estudar antes:** vocabulário do domínio (*Guia §1*); `dataclasses` e `enum`; erros de
arredondamento em ponto flutuante e alternativas (*Guia §13*); contadores monotônicos
(*Guia §5*).

**Ferramentas:** `dataclasses.dataclass` · `enum.Enum` · `itertools.count` · `decimal.Decimal` — *Guia §8*.

- [ ] Definir a entidade que representa uma ordem
- [ ] Definir os tipos enumerados para lado e tipo de ordem
- [ ] Fixar a representação do preço — decisão estrutural, cara de reverter
- [ ] Estabelecer o gerador de identificadores e o contador de ordem de chegada

**Pronto quando:** é possível criar duas ordens ao mesmo preço e determinar, pelo número de sequência, qual chegou primeiro. Na representação de preço adotada, somar 0,10 e 0,20 e comparar com 0,30 devolve verdadeiro.

### 3. Fila do nível de preço

Estrutura que sustenta a prioridade temporal, com remoção em tempo constante.

**Estudar antes:** nós; listas simplesmente e duplamente encadeadas; referências em Python;
fila FIFO; por que `list.pop(0)` é O(N); nós-sentinela — *Guia §6*.

- [ ] Implementar a fila duplamente encadeada, com cabeça e cauda
- [ ] Implementar inserção na cauda
- [ ] Implementar remoção da cabeça
- [ ] Implementar remoção de nó arbitrário, sem percorrer a fila
- [ ] Manter a quantidade agregada do nível atualizada
- [ ] Testar remoção na cabeça, no meio e na cauda

**Pronto quando:** numa fila de três ordens, remover a do meio mantém as outras duas corretamente ligadas e a quantidade agregada igual à soma das restantes — sem que o método percorra a fila.

### 4. Livro de ofertas

Índices que localizam o melhor preço, um nível e uma ordem específica.

**Estudar antes:** tabelas de dispersão (*Guia §7*); heap binário e `heapq`; representação de
*max-heap* por negação da chave (*Guia §8*); remoção preguiçosa (*Guia §7*).

**Ferramentas:** `dict` · `heapq.heappush` · `heapq.heappop` · `sortedcontainers.SortedDict` (alternativa) — *Guia §8*.

- [ ] Implementar o índice de preço para nível, por lado
- [ ] Implementar o índice de identificador para ordem
- [ ] Implementar a estrutura de ranking de preços, por lado
- [ ] Implementar as consultas de melhor preço de compra e de venda
- [ ] Implementar criação e remoção automática de níveis vazios
- [ ] Testar os invariantes de consistência

**Pronto quando:** inserindo compras a 10, 9,99 e 9,98 em ordem arbitrária, a consulta de melhor compra devolve 10; esvaziado um nível, ele deixa de existir e o melhor preço passa ao seguinte.

### 5. Visualização do livro

Atende ao requisito A1 e serve de instrumento de depuração para todas as etapas seguintes.

**Estudar antes:** formatação e alinhamento de cadeias de caracteres; exibição por ordem
individual em vez de nível agregado (*Guia §10*).

- [ ] Implementar a apresentação em duas colunas
- [ ] Exibir cada ordem individualmente, preservando a fila
- [ ] Verificar contra o livro hipotético do requisito adicional 4

**Pronto quando:** o livro do requisito adicional 4 é exibido com as compras em ordem decrescente de preço e as vendas em ordem crescente, uma linha por ordem.

### 6. Inserção de ordens limit

Ordens sem contraparte repousam no livro, na posição correta.

**Estudar antes:** gramática dos comandos e a ordem dos argumentos (*Guia §2*); prioridade
preço-tempo (*Guia §5*); modelo orientado a eventos (*Guia §3*).

- [ ] Implementar a inserção, ainda sem cruzamento
- [ ] Atribuir identificador e número de sequência a cada ordem aceita
- [ ] Conferir, pela visualização, a ordenação entre níveis e dentro do nível

**Pronto quando:** os três primeiros comandos do exemplo do enunciado produzem um livro com uma compra e duas vendas, com a venda de 100 à frente da de 200 no mesmo nível.

### 7. Motor de cruzamento

Lógica central de casamento de ordens. É a etapa mais importante do projeto.

**Estudar antes:** distinção entre cruzamento e execução; regra do preço da ordem passiva;
regra da quantidade mínima; varredura de níveis; significado de limite numa ordem *limit* —
*Guia §4*. Fluxo completo do comando — *Guia §9*.

- [ ] Implementar o laço de cruzamento, com o critério de aceitação parametrizado
- [ ] Emitir a saída `Trade` no formato exato do enunciado
- [ ] Remover ordens integralmente executadas e níveis esvaziados
- [ ] Depositar no livro a quantidade remanescente da ordem agressora
- [ ] Reproduzir o exemplo do enunciado como teste automatizado
- [ ] Registrar no `README.md` a decisão sobre ordens *limit* cruzantes

**Pronto quando:** a sequência completa do exemplo do enunciado produz exatamente as três linhas `Trade` esperadas. Além disso, `limit buy 25 250` contra vendas de 100 @ 20, 100 @ 22 e 100 @ 26 gera dois negócios — a 20 e a 22 — e deixa 50 repousando a 25.

### 8. Ordens a mercado

Caso particular do algoritmo anterior, com aceitação irrestrita de preço.

**Estudar antes:** comportamento da quantidade não executada por insuficiência de liquidez,
conforme fixado pelos exemplos do enunciado — *Guia §3*.

- [ ] Implementar o critério de aceitação irrestrita
- [ ] Descartar a quantidade remanescente, sem depositá-la no livro
- [ ] Testar o caso de liquidez insuficiente

**Pronto quando:** `market buy 200` contra 150 disponíveis imprime `Trade, price: 20, qty: 150` e o lado das vendas fica vazio: os 50 remanescentes não repousam no livro.

### 9. Cancelamento

Atende ao requisito A3.

**Estudar antes:** remoção de nó em lista duplamente encadeada (*Guia §6*); consistência entre
índices que referenciam a mesma ordem.

- [ ] Localizar a ordem pelo identificador
- [ ] Remover da fila do nível e do índice de identificadores
- [ ] Atualizar a quantidade agregada e remover o nível, se esvaziado
- [ ] Emitir a saída `Order cancelled`
- [ ] Definir e documentar o comportamento para identificador inválido
- [ ] Testar o cancelamento nas três posições da fila

**Pronto quando:** o exemplo do requisito adicional 3 é reproduzido — `Order cancelled` é emitido e a ordem desaparece do livro. Cancelar a ordem do meio de uma fila de três preserva a ligação entre as outras duas.

### 10. Alteração de ordens

Atende ao requisito A4.

**Estudar antes:** regra do enunciado quanto à perda de prioridade na alteração de preço;
prática de mercado quanto à alteração de quantidade — *Guia §10*.

- [ ] Definir a sintaxe do comando, não especificada no enunciado
- [ ] Implementar a alteração de preço, com reposicionamento
- [ ] Implementar a alteração de quantidade, com a regra de prioridade adotada
- [ ] Verificar contra o exemplo do requisito adicional 4
- [ ] Registrar a regra adotada no `README.md`

**Pronto quando:** o exemplo do requisito adicional 4 é reproduzido: alterada a compra de 200 @ 10 para 9,98, o livro passa a exibir 100 @ 9,99 acima de 200 @ 9,98.

### 11. Ordens pegged

Atende ao requisito A5. É a etapa de maior complexidade conceitual.

**Estudar antes:** preço de referência; os quatro eventos que alteram o topo do livro;
repreçagem síncrona; risco de cascata; a tensão entre os requisitos adicionais 4 e 5 —
*Guia §11*.

- [ ] Implementar o registro das ordens *pegged* por lado e referência
- [ ] Implementar o cálculo da referência, excluindo as próprias ordens *pegged*
- [ ] Implementar o gatilho de repreçagem ao fim de toda operação que altere o topo
- [ ] Definir e documentar o comportamento sem preço de referência disponível
- [ ] Definir e documentar o comportamento de ordem *pegged* que resultaria em cruzamento
- [ ] Definir e documentar a regra de prioridade na repreçagem
- [ ] Reproduzir a sequência do requisito adicional 5

**Pronto quando:** a sequência do requisito adicional 5 é reproduzida integralmente, inclusive com a ordem *pegged* posicionada à frente da *limit* de 300 no nível de 10,1. Cancelada a ordem que define o *bid*, a *pegged* acompanha o novo melhor preço.

### 12. Interface de linha de comando

Exposição das funcionalidades por comandos textuais.

**Estudar antes:** leitura da entrada padrão; análise sintática de comandos; separação entre
apresentação e lógica de negócio — *Guia §13*.

- [ ] Implementar o laço de leitura e o analisador de comandos
- [ ] Mapear cada comando ao método correspondente da engine
- [ ] Tratar entradas malformadas sem interromper a execução
- [ ] Assegurar que a engine permaneça independente da interface

**Pronto quando:** o bloco de comandos do enunciado, colado no terminal, produz a saída esperada; e uma entrada malformada devolve mensagem de erro sem encerrar a sessão.

### 13. Suíte de testes

Verificação sistemática da correção.

**Estudar antes:** `unittest` ou `pytest` (*Guia §8*); invariantes; teste aleatório e a
importância de fixar a semente — *Guia §14*.

**Ferramentas:** `unittest` ou `pytest` · `random.Random` com semente fixa — *Guia §8*.

- [ ] Transcrever todos os exemplos do enunciado como testes
- [ ] Verificar os invariantes após cada operação
- [ ] Implementar o teste aleatório sobre sequências extensas
- [ ] Cobrir os casos limítrofes de cancelamento e alteração

**Pronto quando:** um único comando executa toda a suíte com sucesso, e o teste aleatório percorre alguns milhares de operações sem violar nenhum invariante.

### 14. Documentação

Registro das decisões técnicas, conforme exigido pelo enunciado.

**Estudar antes:** notação assintótica, para a análise de complexidade.

- [ ] Redigir as instruções de instalação e execução
- [ ] Descrever a arquitetura e as estruturas de dados adotadas
- [ ] Apresentar a análise de complexidade por operação
- [ ] Justificar cada decisão da seção 7 do `README.md`
- [ ] Registrar as limitações conhecidas

**Pronto quando:** uma pessoa que nunca viu o projeto consegue cloná-lo, executá-lo e reproduzir os exemplos usando apenas o `README.md`, e cada decisão da seção 7 tem justificativa escrita.

---

## Cronograma

O último dia é margem: nenhuma implementação deve ser planejada para 30/08.

| Data | Tarefas |
|---|---|
| Dom 23/08 | 1 · 2 |
| Seg 24/08 | 3 |
| Ter 25/08 | 4 · 5 |
| Qua 26/08 | 6 · 7 |
| Qui 27/08 | 8 · 9 · 10 |
| Sex 28/08 | 11 |
| Sáb 29/08 | 12 · 13 · 14 |
| Dom 30/08 | Revisão, conferência do histórico e entrega |

A tarefa 11 recebeu um dia inteiro por ser a de maior complexidade e a única sem precedente nas
anteriores. Havendo atraso, é a que deve ser preservada: trata-se de requisito obrigatório.

Os testes das tarefas 3 e 4 são escritos junto com o código. A tarefa 13 consolida e amplia,
não inaugura.
