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
