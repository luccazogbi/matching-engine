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

## D09 — Unfilled quantity of a market order

### Decision

The quantity of a market order that cannot be executed for lack of liquidity is **discarded**. It
never rests in the book.

### Motivation

A resting order must sit at a price level, and a market order has no price — there is no level to
put it in.

The statement fixes this behaviour by example. Starting from a book whose sell side holds only 150
shares:

```text
>>> market buy 200
Trade, price: 20, qty: 150
>>> market sell 200
Trade, price: 10, qty: 100
```

The buy consumed 150 and 50 remained unexecuted. The following sell traded against the original
resting bid of 100 @ 10 — untouched. Had the 50 rested as a buy order, that sell would have found
it too, and the output would differ.

This behaviour is known in market terminology as **IOC** (*immediate or cancel*): execute whatever
is available at once, cancel the rest.

### Status

Accepted.

---

## D10 — Order modification semantics

### Decision

Modification is implemented as **detach, change, reinsert** on the same `Order` object, under four
rules:

| Aspect | Rule |
|---|---|
| Identifier | **preserved** — the modified order keeps its `order_id` |
| Price change | loses priority: reinserted at the **tail** of the destination level |
| Quantity increase | loses priority: reinserted at the tail of the same level |
| Quantity decrease | **keeps** priority: adjusted in place, without leaving the queue |
| Arrival sequence | `seq` is renewed whenever priority is lost, kept when it is not |
| Quantity set to zero | treated as a **cancellation** |

### Motivation

**Identifier preserved.** The order object is never recreated — it is detached from one level and
reinserted into another, so the identifier travels with it. This is also the only workable choice:
the statement specifies no output for a modification, so a new identifier could not be communicated,
and the order would become impossible to cancel afterwards.

**Priority rules.** The statement requires that a price change reposition the order in the
appropriate price range, noting that it *"loses priority in the queue"*. The rule for quantity is
not specified; the market convention was adopted — increasing the requested quantity asks for more
than the queue position reserved, so it goes to the back, while reducing it harms nobody behind and
therefore keeps the position.

**Arrival sequence.** `seq` records time priority, which is otherwise encoded only by position in
the level's linked list. If an order moved to the tail while keeping an old, low `seq`, position and
sequence would disagree and the invariant *"queue order equals `seq` order"* would no longer hold —
removing the only field able to verify priority independently of the structure that implements it.
So `seq` is renewed exactly when the order is reinserted at a tail.

**Quantity zero.** Setting the quantity to zero states that the order is no longer wanted, which is
a cancellation. Leaving it in the book would put an order of zero shares in the queue: it would
appear in the book display, occupy a position, and be silently consumed on the next attempt to match
against that level. Negative quantities are invalid input and are rejected rather than cancelled —
zero is an instruction, a negative number is an error.

### Status

Accepted.

---

## D11 — Composition of the pegged reference price

### Decision

The reference price is computed **ignoring the pegged orders themselves**. Only orders whose
`peg_reference` is `None` count towards it.

This is why `OrderBook.reference_price` exists as a method separate from `best_price`: the two
deliberately disagree whenever the top level holds only pegged orders.

### Motivation

A pegged order carries no opinion about price — its price is borrowed. If it counted towards the
reference, borrowed prices would start producing prices.

Concretely, take the book from the statement's fifth requirement after the pegged order has
followed a limit order up to 10.1, and then cancel that limit order. No genuine buyer is willing
to pay 10.1 any more, and the legitimate best bid is the level below.

```text
150 @ 10.1     pegged
200 @ 10       limit
100 @ 9.99     limit
```

Excluding pegged orders, the reference becomes 10 and the pegged order follows it down.
Including them, the reference is 10.1 — its own price — so it compares against itself, concludes
that nothing changed, and never moves again.

The resulting defect is a ratchet. An ordinary order can push the pegged order up, because at
that moment the reference comes from outside it, but nothing can bring it back down, because on
the way down it is the very floor holding itself up. The book would advertise a best bid that no
participant ever offered.

The exclusion has a second, structural consequence: since repricing a pegged order cannot change
any reference, there is no cascade. A single repricing pass is enough, with no loop until
stability and no risk of non-termination.

### Status

Accepted.

---

## D12 — Passive pegs only

### Decision

Only passive pegs are accepted: a buy pegs to the `BID`, a sell pegs to the `OFFER`. A command
whose side contradicts its reference — `peg offer buy` — is rejected.

### Motivation

The statement defines a pegged order only in this form, illustrates it with `peg bid buy`, and
adds that the same works for a peg to the offer. Crossing is never mentioned.

Aggressive pegs — buying at the offer, selling at the bid — do exist in real markets, but they
are outside the specified scope, and in this engine they would execute on arrival and never
rest, which makes them indistinguishable from a market order.

This decision also removes a question that would otherwise need answering: a pegged order can
never cross. A buy pegged to the bid sits at the best bid, and the invariant that the best bid is
strictly below the best offer already guarantees it rests below the sell side.

The side token remains part of the command because the statement's syntax includes it. In valid
commands it is redundant; it serves as a consistency check. Deriving the side from the reference
instead would mean asserting inside the command parser that only passive pegs exist — a domain
rule stated in the wrong place.

### Status

Accepted.

---

## D13 — Pegged order without an available reference

### Decision

A pegged order exists only while a reference exists.

| Moment | Behaviour |
|---|---|
| No reference on submission | rejected, with an error naming the side |
| Reference disappears while resting | the order is cancelled |

### Motivation

A pegged order has no price of its own, so with no reference there is nothing to derive a price
from and no level to rest in.

The alternative — leaving it parked at the last known price — was rejected because it
reintroduces precisely the phantom price that D11 eliminates. An order sitting at a price no
participant supports, now the best price on its side, is the defect D11 exists to prevent; it
would be inconsistent to forbid it in one path and produce it in another.

Stating the rule as a single invariant covers both cases with one sentence, which is also what
makes it explainable.

The automatic cancellation is not a trade and does not appear in the list of trades returned by
the operation that triggered it.

### Status

Accepted.

---

## D14 — Priority of a pegged order when repriced

### Decision

A repriced pegged order **keeps its original `seq`** and is reinserted at the position matching
its arrival, not at the tail of the destination level.

This is the only insertion in the project that does not go through `last_insert`; it uses
`PriceLevel.insert_by_seq`.

### Motivation

The statement's example requires it. Starting from a pegged buy of 150 resting at 10, a limit buy
of 300 at 10.1 arrives and establishes a new best bid. The pegged order follows it, and the
expected book is:

```text
150 @ 10.1     pegged, arrived earlier
300 @ 10.1     limit, arrived later but created the level
```

The pegged order appears **ahead** of the limit order that created the level. Inserting at the
tail would produce the two lines in the opposite order and would not match the specification.

This does not contradict D10, which sends a repriced order to the back of the queue. The
distinction is who caused the change. Under D10 it was the owner of the order issuing a new
instruction, and the queue charges for it by renewing `seq`. In a repricing nobody asked for
anything: the engine moved the order on its own, and an order that arrived at a given moment
goes on being an order that arrived at that moment.

Renewing `seq` here would also break the invariant that queue order equals `seq` order, since the
order would sit ahead of orders with smaller sequence numbers.

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
