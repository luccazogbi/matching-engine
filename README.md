# Matching Engine

Order matching system for a single asset, with *limit*, *market* and *pegged* orders, price-time priority and an in-memory order book.

> **Project status:** all requirements from the assignment are implemented and covered by
> tests. Task details are in [ROADMAP.md](ROADMAP.md).

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. Requirements met](#2-requirements-met)
- [3. Execution](#3-execution)
- [4. Commands](#4-commands)
- [5. Architecture](#5-architecture)
- [6. Data structures and complexity](#6-data-structures-and-complexity)
- [7. Design decisions](#7-design-decisions)
- [8. Tests](#8-tests)
- [9. Known limitations](#9-known-limitations)

---

## 1. Overview

An order represents an expression of interest in buying or selling an asset. A *matching
engine* is the component responsible for matching these orders deterministically, while respecting
previously established priority rules.

This project implements an engine for a single asset, under the following assumptions:

- only *limit* and *market* orders, plus the *pegged* type;
- volatile storage, with no disk persistence;
- operations with appropriate complexity, avoiding linear scans;
- scope restricted to business logic, without infrastructure considerations.

The adopted approach separates three responsibilities. `PriceLevel` is a doubly linked
queue that handles time priority within the same price. `OrderBook` stores and
organizes the levels, offering direct access to the best price on each side and to the order for any
identifier, but **does not create orders or make any decisions** — it is a data structure. Every
business rule lives in `MatchingEngine`: what matches, at what price, what rests, what is discarded.

This separation is what makes it possible to test each layer independently and is the reason why the command-line
interface does not have access to any internal structure: it communicates only with the engine.

---

## 2. Requirements met

### Base requirements

| # | Requirement | Status |
|---|---|---|
| B1 | Order insertion with type, side, price and quantity | [x] |
| B2 | *Limit* orders | [x] |
| B3 | *Market* orders | [x] |
| B4 | Output `Trade, price: <price>, qty: <quantity>` | [x] |
| B5 | Defined and justified handling for crossing *limit* orders | [x] |

### Additional requirements

| # | Requirement | Status |
|---|---|---|
| A1 | Order book visualization | [x] |
| A2 | Respect for arrival order | [x] |
| A3 | Order cancellation | [x] |
| A4 | Price and/or quantity modification | [x] |
| A5 | *Pegged* orders | [x] |

---

## 3. Execution

### Environment requirements

Python 3.11 or higher. No runtime dependency — only the standard library
(`decimal`, `heapq`, `enum`, `dataclasses`, `itertools`). `pytest` is used only for
tests.

### Installation

```bash
python -m pip install -e ".[dev]"
```

The project adopts the `src/` layout, so the package is only importable after installation in
editable mode — which ensures that the tests exercise the installed package, not the files from the
working directory.

### Usage

```bash
python -m matching_engine
```

Commands are read from standard input, one per line. `clear` clears the screen without affecting the
book, and `quit` exits.

### Running the tests

From the repository root:

```bash
python -m pytest
```

`pyproject.toml` already defines `pythonpath`, `testpaths` and the naming pattern, so no
additional configuration is required.

---

## 4. Commands

The engine is operated through textual commands read from standard input.

| Command | Syntax | Description |
|---|---|---|
| *Limit* order | `limit <side> <price> <qty>` | Passive order at a fixed price |
| *Market* order | `market <side> <qty>` | Executed immediately at the best available price |
| *Pegged* order | `peg <bid\|offer> <side> <qty>` | Follows the best reference price |
| Cancellation | `cancel order <id>` | Removes the order from the engine |
| Modification | `modify order <id> [price <price>] [qty <qty>]` | Changes price, quantity or both |
| Visualization | `print book` | Displays the state of the book |
| Open orders | `print orders` | Lists resting orders with their identifiers |
| Screen clearing | `clear` | Clears the screen without affecting the book |

The `<side>` argument takes the values `buy` or `sell`. In *limit* orders, **the price precedes the
quantity**.

The identifier is announced only once, when the order is created, and is what `cancel` and `modify` receive.
The book does not display it, because its format is fixed by the assignment — hence `print orders`,
which lists resting orders with identifier, side, quantity, price and, when applicable, the peg
reference.

In a *pegged* order, the side and reference are provided separately, according to the syntax of the
assignment. Since only passive pegs are accepted (§7.7), the side is redundant in valid commands
and serves as a check: `peg offer buy` is rejected due to contradiction.

### Example
The book layout is reproduced exactly as specified in the assignment, in the original language, so the output can be compared against it literally. The tests assert on these strings.

Session reproducing additional requirement 5:

```text
>> limit buy 10 200
Order created: buy 200 @ 10 1
>> limit buy 9.99 100
Order created: buy 100 @ 9.99 2
>> limit sell 10.5 100
Order created: sell 100 @ 10.5 3
>> peg bid buy 150
Order created: buy 150 @ 10 4
>> print book
Ordens de Compra     | Ordens de Venda
---------------------|-----------------
200 @ 10             | 100 @ 10.5
150 @ 10             |
100 @ 9.99           |
>> limit buy 10.1 300
Order created: buy 300 @ 10.1 5
>> print book
Ordens de Compra     | Ordens de Venda
---------------------|-----------------
150 @ 10.1           | 100 @ 10.5
300 @ 10.1           |
200 @ 10             |
100 @ 9.99           |
>> cancel order 5
Order cancelled
>> print book
Ordens de Compra     | Ordens de Venda
---------------------|-----------------
200 @ 10             | 100 @ 10.5
150 @ 10             |
100 @ 9.99           |
>> limit sell 9 500
Order created: sell 500 @ 9 6
Trade, price: 10, qty: 350
Trade, price: 9.99, qty: 100
```

The *pegged* order follows the best bid price in both directions: it rises when the 10.1 *limit*
establishes a new top, and falls when that *limit* is cancelled.

---

## 5. Architecture

Five modules, in layers, each depending only on the previous ones.

| Module | Contents | Responsibility |
|---|---|---|
| `order.py` | `Side`, `OrderType`, `PegReference`, `Order`, `validate_order_terms`, `format_price` | Domain. Defines what an order is and what makes it valid |
| `price_level.py` | `PriceLevel` | Time priority within a price. Doubly linked FIFO queue |
| `order_book.py` | `OrderBook` | Level organization and indexed access. Does not create orders |
| `engine.py` | `Trade`, `MatchingEngine` | Business rules: matching, resting, cancellation, modification, repricing |
| `cli.py` | `execute_command`, `main` | Interface. The only module that knows text |

Validation is centralized in `validate_order_terms`, called from `Order.__post_init__` —
which covers every creation path — and from `modify`, which is the only operation capable of changing price
or quantity after the order already exists. No invalid order reaches the book through any path.

Price formatting is centralized in `format_price` for the same reason: `Decimal("10")` and
`Decimal("10.00")` are equal and occupy the same key, but are displayed differently. Every point that
prints a price — the two book columns, the business output and the interface messages —
passes through it, so the same price never appears with two different representations.

### Code organization

```
src/matching_engine/
    order.py         Side, OrderType, PegReference, Order, validations and formatting
    price_level.py   PriceLevel — doubly linked FIFO queue
    order_book.py    OrderBook — three indexes and two heaps
    engine.py        Trade, MatchingEngine
    cli.py           command parsing and output formatting
    __main__.py      entry point for `python -m matching_engine`
tests/
    test_order.py        order validation and construction
    test_price_level.py  queue operations
    test_order_book.py   levels, best price and reference price
    test_engine.py       matching, cancellation, modification, pegged and invariants
    test_cli.py          commands, outputs and malformed input
docs/
    DECISIONS.md                          decision log, D01 onward
    Matching Engine - Guia de Estudo.pdf   theory and vocabulary
ROADMAP.md
```

---

## 6. Data structures and complexity

Three structures, each chosen for a specific access pattern.

**Doubly linked queue** (`PriceLevel`). Each price level is a queue with pointers to
the head and tail. The choice is justified by cancellation: removing an order from an
arbitrary position is O(1), because the order stores references to the previous and next orders and there is no need
to traverse the queue to find it. A Python list would give O(N) for this operation, since `remove` and
`pop(0)` shift the following elements.

**Dictionaries** as indexes. `bids` and `offers` map price to level, and `orders` maps
identifier to order. The second one is what makes cancellation and modification O(1): the
identifier leads directly to the object, which in turn knows which level it is in.

**Binary heaps** for the best price. `heapq` implements only a *min-heap*, so the buy side
stores negated prices and the read operation reverses the sign. Removal is **lazy**: a
price is never removed from the middle of the heap. When the top points to a price that no longer exists in the
levels dictionary, it is discarded on the next read. Each price is pushed and discarded
at most once, so the cost is amortized.

| Operation | Complexity | Responsible structure |
|---|---|---|
| Insertion of a resting order | O(1), or O(log P) if creating a level | `PriceLevel`, heap |
| Matching | O(K + M log P) | `OrderBook`, `PriceLevel` |
| Cancellation | O(1) | `orders` index, queue |
| Decreasing quantity | O(1) | queue, without leaving the position |
| Price modification | O(1) + matching cost + O(log P) | queue, heap |
| Best price lookup | O(1) on read, O(log P) amortized | heap |
| *Pegged* reference price | O(P log P + N) | level scan |
| *Pegged* order repricing | O(G × (P log P + N + Q)) | scan and ordered reinsertion |

Notation: `N` denotes the number of orders, `P` the number of distinct price levels, `K` the number
of orders consumed in a match, `M` the number of levels emptied in that match, `G` the
number of live *pegged* orders and `Q` the length of the destination queue.

The last two rows are the expensive operations in the project, and the reason is explained in §9.

---

## 7. Design decisions

The assignment requires the adopted behavior to be justified. This section summarizes each
decision; the complete record, with discarded alternatives, is in
[docs/DECISIONS.md](docs/DECISIONS.md).

### 7.1 *Limit* orders whose price would generate a trade

**They are executed.** The order consumes the opposite side while the price is acceptable, and any remainder
rests at its own limit price.

The assignment allows either behavior, as long as it is justified. Execution was
chosen because it is what real markets do with a marketable order; because ignoring the order
would leave the best *bid* greater than or equal to the best *offer*, a crossed book, which is an invalid state
for an engine; and because it unifies the algorithm — a market order becomes the same
procedure with an unrestricted price test, instead of a separate code path.
(`D08`)

### 7.2 *Market* order without sufficient liquidity

**The unexecuted quantity is discarded**, it never rests. A resting order must occupy
a price level, and a market order has no price — there is no level where it can be placed.

The assignment fixes this behavior by example: after a market buy consumes all the
available offers, a subsequent sell finds the buy book unchanged, which can only be explained
if the excess of the buy did not rest. This is the behavior known as *immediate or
cancel*. (`D09`)

### 7.3 Trade output granularity

**One trade per price level**, not per counterparty. An order that consumes multiple resting orders
at the same price produces a single line; if it sweeps several levels, it produces one line per
level.

The assignment example fixes this: a market buy of 150 against two sell orders at the
same price produces one line of 150, not two lines. A real exchange would emit one trade per
`(aggressor, resting)` pair, because each execution is a contract between identifiable participants
— but this model has no participants, and the distinction would carry no information. (`D07`)

### 7.4 Quantity modification and queue priority

**Increasing loses priority, decreasing keeps it.** The modified order retains its identifier in
either case.

The assignment specifies the loss of priority on price change, but says nothing about
quantity. The market convention was adopted: increasing asks for more than the position in the queue
reserved, and therefore moves to the end; decreasing does not harm anyone behind it and keeps the position.
Zero quantity is treated as cancellation — it is the statement that the order is no longer desired —
while negative quantity is invalid input and rejected. (`D10`)

### 7.5 Priority of *pegged* orders during repricing

**The *pegged* order keeps its original `seq` when repriced**, and therefore is reinserted in the
position corresponding to its arrival, not at the tail.

The assignment example requires this: after the arrival of a *limit* that establishes a new
best price, the *pegged* appears **ahead** of that *limit* at the new level, even though it arrived
there later. Inserting at the tail would produce the reverse order.

This does not contradict §7.4. The distinction is who caused the change: in a modification it was the owner of the
order, a new request, and the queue charges for that by renewing the `seq`; in repricing it was the engine,
by itself, without anyone asking — the order remains an order that arrived when it arrived.
(`D14`)

### 7.6 Composition of the reference price for *pegged* orders

**The reference price is calculated while ignoring the *pegged* orders themselves.** Only orders without
a peg reference count.

Without this exclusion, a *pegged* order alone at the top of the book starts deriving its price from itself. The
effect is a ratchet: a regular order can push it upward, because at that moment the
reference comes from outside it, but nothing can bring it back down, because on the way down
it is the floor supporting itself. The book would then announce a best price that no
participant offered.

The exclusion has a second structural consequence: since repricing a *pegged* order does not change
any reference, there is no chain effect, and a single repricing pass is enough. (`D11`)

### 7.7 *Pegged* order that would result in a match

**It does not occur, by construction.** Only passive pegs are accepted: buy with reference to the
*bid*, sell with reference to the *offer*. A buy pegged to the *bid* stays at the best *bid*, and the
invariant best *bid* < best *offer* already guarantees that it does not cross.

The assignment defines the *pegged* order only in this form and does not mention matching at any
point. Aggressive pegs — buying pegged to the *offer*, selling pegged to the *bid* — exist in
real markets, but would be outside the specified scope and, in this engine, would execute
immediately without ever resting, which would make them indistinguishable from a market order.

Related decision: a *pegged* order only exists while a reference exists. Without an available reference
at the time of entry, it is rejected; if the reference disappears later, it is cancelled.
Leaving it parked at the last known price would reintroduce exactly the ghost price that §7.6
eliminates. (`D12`, `D13`)

### 7.8 Price representation

**`Decimal`, always constructed from a string.** Prices are compared for
exact equality and used as dictionary keys, and `float` introduces binary representation
error — `0.1 + 0.2 == 0.3` is false. With `Decimal` constructed from a string, equality
behaves as expected. (`D01`)

---

## 8. Tests

116 tests, organized by layer, executed with `pytest`. Each module has its own file, so a
failure points directly to the responsible layer.

The main verification consists of the **assignment examples transcribed literally**: the book tables are
compared line by line with the output of `OrderBook.__str__`. It is the criterion closest to
what will be evaluated.

In addition, the engine tests end by calling `assert_book_invariants`, which checks
four properties that must hold after any operation, regardless of which one:

1. the book is never crossed — the best *bid* is strictly lower than the best *offer*;
2. no empty level remains in the dictionary;
3. the `total_qty` of each level is equal to the sum of the quantities in its queue;
4. `seq` is increasing along the queue of each level.

The fourth is what supports time priority. Queue order and `seq` are two
representations of the same information, and keeping them consistent is what makes it possible to verify priority
independently of the structure that implements it.

| Layer | Objective | Status |
|---|---|---|
| Assignment examples | Verify compliance with the specification | [x] partial — the *pegged* example is still missing |
| Book invariants | Verify consistency after each operation | [x] |
| Random test (*fuzz*) | Explore sequences not manually anticipated | [ ] |
| Edge cases | Cover cancellation and modification in different positions | [x] |

---

## 9. Known limitations

Deliberately assumed restrictions, with the reason for each one.

**A single asset, everything in memory.** There is no symbol, session or persistence. Restarting the
process clears the book. This is the scope of the assignment.

**No participants.** An order has side, type, price and quantity, but no owner. This is why
trade aggregation by level does not lose information (§7.3): two executions at the same
price differ in nothing except the arrival sequence of the consumed order. As soon as the model
gained participants, the output would need to report by counterparty, which is what
clearing and settlement require.

**No concurrency.** The engine is single-threaded and operations are synchronous. There are no locks, and
nothing prevents two simultaneous callers from corrupting the indexes. A real system would handle this
with a serialized input queue, not with locks scattered across the structure.

***Pegged* repricing is the most expensive operation.** Reference price calculation sorts the
levels on the side and traverses queues, and is recomputed for each live *pegged* order at the end of every operation that
may change the top. As long as the number of *pegged* orders is small, as in the scope of this project, the
cost is irrelevant. To scale, the path would be to maintain the best non-*pegged* price on each
side incrementally, updated in the four operations that change it, instead of recalculating it
by scanning — the same scan-for-index tradeoff that the heaps already make for the best price.

**No order types beyond the three required.** There is no *stop*, *iceberg*, nor validity beyond the
session. Market orders are implicitly *immediate or cancel* (§7.2), and there is no way to request
another validity behavior.

**The identifier of the created order is not returned by the submission methods.** They
return `list[Trade]`, and the interface needs the identifier for the `Order created` output.
The engine records the last accepted order in an attribute, which the interface reads. The correct
design would be to return identifier and trades together, in a small result object; this was
deferred because it would change the signature of three methods and around ten existing assertions,
a few hours before the deadline. The tradeoff is recorded here instead of being hidden.

**Price precision is not limited.** `Decimal` accepts any number of decimal places, and the
engine does not enforce a minimum price increment. A real exchange would reject prices outside the
tick size grid.
