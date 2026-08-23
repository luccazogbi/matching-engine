# Roadmap — Matching Engine

Plano de construção do sistema de cruzamento de ordens solicitado no processo seletivo para a
vaga de estágio na área de Strats.

Cada etapa declara o conhecimento necessário para executá-la. A recomendação é estudar esses
pontos antes de escrever a etapa correspondente: o custo de meia hora de leitura é
sistematicamente menor que o de uma refatoração.

O material teórico de apoio está em **`Matching Engine - Guia de Estudo.pdf`**, nesta mesma
pasta. As referências no formato *Guia §N* remetem às seções daquele documento.

**Prazo de entrega: 30/08/2026, 23h59.**

---

## Índice

1. [Contexto e escopo](#1-contexto-e-escopo)
2. [Requisitos de entrega e critérios de avaliação](#2-requisitos-de-entrega-e-critérios-de-avaliação)
3. [Requisitos funcionais](#3-requisitos-funcionais)
4. [Etapas de construção](#4-etapas-de-construção)
5. [Decisões de projeto a documentar](#5-decisões-de-projeto-a-documentar)
6. [Cronograma](#6-cronograma)
7. [Checklist de entrega](#7-checklist-de-entrega)

---

## 1. Contexto e escopo

Uma *matching engine* é o sistema responsável por cruzar ordens de compra e venda em uma bolsa,
de forma determinística e respeitando regras de prioridade. O objetivo do exercício é demonstrar
domínio de estruturação de dados, algoritmos e engenharia de software.

Premissas fixadas pelo enunciado:

| Premissa | Consequência para o projeto |
|---|---|
| Um único ativo | Não há necessidade de segmentar o livro por instrumento |
| Apenas ordens *limit* e *market* | Dois tipos, mais o tipo *pegged* exigido nos requisitos adicionais |
| Armazenamento volátil | Tudo em memória; nenhuma persistência em disco ou banco de dados |
| Sem preocupação com escalabilidade de infraestrutura | Nenhuma discussão sobre nuvem, contêineres ou elasticidade |
| Complexidade preferencialmente O(N) | As operações não devem depender de varreduras lineares evitáveis |

O paradigma é livre: estrutural ou orientado a objetos. A linguagem também é livre.

---

## 2. Requisitos de entrega e critérios de avaliação

Esta seção consolida as exigências formais comunicadas por e-mail. São condições de
elegibilidade da entrega, independentes da qualidade técnica do código.

### 2.1 Prazo e forma de entrega

| Item | Definição |
|---|---|
| Prazo | 30/08/2026, até 23h59 |
| Forma de entrega | Repositório no GitHub |
| Linguagem de programação | Livre |
| Canal para dúvidas | Resposta ao e-mail recebido |

### 2.2 Autoria e responsabilidade

O uso de ferramentas de inteligência artificial é permitido. Entretanto, o candidato é
integralmente responsável pelo código entregue e deve conhecer e conseguir explicar toda a base
de código, incluindo decisões técnicas, comportamentos, limitações e testes. Para todos os
efeitos da avaliação, o código produzido com auxílio de IA é considerado de autoria e
responsabilidade do candidato.

**Implicação prática.** Nenhum trecho deve ser incorporado ao projeto sem compreensão plena.
Ao final de cada etapa, convém verificar se é possível explicar, sem consultar o código, o que
foi implementado e por quê.

### 2.3 Histórico de versionamento

O histórico Git integra a avaliação. As exigências são explícitas:

- manter **commits incrementais**;
- redigir **mensagens claras**;
- demonstrar a **evolução da solução e as decisões tomadas**;
- **evitar concentrar toda a implementação em um único commit final**.

**Implicação prática.** O repositório deve ser criado antes da primeira linha de código, e cada
etapa da seção 4 corresponde a pelo menos um commit. Mensagens devem descrever a decisão, não
apenas o arquivo alterado.

### 2.4 Abrangência

Todos os requisitos descritos no enunciado, **incluindo os requisitos adicionais**, são
obrigatórios. Não há itens opcionais.

### 2.5 Verificação

| Verificação | Situação |
|---|---|
| Repositório GitHub criado e acessível | [ ] |
| Histórico com commits incrementais e mensagens descritivas | [ ] |
| Nenhum commit concentrando a implementação | [ ] |
| Os cinco requisitos adicionais implementados | [ ] |
| Capacidade de explicar integralmente a base de código | [ ] |
| Entrega realizada dentro do prazo | [ ] |

---

## 3. Requisitos funcionais

Extraídos do enunciado. A coluna de etapa remete à seção 4 deste documento.

### 3.1 Requisitos base

| # | Requisito | Etapa |
|---|---|---|
| B1 | Inserção de ordens com tipo, lado, preço (quando *limit*) e quantidade | 4.6 |
| B2 | Ordens *limit* — passivas, a preço fixo | 4.6 |
| B3 | Ordens *market* — executadas ao melhor preço disponível imediatamente | 4.8 |
| B4 | Emissão da saída `Trade, price: <preço>, qty: <quantidade>` a cada negócio | 4.7 |
| B5 | Definição justificada do tratamento de ordens *limit* que gerariam negócio | 4.7 · 5 |

### 3.2 Requisitos adicionais

| # | Requisito | Etapa |
|---|---|---|
| A1 | Função ou método para visualização do livro | 4.5 |
| A2 | Respeito à ordem de chegada das ordens | 4.3 · 4.7 |
| A3 | Cancelamento, com remoção efetiva da ordem da engine | 4.9 |
| A4 | Alteração de preço, quantidade ou ambos, com reposicionamento na fila | 4.10 |
| A5 | Ordens *pegged*, acompanhando o *bid* ou o *offer* | 4.11 |

---

## 4. Etapas de construção

As etapas estão em ordem de dependência. Cada uma pressupõe a anterior concluída e testada.

---

### 4.1 Preparação do repositório

**Objetivo.** Estabelecer a estrutura do projeto e iniciar o histórico de versionamento antes
de qualquer implementação.

**Conhecimento necessário**
- Comandos básicos de Git: `init`, `add`, `commit`, `push`, `log`
- Convenções de mensagem de commit (modo imperativo, assunto conciso, corpo explicativo)
- Finalidade e sintaxe do arquivo `.gitignore`
- Organização de um projeto Python em pacotes e módulos

**Tarefas**
1. Criar o repositório no GitHub e clonar localmente.
2. Definir a estrutura de diretórios, separando o código-fonte dos testes.
3. Adicionar `.gitignore` apropriado à linguagem escolhida.
4. Criar o `README.md` inicial, contendo ao menos o enunciado do problema e as instruções de
   execução previstas.
5. Registrar o primeiro commit.

**Critério de conclusão.** Repositório publicado, com histórico iniciado e estrutura definida.

---

### 4.2 Modelo de domínio

**Objetivo.** Definir as entidades e a representação do preço antes de qualquer lógica.

**Conhecimento necessário**
- Vocabulário do domínio: ordem, lado, quantidade, preço, livro, *bid*, *offer*, *spread*,
  nível de preço, ordem passiva e agressora — *Guia §1*
- Definição de classes e uso de `dataclasses`; diferença entre atributos mutáveis e imutáveis
- Tipos enumerados (`enum.Enum`) e sua vantagem sobre cadeias de caracteres literais
- Representação exata de valores monetários: aritmética de ponto flutuante e seus erros de
  arredondamento; alternativas por inteiro em centavos ou `Decimal` — *Guia §13*
- Contadores monotônicos e determinismo — *Guia §5*

**Tarefas**
1. Definir a entidade que representa uma ordem, com seus atributos.
2. Definir os tipos enumerados para lado e tipo de ordem.
3. **Decidir e fixar a representação do preço.** Esta decisão é estrutural e cara de reverter.
4. Estabelecer o gerador de identificadores e o contador de número de sequência de chegada.

**Critério de conclusão.** É possível instanciar ordens e compará-las por prioridade de chegada.

> **Atenção.** A representação do preço em ponto flutuante compromete comparações de igualdade
> e, por consequência, a identificação de níveis de preço. Recomenda-se inteiro em centavos.

---

### 4.3 Fila do nível de preço

**Objetivo.** Implementar a estrutura que sustenta a prioridade temporal dentro de um nível de
preço, com remoção em tempo constante em qualquer posição.

**Conhecimento necessário**
- Conceito de **nó**: objeto que armazena um dado e referências para seus vizinhos — *Guia §6*
- **Listas encadeadas**: diferença entre simples e duplamente encadeada, e por que apenas a
  segunda permite remoção em tempo constante — *Guia §6*
- **Referências em Python**: a linguagem não possui ponteiros; variáveis são referências a
  objetos, e dois nomes podem designar o mesmo objeto — *Guia §6*
- **Fila FIFO**: inserção pela cauda, remoção pela cabeça
- **Análise de complexidade**: por que `list.pop(0)` e a busca por índice são O(N), e por que
  isso inviabiliza o requisito de cancelamento — *Guia §6*
- Tratamento das extremidades e a técnica dos **nós-sentinela**

**Tarefas**
1. Implementar a fila duplamente encadeada, mantendo referências para cabeça e cauda.
2. Implementar inserção na cauda.
3. Implementar remoção da cabeça.
4. Implementar remoção de um nó arbitrário, sem percorrer a fila.
5. Manter a quantidade agregada do nível atualizada a cada operação.
6. Escrever os testes desta estrutura isoladamente, incluindo remoção na cabeça, no meio e na
   cauda.

**Critério de conclusão.** As quatro operações executam em tempo constante e os testes cobrem
as três posições de remoção.

---

### 4.4 O livro de ofertas

**Objetivo.** Compor os índices que permitem localizar o melhor preço, um nível específico e
uma ordem específica, cada um em tempo adequado.

**Conhecimento necessário**
- Tabelas de dispersão (`dict`): custo de inserção e busca — *Guia §7*
- **Heap binário** e o módulo `heapq`: custo das operações, e o fato de existir apenas
  *min-heap* — *Guia §8*
- Técnica de representar um *max-heap* por negação da chave — *Guia §8*
- **Remoção preguiçosa**: por que não se remove um elemento do meio de um heap, e como
  descartar entradas obsoletas na leitura — *Guia §7*
- Alternativa por mapa ordenado (`SortedDict`) e seus compromissos
- Noção de invariante de estrutura de dados

**Tarefas**
1. Implementar o índice de preço para nível, por lado.
2. Implementar o índice de identificador para ordem.
3. Implementar a estrutura de ranking de preços, por lado.
4. Implementar as consultas de melhor preço de compra e melhor preço de venda.
5. Implementar a criação e a remoção automática de níveis vazios.
6. Escrever os testes dos invariantes: coerência entre a quantidade agregada e a soma das
   ordens; ausência de níveis vazios remanescentes.

**Critério de conclusão.** O livro aceita ordens em múltiplos níveis e responde corretamente
qual é o melhor preço de cada lado.

---

### 4.5 Visualização do livro

**Objetivo.** Atender ao requisito A1 e, sobretudo, dispor de um instrumento de depuração para
todas as etapas seguintes.

**Conhecimento necessário**
- Formatação e alinhamento de cadeias de caracteres
- Ordenação de exibição: compras do maior para o menor preço, vendas do menor para o maior
- Distinção entre exibir ordens individualmente ou níveis agregados, e por que a primeira
  alternativa permite verificar a prioridade — *Guia §10*

**Tarefas**
1. Implementar a apresentação em duas colunas, conforme os exemplos do enunciado.
2. Exibir cada ordem individualmente, preservando a ordem da fila.
3. Verificar a saída contra o livro hipotético apresentado no requisito adicional 4.

**Critério de conclusão.** A visualização reproduz a disposição dos exemplos do enunciado.

> Esta etapa é deliberadamente antecipada. Todas as etapas seguintes serão depuradas por
> inspeção visual do livro.

---

### 4.6 Inserção de ordens limit

**Objetivo.** Permitir que ordens *limit* sem contraparte repousem no livro, respeitando a
prioridade preço-tempo.

**Conhecimento necessário**
- Gramática dos comandos e a ordem dos argumentos: em `limit buy 10 100`, o preço precede a
  quantidade — *Guia §2*
- **Prioridade preço-tempo**: primeiro o melhor preço; em caso de empate, a ordem de chegada
  — *Guia §5*
- Modelo orientado a eventos: o livro é alterado exclusivamente pela chegada de comandos, sem
  qualquer temporizador — *Guia §3*

**Tarefas**
1. Implementar a inserção, sem cruzamento por ora.
2. Atribuir identificador e número de sequência a cada ordem aceita.
3. Verificar, pela visualização, que a ordenação entre níveis e a fila dentro do nível estão
   corretas.

**Critério de conclusão.** Sucessivas ordens não cruzantes formam um livro coerente.

---

### 4.7 Motor de cruzamento

**Objetivo.** Implementar a lógica central de casamento de ordens. Esta é a etapa mais
importante do projeto.

**Conhecimento necessário**
- Distinção entre **cruzamento** (a decisão de compatibilidade de preços) e **execução**
  (a transferência de quantidade e a atualização das estruturas) — *Guia §4*
- Regra do **preço da ordem passiva**: o negócio ocorre ao preço da ordem que já estava no
  livro, não ao da ordem agressora — *Guia §4*
- Regra da **quantidade mínima** entre as duas ordens envolvidas — *Guia §4*
- Conceito de **varredura de níveis**: uma ordem pode consumir vários níveis, cada um ao
  respectivo preço — *Guia §4*
- Significado de **limite** em uma ordem *limit*: é o pior preço aceitável, não o preço
  pretendido — *Guia §4*
- Preenchimento parcial e ordens remanescentes
- Fluxo completo de processamento de um comando — *Guia §9*

**Tarefas**
1. Implementar o laço de cruzamento, parametrizando o critério de aceitação de preço.
2. Emitir a saída `Trade, price: <preço>, qty: <quantidade>` no formato exato do enunciado.
3. Remover as ordens integralmente executadas e os níveis esvaziados.
4. Depositar no livro a quantidade remanescente da ordem agressora.
5. Reproduzir integralmente o exemplo do enunciado como teste automatizado.

**Critério de conclusão.** A sequência de comandos do enunciado produz exatamente a saída
esperada.

> **Decisão a justificar.** O enunciado admite ignorar ou preencher ordens *limit* cujo preço
> geraria negócio. Recomenda-se preencher: é o comportamento de mercado e unifica o algoritmo,
> tornando a ordem *market* um caso particular de ordem *limit*. A justificativa deve constar
> do `README.md`.

---

### 4.8 Ordens a mercado

**Objetivo.** Atender ao requisito B3.

**Conhecimento necessário**
- Ordem *market* como caso particular do algoritmo anterior, com aceitação irrestrita de preço
- Comportamento da quantidade não executada por insuficiência de liquidez, conforme fixado
  pelos exemplos do enunciado — *Guia §3*

**Tarefas**
1. Implementar o critério de aceitação irrestrita.
2. Descartar a quantidade remanescente, sem depositá-la no livro.
3. Testar o caso de liquidez insuficiente contra os exemplos do enunciado.

**Critério de conclusão.** Os três comandos *market* do exemplo produzem as saídas esperadas.

> Uma ordem a mercado nunca repousa no livro.

---

### 4.9 Cancelamento

**Objetivo.** Atender ao requisito A3.

**Conhecimento necessário**
- Operação de remoção de nó em lista duplamente encadeada — *Guia §6*
- Necessidade de manter consistentes todos os índices que referenciam a ordem removida
- Tratamento de casos limítrofes: identificador inexistente, ordem já cancelada, ordem já
  integralmente executada

**Tarefas**
1. Implementar a localização da ordem pelo identificador.
2. Remover a ordem da fila do nível e do índice de identificadores.
3. Atualizar a quantidade agregada e remover o nível, se esvaziado.
4. Emitir a saída `Order cancelled`.
5. Definir e documentar o comportamento para identificador inválido.
6. Testar o cancelamento nas três posições da fila.

**Critério de conclusão.** O cancelamento executa em tempo constante e preserva os invariantes
do livro.

> Se esta etapa exigir percorrer alguma estrutura, a modelagem da etapa 4.3 deve ser revista.

---

### 4.10 Alteração de ordens

**Objetivo.** Atender ao requisito A4.

**Conhecimento necessário**
- Regra explícita do enunciado: a alteração de preço implica **perda de prioridade**, com
  reposicionamento ao final da fila do novo nível — *Guia §10*
- Prática de mercado quanto à alteração de quantidade: o aumento implica perda de prioridade;
  a redução a preserva — *Guia §10*
- Vantagem de modelar a alteração como remoção seguida de reinserção

**Tarefas**
1. Definir a sintaxe do comando de alteração, não especificada no enunciado.
2. Implementar a alteração de preço, com reposicionamento.
3. Implementar a alteração de quantidade, aplicando a regra de prioridade adotada.
4. Verificar contra o exemplo do requisito adicional 4.
5. Documentar a regra adotada para alteração de quantidade.

**Critério de conclusão.** O exemplo do enunciado é reproduzido, com a ordem alterada
efetivamente no fim da fila do novo nível.

---

### 4.11 Ordens pegged

**Objetivo.** Atender ao requisito A5. Esta é a etapa de maior complexidade conceitual.

**Conhecimento necessário**
- Conceito de ordem *pegged* e de preço de referência — *Guia §11*
- Os quatro eventos que alteram o topo do livro: chegada de ordem melhor, cancelamento da
  ordem do topo, alteração de preço da ordem do topo e consumo integral do nível de topo
  — *Guia §11*
- Compreensão de que a repreçagem é **síncrona**, executada ao final da operação que alterou o
  topo, sem qualquer monitoramento contínuo — *Guia §3 e §11*
- Risco de **cascata de repreçagem** e sua prevenção pela exclusão das próprias ordens
  *pegged* do cálculo da referência — *Guia §11*
- Tensão aparente entre o requisito adicional 4 e o exemplo do requisito adicional 5 quanto à
  preservação de prioridade — *Guia §11*

**Tarefas**
1. Implementar o registro das ordens *pegged* por lado e referência.
2. Implementar o cálculo do preço de referência, excluindo as próprias ordens *pegged*.
3. Implementar o gatilho de repreçagem ao final de toda operação que possa alterar o topo.
4. Definir e documentar o comportamento quando não houver preço de referência disponível.
5. Definir e documentar o comportamento de uma ordem *pegged* que resultaria em cruzamento.
6. Definir e documentar a regra de prioridade na repreçagem.
7. Reproduzir a sequência de três comandos do requisito adicional 5.

**Critério de conclusão.** A ordem *pegged* acompanha a referência nos quatro eventos, e o
exemplo do enunciado é reproduzido.

> **Decisão a justificar.** O requisito adicional 4 determina que a alteração de preço acarreta
> perda de prioridade, mas o exemplo do requisito adicional 5 exibe a ordem *pegged* repreçada
> à frente de uma ordem *limit* recém-inserida no mesmo nível. A conciliação possível consiste
> em distinguir a origem da alteração: no primeiro caso ela decorre de ato do participante; no
> segundo, de ato da própria engine. A identificação e a justificativa desta distinção têm peso
> na avaliação.

---

### 4.12 Interface de linha de comando

**Objetivo.** Expor as funcionalidades por meio de comandos textuais, conforme os exemplos.

**Conhecimento necessário**
- Leitura de entrada padrão e laço de repetição
- Análise sintática de comandos e validação de argumentos
- Princípio de separação entre a camada de apresentação e a lógica de negócio — *Guia §13*

**Tarefas**
1. Implementar o laço de leitura e o analisador de comandos.
2. Mapear cada comando ao método correspondente da engine.
3. Tratar entradas malformadas sem interromper a execução.
4. Assegurar que a engine permaneça independente da interface.

**Critério de conclusão.** A sessão interativa reproduz os exemplos do enunciado.

> A lógica de negócio não deve conter chamadas de entrada ou saída. Os testes invocam os
> métodos diretamente.

---

### 4.13 Suíte de testes

**Objetivo.** Demonstrar a correção da implementação e a existência de verificação sistemática.

**Conhecimento necessário**
- Estrutura de testes automatizados (`unittest` ou `pytest`) — *Guia §8*
- Conceito de **invariante** e sua verificação após cada operação — *Guia §14*
- Conceito de **teste aleatório** (*fuzz*) e a importância de fixar a semente para
  reprodutibilidade — *Guia §14*

**Tarefas**
1. Transcrever todos os exemplos do enunciado como testes.
2. Implementar a verificação dos invariantes: livro não cruzado; coerência da quantidade
   agregada; integridade do índice de identificadores; ausência de quantidades não positivas.
3. Implementar o teste aleatório sobre sequências extensas de operações.
4. Cobrir os casos limítrofes de cancelamento e alteração.

**Critério de conclusão.** Todos os testes são executados com sucesso a partir de um comando
único.

---

### 4.14 Documentação

**Objetivo.** Registrar as decisões técnicas, conforme exigido pelo enunciado.

**Conhecimento necessário**
- Notação assintótica, para a análise de complexidade
- Capacidade de justificar cada decisão da seção 5 deste documento

**Tarefas**
1. Redigir as instruções de instalação e execução.
2. Descrever a arquitetura e as estruturas de dados adotadas.
3. Apresentar a análise de complexidade por operação.
4. Justificar cada uma das decisões da seção 5.
5. Registrar as limitações conhecidas.

**Critério de conclusão.** O `README.md` permite a um terceiro compreender e executar o projeto
sem consulta adicional.

---

## 5. Decisões de projeto a documentar

O enunciado determina que o comportamento escolhido seja justificado. Cada linha abaixo
corresponde a um item do `README.md`.

| # | Questão | Recomendação | Fundamento |
|---|---|---|---|
| D1 | Ordens *limit* cruzantes: ignorar ou preencher | Preencher | Corresponde ao comportamento de mercado e unifica o algoritmo |
| D2 | Ordem *market* sem liquidez suficiente | Executar o disponível e descartar o remanescente | Fixado pelos exemplos do enunciado |
| D3 | Granularidade da saída de negócios | Por nível de preço | Corresponde ao exemplo; a prática de mercado seria por contraparte |
| D4 | Alteração de quantidade e prioridade | Aumento acarreta perda; redução preserva | Prática de mercado; a redução não prejudica as ordens subsequentes |
| D5 | Prioridade da ordem *pegged* na repreçagem | Preservada | A alteração decorre de ato da engine, não do participante |
| D6 | Composição do preço de referência | Exclui as próprias ordens *pegged* | Previne cascata de repreçagem |
| D7 | Ordem *pegged* que resultaria em cruzamento | Limitar ao melhor preço passivo do próprio lado | Preserva a natureza passiva da ordem |
| D8 | Representação do preço | Inteiro em centavos | Evita erros de comparação em ponto flutuante |
| D9 | Emissão da mensagem `Order created` | A definir | O enunciado não é explícito quanto à sua obrigatoriedade |
| D10 | Sintaxe do comando de alteração | A definir | Não especificada no enunciado |

---

## 6. Cronograma

Prazo de sete dias, de 23/08 a 30/08. O último dia é reservado como margem: nenhuma atividade
de implementação deve ser planejada para 30/08.

| Data | Atividade | Etapas |
|---|---|---|
| Dom 23/08 | Leitura do guia de estudo; preparação do repositório; modelo de domínio | 4.1 · 4.2 |
| Seg 24/08 | Fila do nível de preço e respectivos testes | 4.3 |
| Ter 25/08 | Livro de ofertas e visualização | 4.4 · 4.5 |
| Qua 26/08 | Inserção de ordens *limit* e motor de cruzamento | 4.6 · 4.7 |
| Qui 27/08 | Ordens a mercado, cancelamento e alteração | 4.8 · 4.9 · 4.10 |
| Sex 28/08 | Ordens *pegged* | 4.11 |
| Sáb 29/08 | Interface, suíte de testes e documentação | 4.12 · 4.13 · 4.14 |
| Dom 30/08 | Revisão, verificação do histórico Git e entrega | — |

Considerações sobre o cronograma:

- A etapa 4.11 recebeu um dia inteiro por ser a de maior complexidade conceitual e a única sem
  precedente direto nas anteriores.
- Os testes das etapas 4.3 e 4.4 são escritos junto com o código, não postergados para 29/08.
  A etapa 4.13 consolida e amplia, não inaugura.
- Havendo atraso, a etapa 4.11 é a que deve ser preservada: trata-se de requisito obrigatório,
  e sua ausência compromete a elegibilidade da entrega.

---

## 7. Checklist de entrega

### Conformidade

- [ ] Repositório público no GitHub, com o projeto integralmente versionado
- [ ] Histórico com commits incrementais e mensagens descritivas das decisões
- [ ] Nenhum commit concentrando parcela desproporcional da implementação
- [ ] Entrega efetuada até 30/08/2026, 23h59

### Requisitos base

- [ ] Inserção de ordens com tipo, lado, preço e quantidade
- [ ] Ordens *limit* operacionais
- [ ] Ordens *market* operacionais
- [ ] Saída `Trade, price: <preço>, qty: <quantidade>` no formato exato
- [ ] Tratamento de ordens *limit* cruzantes definido e justificado

### Requisitos adicionais

- [ ] Visualização do livro
- [ ] Prioridade por ordem de chegada
- [ ] Cancelamento com remoção efetiva
- [ ] Alteração com reposicionamento na faixa de preço adequada
- [ ] Ordens *pegged* acompanhando *bid* e *offer*

### Qualidade

- [ ] Os exemplos do enunciado reproduzidos como testes automatizados
- [ ] Invariantes verificados; teste aleatório implementado
- [ ] Preço representado sem ponto flutuante
- [ ] Engine independente da interface de linha de comando
- [ ] Complexidade das operações analisada e documentada
- [ ] Todas as decisões da seção 5 justificadas no `README.md`
- [ ] Capacidade de explicar integralmente a base de código
