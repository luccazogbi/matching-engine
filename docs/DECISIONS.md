# Design Decisions

The reasoning behind each choice made while building the engine. All of them are in effect;
none was later reversed.

Where the statement fixes a behaviour by example, the example is quoted — those are not
preferences, they are requirements read off the specification.

---

## D01 — Price representation

**Decision.** Prices are `Decimal`, always built from a string.

**Why.** Prices are compared for exact equality and used as dictionary keys. In `float`,
`0.1 + 0.2 == 0.3` is false. Building from a string avoids inheriting the error a float literal
already carries: `Decimal(10.1)` is `10.0999999...`, `Decimal("10.1")` is `10.1`.

---

## D02 — Order identifier

**Decision.** A monotonic integer counter.

**Why.** One asset, everything in memory, no persistence. A sequential integer is unique for the
lifetime of the engine, and that is all that is needed.

---

## D03 — Arrival sequence

**Decision.** A second monotonic counter, `seq`, records arrival order.

**Why.** Orders at the same price are served by time priority. A smaller `seq` means it arrived
first. It is separate from `order_id` because the two answer different questions: `order_id`
identifies, `seq` orders. They diverge whenever an order is repriced and keeps its identifier
but loses its place.

---

## D04 — Order representation

**Decision.** `Order` is a `dataclass`.

**Why.** It is a data holder — side, type, quantity, price, peg reference, queue links — and the
decorator generates `__init__` and `__repr__` for free.

---

## D05 — Enumerated values

**Decision.** `Enum` for side, order type and peg reference.

**Why.** It keeps `"Buy"`, `"BUY"` and typos out of the code. The enum values are the command
words themselves, so the interface validates input by looking the value up — the lookup is the
validation.

---

## D06 — Pegged is not an order type

**Decision.** `OrderType` holds only `LIMIT` and `MARKET`. Pegged behaviour is the separate field
`peg_reference`, whose values are `BID`, `OFFER` or `None`.

**Why.** They are independent axes. A pegged order is a limit order whose price is derived rather
than given; once resting, it behaves like any limit order. Making it a third type would duplicate
every limit code path.

---

## D07 — Trade granularity

**Decision.** Trades are aggregated by price level, not by counterparty.

**Why.** The statement fixes it. A market buy of 150 against two resting sells at the same price
prints one line:

```text
>>> market buy 150
Trade, price: 20, qty: 150
```

Reporting per counterparty would print two lines and not match.

**Trade-off.** A real exchange reports per counterparty, because each execution is a contract
between identifiable participants. This model has no participants, so two executions at the same
price differ in nothing but the arrival sequence of the order consumed — the detail would be
recorded and never used. It becomes necessary the moment the model gains participants.

---

## D08 — Limit orders that would cross

**Decision.** They execute. The remainder rests at the order's own limit price.

**Why.** The statement allows either behaviour if justified. Three reasons for executing:

1. It is what real markets do — an order priced through the other side is marketable.
2. Ignoring it would leave the best bid at or above the best offer: a crossed book, an invalid
   state.
3. It unifies the algorithm. A market order becomes the same procedure with the price test
   removed, instead of a separate code path.

---

## D09 — Unfilled quantity of a market order

**Decision.** Discarded. It never rests. This is *immediate or cancel*.

**Why.** A resting order needs a price level, and a market order has no price.

The statement fixes it by example. With only 150 on the sell side:

```text
>>> market buy 200
Trade, price: 20, qty: 150
>>> market sell 200
Trade, price: 10, qty: 100
```

The buy left 50 unexecuted. The following sell traded against the original bid of 100 — if the
50 had rested, that sell would have found it first.

---

## D10 — Order modification

**Decision.**

| aspect | rule |
|---|---|
| identifier | preserved |
| price change | goes to the tail of the destination level |
| quantity increase | goes to the tail of the same level |
| quantity decrease | keeps its position |
| `seq` | renewed whenever priority is lost, kept when it is not |
| quantity set to zero | treated as a cancellation |

**Why.** The order object is never recreated — it is detached and reinserted — so the identifier
travels with it. It is also the only workable choice: the statement specifies no output for a
modification, so a new identifier could not be communicated and the order would become
impossible to cancel.

The statement requires a price change to lose priority. The rule for quantity is not specified;
market convention was followed. Asking for more than the queue position reserved sends the order
to the back; asking for less harms nobody behind it.

`seq` is renewed exactly where the order is reinserted at a tail, so that queue order and `seq`
order never disagree.

Zero quantity says the order is no longer wanted, which is a cancellation. A negative quantity is
invalid input and is rejected — zero is an instruction, a negative number is an error.

---

## D11 — Composition of the pegged reference price

**Decision.** The reference ignores pegged orders. Only orders with `peg_reference is None` count.

**Why.** A pegged order has no opinion about price — its price is borrowed. If it counted towards
the reference, borrowed prices would produce prices.

Take a pegged order that followed a limit up to 10.1, and cancel that limit. No real buyer wants
10.1 any more:

```text
150 @ 10.1     pegged
200 @ 10       limit
```

Excluding pegs, the reference becomes 10 and the order follows it down. Including them, the
reference is its own price, so it compares against itself and never moves again. The defect is a
ratchet: an ordinary order can push it up, but nothing brings it down, because on the way down it
is its own floor. The book would advertise a best bid nobody offered.

**Consequence.** Since repricing a peg cannot change any reference, there is no cascade — one
pass is enough, with no loop until stability.

---

## D12 — Passive pegs only

**Decision.** A buy pegs to the `BID`, a sell pegs to the `OFFER`. `peg offer buy` is rejected.

**Why.** The statement defines pegged orders only in this form and never mentions crossing.
Aggressive pegs exist in real markets, but here they would execute on arrival and never rest,
making them indistinguishable from a market order.

This also removes a question that would otherwise need answering: a passive peg can never cross,
because it rests at the best price of its own side and the book is never crossed.

The side stays in the command because the statement's syntax includes it. In valid commands it is
redundant and serves as a consistency check — deriving it instead would put a domain rule inside
the command parser.

---

## D13 — Pegged order without a reference

**Decision.** A pegged order exists only while a reference exists. No reference on submission:
rejected. Reference disappears while resting: cancelled.

**Why.** With no reference there is no price to derive and no level to rest in.

Leaving it parked at the last known price was rejected because it recreates exactly the phantom
price D11 eliminates: an order sitting at a price nobody supports, now the best price on its side.

The automatic cancellation is not a trade and does not appear in the returned trades.

---

## D14 — Priority of a pegged order when repriced

**Decision.** A repriced pegged order keeps its original `seq` and is reinserted by arrival order,
not at the tail. This is the only insertion in the project that does not use `last_insert`.

**Why.** The statement's example requires it. A pegged buy of 150 rests at 10; a limit buy of 300
at 10.1 arrives and sets a new best bid. The expected book is:

```text
150 @ 10.1     pegged, arrived earlier
300 @ 10.1     limit, arrived later but created the level
```

The peg is ahead of the order that created the level. Inserting at the tail inverts it.

**This does not contradict D10.** The difference is who caused the change. Under D10 the owner
issued a new instruction, and the queue charges for it. In a repricing nobody asked for anything —
the engine moved the order on its own, and an order that arrived at a given moment goes on being
one that arrived at that moment.

---

## D15 — Changing the price of a pegged order

**Decision.** `modify` rejects a price change on a pegged order. Quantity changes are accepted and
follow D10.

**Why.** The price of a peg is derived, not owned. Asking to set it is the same contradiction as
`peg offer buy`.

Allowing it would be worse than useless: the repricing pass runs at the end of the same call and
reverts the price before the user sees it, but `seq` was already renewed on the way. The user
would observe no change and be charged a queue position for it.

---

## D16 — Syntax of the modify command

**Decision.** `modify order <id> [price <price>] [qty <qty>]`, as named pairs, at least one
present.

**Why.** The statement specifies no syntax for this command. The operation has three shapes —
price only, quantity only, both — and a positional form would need a placeholder for the term
being left alone. There is no natural placeholder for a price.

`order` is kept as the second word for symmetry with `cancel order <id>`, which the statement does
specify.

---

## D17 — Output of a modification

**Decision.** `Order modified`, followed by any trades produced.

**Why.** The trades are not optional: the base requirement reports every trade regardless of
cause, and a price change can cross and execute immediately. That is why `modify` returns
`list[Trade]`.

The confirmation line is not required — the statement specifies output for trades, creation and
cancellation, but not for modification. It was added for symmetry with `Order cancelled`, so that
a change producing no trade does not print nothing at all.

The book is not printed afterwards: `print book` is a separate command.

---

## D18 — A market order prints no creation line

**Decision.** `limit` and `peg` print `Order created: ...`. `market` prints only its trades.

**Why.** The creation line carries a price and an identifier, and a market order has neither in
any useful sense: no price by definition, and it never rests (D09), so the identifier would name
an order that no longer exists.

---

## D19 — Recovering an order identifier

**Decision.** `print orders` lists resting orders with identifier, side, quantity, price and peg
reference. The identifier is not added to `print book`.

**Why.** The identifier is announced once, at creation, and is what `cancel` and `modify` take.
Without a way to look it up, the user has to have written it down.

The book display is exactly where it cannot go: that format is the one fixed by the statement and
is compared against literally. A separate command solves it without touching specified output, and
can show what the book has no room for.

---

## D20 — Exposing the identifier of a newly created order

**Decision.** The engine records the last accepted order in an attribute, which the interface
reads. The submission methods keep returning `list[Trade]`.

**Why.** The statement specifies `Order created: buy 100 @ 10 identificador_1` followed by
`cancel order identificador_1`. The identifier is generated inside `Order.__post_init__` and never
leaves the engine. Reading it back from `book.orders` does not work either: an order that executed
in full never rests, and still has to print its creation line.

**Trade-off, stated plainly.** The correct design returns the identifier and the trades together in
a small result object. It was not done for scope, not preference: it changes three signatures and
about ten existing assertions, in tested code, hours before the deadline.

The cost is real. This is hidden state — meaningful only immediately after a submission, and
overwritten by the next one. Today the only reader is the interface, on the line after the call,
so it cannot go wrong; but that is guaranteed by convention, not by structure. It is the first
thing to replace if the project continues, and it is recorded in section 9 of the `README.md`
rather than left implicit.

---

# Future decisions

Same shape: what was decided, why, and the trade-off when there is one.
