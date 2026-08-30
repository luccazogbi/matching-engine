\# Roadmap — Matching Engine

Construction plan for the order matching system requested in the selection process.

Each task includes a **\*\*Study before\*\*** line, indicating the knowledge required to

complete it. References in the format *\*Guide §N\** refer to the document

\`Matching Engine - Guia de Estudo.pdf\`, in this same folder.

**\*\*Deadline: 30/08/2026, 23h59.\*\***

\---

\## About the project

A *\*matching engine\** is the component responsible for matching buy and sell orders in a

deterministic way, respecting priority rules. This project implements an engine for a

single asset, with *\*limit\**, *\*market\** and *\*pegged\** orders.

Assumptions established by the assignment:

\- a single asset, without book segmentation by instrument;

\- volatile storage, without disk or database persistence;

\- complexity preferably O(N), avoiding linear scans;

\- scope restricted to business logic, without infrastructure considerations;

\- language and paradigm are free.

\---

\## Requirements

\### Delivery and evaluation

\- [x] Project published in a GitHub repository

\- [ ] Incremental commits, with messages describing the decisions made

\- [ ] No commit concentrating a disproportionate portion of the implementation

\- [ ] Ability to fully explain the codebase, including what was produced with

      the assistance of AI tools

\- [ ] Delivery completed by 30/08/2026, 23h59

\### Functional — base

\- [x] **\*\*B1\*\*** Order insertion with type, side, price and quantity

\- [x] **\*\*B2\*\*** *\*Limit\** orders, passive and at a fixed price

\- [x] **\*\*B3\*\*** *\*Market\** orders, executed at the best available price

\- [x] **\*\*B4\*\*** Output \`Trade, price: \<price>, qty: \<quantity>\` for each trade

\- [x] **\*\*B5\*\*** Defined and justified handling for *\*limit\** orders whose price would generate a trade

\### Functional — additional

\- [x] **\*\*A1\*\*** Order book visualization

\- [x] **\*\*A2\*\*** Respect for order arrival sequence

\- [x] **\*\*A3\*\*** Cancellation, with effective removal from the engine

\- [x] **\*\*A4\*\*** Modification of price, quantity or both, with queue repositioning

\- [x] **\*\*A5\*\*** *\*Pegged\** orders, following the *\*bid\** or the *\*offer\**

The design decisions required by the assignment are recorded in section 7 of \`README.md\`.

\---

\## Tasks

\### 1. Repository preparation

Project structure and beginning of the version control history.

**\*\*Study before:\*\*** basic Git commands; commit message conventions; \`.gitignore\`.

\- [x] Create the repository on GitHub and link it to the local folder

\- [x] Define the directory structure, separating source code and tests

\- [x] Add \`.gitignore\`

\- [x] Create the initial \`README.md\`

\- [x] Record the first commit

**\*\*Done when:\*\*** \`git log\` shows at least one commit, \`git status\` is clean, the repository opens on GitHub displaying the README, and \`git ls-files\` does not list any execution artifact.

\### 2. Domain model

Entities and price representation, before any logic.

**\*\*Study before:\*\*** domain vocabulary (*\*Guide §1\**); \`dataclasses\` and \`enum\`; floating-point

rounding errors and alternatives (*\*Guide §13\**); monotonic counters

(*\*Guide §5\**).

**\*\*Tools:\*\*** \`dataclasses.dataclass\` · \`enum.Enum\` · \`itertools.count\` · \`decimal.Decimal\` — *\*Guide §8\**.

\- [x] Define the entity that represents an order

\- [x] Define the enumerated types for side and order type

\- [x] Establish the price representation — structural decision, expensive to reverse

\- [x] Establish the identifier generator and the arrival sequence counter

**\*\*Done when:\*\*** it is possible to create two orders at the same price and determine, by the sequence number, which one arrived first. In the adopted price representation, adding 0.10 and 0.20 and comparing with 0.30 returns true.

\### 3. Price level queue

Structure that supports time priority, with constant-time removal.

**\*\*Study before:\*\*** nodes; singly and doubly linked lists; references in Python;

FIFO queue; why \`list.pop(0)\` is O(N); sentinel nodes — *\*Guide §6\**.

\- [x] Implement the doubly linked queue, with head and tail

\- [x] Implement tail insertion

\- [x] Implement head removal

\- [x] Implement arbitrary node removal, without traversing the queue

\- [x] Keep the aggregated quantity of the level updated

\- [x] Test removal at the head, middle and tail

**\*\*Done when:\*\*** in a queue of three orders, removing the middle one keeps the other two correctly linked and the aggregated quantity equal to the sum of the remaining ones — without the method traversing the queue.

\### 4. Order book

Indexes that locate the best price, a level and a specific order.

**\*\*Study before:\*\*** hash tables (*\*Guide §7\**); binary heap and \`heapq\`; representation of

*\*max-heap\** by negating the key (*\*Guide §8\**); lazy removal (*\*Guide §7\**).

**\*\*Tools:\*\*** \`dict\` · \`heapq.heappush\` · \`heapq.heappop\` · \`sortedcontainers.SortedDict\` (alternative) — *\*Guide §8\**.

\- [x] Implement the price-to-level index, by side

\- [x] Implement the identifier-to-order index

\- [x] Implement the price ranking structure, by side

\- [x] Implement the best bid and best offer queries

\- [x] Implement automatic creation and removal of empty levels

\- [x] Test the consistency invariants

**\*\*Done when:\*\*** inserting buys at 10, 9.99 and 9.98 in arbitrary order, the best bid query returns 10; after a level is emptied, it ceases to exist and the best price moves to the next one.

\### 5. Order book visualization

Meets requirement A1 and serves as a debugging tool for all following stages.

**\*\*Study before:\*\*** string formatting and alignment; display by individual order

instead of aggregated level (*\*Guide §10\**).

\- [x] Implement the two-column presentation

\- [x] Display each order individually, preserving the queue

\- [x] Verify against the hypothetical book from additional requirement 4

**\*\*Done when:\*\*** the book from additional requirement 4 is displayed with buys in descending price order and sells in ascending order, one line per order.

\### 6. Limit order insertion

Orders without a counterparty rest in the book, in the correct position.

**\*\*Study before:\*\*** command grammar and argument order (*\*Guide §2\**); price-time priority

(*\*Guide §5\**); event-driven model (*\*Guide §3\**).

\- [x] Implement insertion, still without matching

\- [x] Assign an identifier and sequence number to each accepted order

\- [x] Check, through visualization, the ordering between levels and within the level

**\*\*Done when:\*\*** the first three commands from the assignment example produce a book with one buy and two sells, with the sell of 100 ahead of the sell of 200 at the same level.

\### 7. Matching engine

Core order matching logic. It is the most important stage of the project.

**\*\*Study before:\*\*** distinction between crossing and execution; passive order price rule;

minimum quantity rule; level sweeping; meaning of limit in a *\*limit\** order —

*\*Guide §4\**. Complete command flow — *\*Guide §9\**.

\- [x] Implement the matching loop, with a parameterized acceptance criterion

\- [x] Emit the \`Trade\` output in the exact format from the assignment

\- [x] Remove fully executed orders and emptied levels

\- [x] Rest the remaining quantity of the aggressive order in the book

\- [x] Reproduce the assignment example as an automated test

\- [x] Record the decision regarding crossing *\*limit\** orders — \`docs/DECISIONS.md\`, D08

**\*\*Done when:\*\*** the complete sequence from the assignment example produces exactly the three expected \`Trade\` lines. In addition, \`limit buy 25 250\` against sells of 100 @ 20, 100 @ 22 and 100 @ 26 generates two trades — at 20 and 22 — and leaves 50 resting at 25.

\### 8. Market orders

Special case of the previous algorithm, with unrestricted price acceptance.

**\*\*Study before:\*\*** behavior of unexecuted quantity due to insufficient liquidity,

as established by the examples from the assignment — *\*Guide §3\**.

\- [x] Implement the unrestricted acceptance criterion

\- [x] Discard the remaining quantity, without resting it in the book

\- [x] Test the insufficient liquidity case

**\*\*Done when:\*\*** \`market buy 200\` against 150 available prints \`Trade, price: 20, qty: 150\` and the sell side becomes empty: the remaining 50 do not rest in the book.

\### 9. Cancellation

Meets requirement A3.

**\*\*Study before:\*\*** node removal in a doubly linked list (*\*Guide §6\**); consistency between

indexes that reference the same order.

\- [x] Locate the order by identifier

\- [x] Remove it from the level queue and from the identifier index

\- [x] Update the aggregated quantity and remove the level, if emptied

\- [x] Emit the \`Order cancelled\` output

\- [x] Define and document the behavior for an invalid identifier

\- [x] Test cancellation in all three queue positions

**\*\*Done when:\*\*** the example from additional requirement 3 is reproduced — \`Order cancelled\` is emitted and the order disappears from the book. Cancelling the middle order of a queue of three preserves the link between the other two.

\### 10. Order modification

Meets requirement A4.

**\*\*Study before:\*\*** assignment rule regarding loss of priority when changing price;

market practice regarding quantity changes — *\*Guide §10\**.

\- [x] Define the command syntax, not specified in the assignment

\- [x] Implement price modification, with repositioning

\- [x] Implement quantity modification, with the adopted priority rule

\- [x] Verify against the example from additional requirement 4

\- [x] Record the adopted rule in \`README.md\`

**\*\*Done when:\*\*** the example from additional requirement 4 is reproduced: after changing the buy of 200 @ 10 to 9.98, the book displays 100 @ 9.99 above 200 @ 9.98.

\### 11. Pegged orders

Meets requirement A5. It is the stage with the greatest conceptual complexity.

**\*\*Study before:\*\*** reference price; the four events that change the top of the book;

synchronous repricing; cascade risk; the tension between additional requirements 4 and 5 —

*\*Guide §11\**.

\- [x] Implement \`reference\_price\`, excluding the *\*pegged\** orders themselves

\- [x] Implement \`insert\_by\_seq\` in \`PriceLevel\`

\- [x] Implement \`submit\_pegged\`, with registration of live *\*pegged\** orders

\- [x] Implement the repricing trigger at the end of every operation that changes the top

\- [x] Reject a peg whose reference contradicts the side

\- [x] Define and document the behavior when no reference price is available

\- [x] Document preservation of \`seq\` during repricing

\- [x] Reproduce the sequence from additional requirement 5

**\*\*Done when:\*\*** the sequence from additional requirement 5 is fully reproduced, including the *\*pegged\** order positioned ahead of the *\*limit\** of 300 at the 10.1 level. After the order that defines the *\*bid\** is cancelled, the *\*pegged\** order follows the new best price.

\### 12. Command-line interface

Exposure of functionality through textual commands.

**\*\*Study before:\*\*** reading standard input; command parsing; separation between

presentation and business logic — *\*Guide §13\**.

\- [x] Implement the input loop and command parser

\- [x] Support the six commands: \`limit\`, \`market\`, \`peg\`, \`cancel order\`, modification and \`print book\`

\- [x] Emit \`Order created: \<side> \<qty> @ \<price> \<id>\` when accepting an order

\- [x] Emit \`Order cancelled\` when cancelling

\- [x] Format every displayed price with \`format\_price\`

\- [x] Handle malformed input without interrupting execution

\- [x] Ensure the engine remains independent of the interface

**\*\*Done when:\*\*** the command block from the assignment, pasted into the terminal, produces the expected output; and malformed input returns an error message without ending the session.

\### 13. Test suite

Systematic verification of correctness.

**\*\*Study before:\*\*** \`unittest\` or \`pytest\` (*\*Guide §8\**); invariants; random testing and the

importance of fixing the seed — *\*Guide §14\**.

**\*\*Tools:\*\*** \`unittest\` or \`pytest\` · \`random.Random\` with a fixed seed — *\*Guide §8\**.

\- [x] Transcribe all assignment examples as tests

\- [x] Verify the invariants after every operation

\- [ ] Implement the random test over long sequences

\- [x] Cover edge cases of cancellation and modification

**\*\*Done when:\*\*** a single command runs the entire suite successfully, and the random test goes through a few thousand operations without violating any invariant.

\### 14. Documentation

Record of technical decisions, as required by the assignment.

**\*\*Study before:\*\*** asymptotic notation, for complexity analysis.

\- [x] Write the installation and execution instructions

\- [x] Describe the architecture and adopted data structures

\- [x] Present the complexity analysis by operation

\- [x] Justify each decision from section 7 of \`README.md\`

\- [x] Record the known limitations

**\*\*Done when:\*\*** a person who has never seen the project can clone it, run it and reproduce the examples using only \`README.md\`, and every decision in section 7 has a written justification.

\---

\## Schedule

The last day is buffer time: no implementation should be planned for 30/08.

\| Date | Tasks |

\|---|---|

\| Sun 23/08 | 1 · 2 |

\| Mon 24/08 | 3 |

\| Tue 25/08 | 4 · 5 |

\| Wed 26/08 | 6 · 7 |

\| Thu 27/08 | 8 · 9 · 10 |

\| Fri 28/08 | 11 |

\| Sat 29/08 | 12 · 13 · 14 |

\| Sun 30/08 | Review, history check and delivery |

Task 11 received a full day because it has the greatest complexity and is the only one without precedent in the

previous tasks. In case of delay, it is the one that must be preserved: it is a mandatory requirement.

The tests for tasks 3 and 4 are written together with the code. Task 13 consolidates and expands,

it does not introduce them.

\## Justifications

\* Use of doubly linked lists: Inserting or removing an element from the list does not imply moving other elements. Therefore, we have an O(1) level of complexity.

\## Concepts

\* \`Enum\` : serves to create a **\*\****\*closed set of valid values\****\*\***. Since in our project, orders can only be *\*buy\** or *\*sell\**, we will use this resource to make it easier to define the orders that will be a class. 

    \* \`@property\`: It is a decorator that transforms a method into **\*\*attribute access\*\*** — you write \`side.opposite\` instead of \`side.opposite()\`.

\## Commits

\`type: short description\`

The most useful types for this project are:

\- \`feat:\` new functionality  

    Ex.: \`feat: add order domain model\`

\- \`fix:\` bug fix  

    Ex.: \`fix: correct order removal from price level\`

\- \`test:\` creation or modification of tests  

    Ex.: \`test: add price level removal tests\`

\- \`docs:\` documentation  

    Ex.: \`docs: update project architecture section\`

\- \`refactor:\` code reorganization without changing behavior  

    Ex.: \`refactor: simplify price level removal logic\`

\- \`chore:\` project organization, configuration or maintenance  

    Ex.: \`chore: organize project into src and tests directories\`

\- \`style:\` formatting changes without changing logic  

    Ex.: \`style: format order module\`

\- \`perf:\` performance improvement  

    Ex.: \`perf: optimize best price lookup\`

\- \`build:\` changes related to dependencies or packaging  

    Ex.: \`build: add pytest dependency\`

\- \`ci:\` continuous integration changes  

    Ex.: \`ci: add automated test workflow\`

\## Study

\- Better understand the part where, when searching for the best price, pegged orders are ignored.

\## Problems 

\- When I do \`eng.submit\_limit(Side.BUY, Decimal("10.00000"), 100)\` in the test, it shows all the decimal places. How to solve this?

\- When an order comes inside the orderbook, it doens't show its orderId. IT'S AN IMPORTANT THING TO DO
