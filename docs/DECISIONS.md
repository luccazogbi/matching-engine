# Design Decisions

This document records the main technical and behavioral decisions made during the development of the Matching Engine.

The goal is to make the reasoning behind the implementation explicit.

---

## D01 — Price representation

### Decision

Use Python's `Decimal` type to represent order prices.

### Motivation

Order prices need to be compared exactly and will later be used to identify price levels in the order book.

Using `float` could introduce binary floating-point precision errors. For example:

```python
0.1 + 0.2 == 0.3
```

evaluates to `False`.

Using `Decimal` avoids this problem when values are created from strings:

```python
Decimal("0.10") + Decimal("0.20") == Decimal("0.30")
```

evaluates to `True`.

**Obs:** Furthermore, if we decide to deal with values that have decimal values, we could use `getcontext().prec = X`, where `'` specify how many decimal places we want.

### Status

Accepted.

---

## D02 — Order identifier

### Decision

Use a monotonic integer counter to generate `order_id`.

Each new order receives a unique identifier during the lifetime of the Matching Engine.

### Motivation

The project handles a single asset, stores all information in memory and does not require persistent identifiers.

A sequential integer is therefore sufficient, simple to generate and efficient to compare and store.

### Status

Accepted.

---

## D03 — Arrival sequence

### Decision

Use a monotonic integer counter named `seq` to represent the arrival order of each order.

### Motivation

Orders at the same price level must respect time priority.

A smaller sequence number means that the order arrived before another order with a larger sequence number.

For example:

```text
Order A → seq 1
Order B → seq 2
```

If both orders have the same price, Order A has priority.

### Status

Accepted.

---

## D04 — Order representation

### Decision

Represent orders using a Python `dataclass`.

### Motivation

An order is primarily a structure that stores information used throughout the Matching Engine, including:

* identifier;
* side;
* order type;
* remaining quantity;
* price;
* pegged reference;
* arrival sequence;
* references to the previous and next orders in a price-level queue.

Using `dataclass` automatically generates common methods such as `__init__` and `__repr__`, reducing boilerplate code and keeping the order representation concise.

### Status

Accepted.

---

## D05 — Enumerated values

### Decision

Use Python `Enum` classes for attributes that have a fixed set of valid values.

Currently:

```text
Side
├── BUY
└── SELL

OrderType
├── LIMIT
└── MARKET

PegReference
├── BID
└── OFFER
```

### Motivation

Using enumerations avoids spreading arbitrary strings throughout the code and makes the expected values explicit.

Instead of comparing:

```python
order.side == "buy"
```

the code can use:

```python
order.side == Side.BUY
```

This improves readability and reduces the chance of inconsistent values such as `"Buy"`, `"BUY"` or typing mistakes.

### Status

Accepted.

---

## D06 — Pegged order representation

### Decision

Do not represent `PEGGED` as a separate value of `OrderType`.

`OrderType` contains only:

```text
LIMIT
MARKET
```

The presence and reference of pegged behavior are represented separately using `peg_reference`, whose possible values are `BID`, `OFFER` or `None`.

### Motivation

This keeps the execution type of the order separate from the reference used by pegged behavior.

A regular order has:

```text
peg_reference = None
```

while an order that follows a market reference stores the corresponding `PegReference`.

### Status

Accepted.

---

## D07 — Trade granularity

### Decision

Trades are aggregated **by price level**, not by counterparty order.

A single incoming order that consumes several resting orders at the same price produces **one**
`Trade`. If it sweeps more than one price level, it produces one `Trade` per level.

### Motivation

The example given in the challenge statement fixes this behaviour. Starting from a book with two
resting sell orders at the same price — one of 100 and one of 200 — the statement shows:

```text
>>> market buy 150
Trade, price: 20, qty: 150
```

That command consumed the first order entirely (100) and part of the second (50), yet the expected
output is a **single line** with a quantity of 150. Emitting one trade per counterparty would print
two lines and would not match the specification.

### Trade-off

A real exchange emits one trade per `(aggressor, resting order)` pair, because each execution is a
distinct contract between two identifiable participants, and both sides must be reported
individually for clearing and settlement.

This project has no notion of participant — an order carries side, type, price and quantity, but no
owner — so the per-counterparty distinction carries no information here. Aggregating by level
matches the specified output without losing anything the model represents.

The behaviour is confined to the matching loop: the inner loop accumulates the executed quantity
while consuming the queue of a level, and a single `Trade` is emitted when that level is exhausted
or the incoming order is filled. Changing to per-counterparty granularity would mean emitting inside
the inner loop instead, and nothing else.

### Possible extension

A richer version would record **both** granularities: every individual execution against a resting
order, plus the aggregated view used for output. The engine would keep the detailed list and expose
the aggregated one, so the required output stays unchanged while the finer detail remains available
for inspection.

This was deliberately not implemented, for two reasons.

The first is informational. Each individual execution is only meaningful when the two sides can be
told apart, and in this model they cannot: an order has no owner, so two executions at the same
price differ in nothing but the arrival sequence of the resting order they consumed. The detail
would be recorded and never used.

The second is scope. The statement specifies the aggregated output, and the effort is better spent
on the mandatory requirements.

The extension becomes worthwhile as soon as the model gains participants — at that point each
execution identifies a distinct counterparty pair, which is what clearing and settlement actually
require, and the aggregation would have to be relaxed to per-counterparty reporting.

### Status

Accepted.

---

## D08 — Limit orders that would cross

### Decision

A limit order whose price crosses the opposite side is **executed**, not ignored.

It consumes the opposite side while the price is acceptable, and any remaining quantity rests in the
book at its own limit price.

### Motivation

The statement explicitly allows either behaviour, provided the choice is justified.

Executing was chosen for three reasons:

1. **It is the behaviour of real markets.** An order priced through the opposite side is a
   marketable limit order, and exchanges execute it.
2. **It keeps the book consistent.** Ignoring a crossing order would leave the best bid greater than
   or equal to the best offer — a crossed book, which is an invalid state for a matching engine.
3. **It unifies the algorithm.** With execution in place, a market order is the same procedure with
   an unconstrained price test, rather than a separate code path.

### Status

Accepted.

---

# Future Decisions

As new implementation decisions are made, they should be documented using the structure below.

---

## DXX — Decision title

### Decision

Describe the adopted decision.

### Motivation

Explain why this approach was chosen and how it fits the project requirements.

### Status

Pending / Accepted / Rejected.
