# Matching Engine

Sistema de cruzamento de ordens (*order matching system*) para um único ativo, com ordens
*limit*, *market* e *pegged*, prioridade preço-tempo e livro de ofertas mantido em memória.

> **Estado do projeto:** em desenvolvimento. As seções marcadas com _a preencher_ serão
> completadas conforme as etapas do [ROADMAP.md](ROADMAP.md) forem concluídas.

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

> _A preencher: parágrafo final descrevendo a abordagem adotada, uma vez definida._

---

## 2. Requisitos atendidos

### Requisitos base

| # | Requisito | Situação |
|---|---|---|
| B1 | Inserção de ordens com tipo, lado, preço e quantidade | [ ] |
| B2 | Ordens *limit* | [ ] |
| B3 | Ordens *market* | [ ] |
| B4 | Saída `Trade, price: <preço>, qty: <quantidade>` | [ ] |
| B5 | Tratamento definido e justificado para ordens *limit* cruzantes | [ ] |

### Requisitos adicionais

| # | Requisito | Situação |
|---|---|---|
| A1 | Visualização do livro | [ ] |
| A2 | Respeito à ordem de chegada | [ ] |
| A3 | Cancelamento de ordens | [ ] |
| A4 | Alteração de preço e/ou quantidade | [ ] |
| A5 | Ordens *pegged* | [ ] |

---

## 3. Execução

### Requisitos de ambiente

> _A preencher: versão da linguagem e dependências, se houver._

### Instalação

```
a preencher
```

### Uso

```
a preencher
```

### Execução dos testes

```
a preencher
```

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

### Exemplo

> _A preencher: sessão de exemplo com entrada e saída reais, após a etapa 4.12._

---

## 5. Arquitetura

> _A preencher: descrição dos módulos e da separação entre a lógica de negócio e a interface._

### Organização do código

```
a preencher
```

---

## 6. Estruturas de dados e complexidade

> _A preencher: descrição das estruturas adotadas e a justificativa de cada escolha._

| Operação | Complexidade | Estrutura responsável |
|---|---|---|
| Inserção de ordem | | |
| Cruzamento | | |
| Cancelamento | | |
| Alteração | | |
| Consulta do melhor preço | | |
| Repreçagem de ordens *pegged* | | |

Notação: `N` denota o número de ordens e `P` o número de níveis de preço distintos.

---

## 7. Decisões de projeto

O enunciado determina que o comportamento adotado seja justificado. Esta seção registra cada
decisão e o respectivo fundamento.

### 7.1 Ordens *limit* cujo preço geraria negócio

> _A preencher._

### 7.2 Ordem *market* sem liquidez suficiente

> _A preencher._

### 7.3 Granularidade da saída de negócios

> _A preencher._

### 7.4 Alteração de quantidade e prioridade na fila

> _A preencher._

### 7.5 Prioridade das ordens *pegged* na repreçagem

> _A preencher._

### 7.6 Composição do preço de referência das ordens *pegged*

> _A preencher._

### 7.7 Ordem *pegged* que resultaria em cruzamento

> _A preencher._

### 7.8 Representação do preço

> _A preencher._

---

## 8. Testes

> _A preencher: estratégia de testes e cobertura._

| Camada | Objetivo | Situação |
|---|---|---|
| Exemplos do enunciado | Verificar a conformidade com a especificação | [ ] |
| Invariantes do livro | Verificar a consistência após cada operação | [ ] |
| Teste aleatório (*fuzz*) | Explorar sequências não previstas manualmente | [ ] |
| Casos limítrofes | Cobrir cancelamento e alteração em posições diversas | [ ] |

---

## 9. Limitações conhecidas

> _A preencher: restrições de escopo assumidas e comportamentos deliberadamente não
> implementados._
