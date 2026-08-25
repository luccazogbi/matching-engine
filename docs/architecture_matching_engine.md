# Arquitetura do Matching Engine

Pense no `OrderBook` como o objeto maior, que organiza tudo:

```text
OrderBook
│
├── bids
│   └── preço → PriceLevel
│
├── offers
│   └── preço → PriceLevel
│
├── orders
│   └── order_id → Order
│
├── bid_prices
└── offer_prices
```

E cada `PriceLevel` contém as ordens daquele preço:

```text
PriceLevel 10.50
│
└── Order A <-> Order B <-> Order C
```

Então o fluxo futuro para inserir uma ordem LIMIT será aproximadamente:

```text
Chega uma Order
      ↓
OrderBook verifica o lado e o preço
      ↓
get_or_create_level(side, price)
      ↓
retorna o PriceLevel daquele preço
      ↓
level.last_insert(order)
      ↓
Order entra no final da fila FIFO
```

Por exemplo:

```python
order = Order(
    side=Side.BUY,
    order_type=OrderType.LIMIT,
    qty=100,
    price=Decimal("10.50")
)
```

O `OrderBook` procuraria:

```text
Existe BUY em 10.50?
```

Se não:

```text
cria PriceLevel(10.50)
```

Depois:

```python
level = ...
level.last_insert(order)
```

E teríamos:

```text
OrderBook
└── bids
    └── 10.50
        └── PriceLevel
            └── Order
```

Se depois chegar outra ordem no mesmo preço:

```text
Order B → BUY → 10.50
```

`get_or_create_level()` não cria outro nível. Ele retorna o mesmo objeto:

```text
10.50 → PriceLevel
        │
        A <-> B
```

E aqui tem um detalhe importante: a ordem também provavelmente será registrada em:

```python
self.orders[order.order_id] = order
```

Então a mesma `Order` estará acessível por dois caminhos:

```text
OrderBook.orders
    └── order_id → Order
```

e:

```text
OrderBook.bids/offers
    └── price → PriceLevel → Order
```

Não são cópias diferentes. São **referências para o mesmo objeto `Order`**.

Então a frase:

> "não adicionamos uma ordem diretamente no OrderBook"

Pode ser ajustada para:

**Conceitualmente adicionamos a ordem ao `OrderBook`, mas o `OrderBook` delega o armazenamento FIFO daquela ordem ao `PriceLevel` correspondente.**

A divisão de responsabilidades fica:

```text
Order
→ representa uma ordem

PriceLevel
→ organiza em FIFO as ordens de um mesmo preço

OrderBook
→ organiza todos os PriceLevels e fornece acesso rápido às ordens e aos melhores preços
```

Essa é a visão mais importante para não se perder na arquitetura do projeto.
