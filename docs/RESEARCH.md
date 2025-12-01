# MiniChess AI Research Project

## Research Question

> **How do depth-limited minimax with alpha-beta pruning and Monte Carlo Tree Search compare in playing strength and computational efficiency on Gardner MiniChess, under equal computational budgets?**

## Game Environment: Gardner MiniChess

- **Board:** 5×5
- **Pieces:** Rook, Knight, Bishop, Queen, King, and five pawns per side
- **Rules:**
  - Same movement rules as standard chess
  - No double pawn moves, en passant, or castling
- **Objective:** Checkmate the opponent's king

This compact variant provides a tractable testbed for comparing search algorithms without the full complexity of standard chess (~10²⁰ vs ~10⁴⁶ game states).

## Algorithms

### Minimax with Alpha-Beta Pruning

**Core approach:** Exhaustive, depth-limited search assuming optimal play from both players.

**Implementation features:**
- Alpha-beta pruning to skip inferior branches
- Material-based evaluation function (P=1, N=3, B=3, R=5, Q=9, K=1000)
- Move ordering (captures first) for better pruning
- Configurable depth (2-5 plies)

**Variants tested:** Depth 2, 3, 4 to explore strength vs. computation trade-offs

### Monte Carlo Tree Search (MCTS)

**Core approach:** Build search tree through repeated simulations using UCB1 selection.

**Implementation features:**
- UCB1 tree policy for exploration-exploitation balance
- Capture-biased rollout policy for tactical play
- Heuristic evaluation for non-terminal rollouts
- Early termination for decisive positions
- Move ordering in expansion phase

**Optimizations applied:**
- 4× speedup through profiling-driven improvements
- Eliminated redundant legal move generation
- Reduced rollout depth (40→30 plies)

**Variants tested:** 50, 100, 200, 300, 500, 1000, 2000, 3000, 5000 simulations per move

## Evaluation Methodology

### 1. Playing Strength
- Head-to-head matches at time-matched computational budgets
- Win rate, draw rate, average game length
- Baseline tests vs. Random and Greedy agents

### 2. Computational Efficiency
- Time per move measurements
- Nodes/simulations per second
- Scaling behavior with increased resources

### 3. Performance Characteristics
- Decisiveness (ability to finish games)
- Tactical accuracy
- Resource degradation curves

**Test parameters:**
- 50-200 games per matchup
- Color swapping for fairness
- Fixed seeds for reproducibility
- 200-ply game limit

## Expected Insights

This research aims to determine:
1. Which algorithm performs better at equal computational budgets
2. How each algorithm scales with additional resources
3. Where the trade-offs lie between exhaustive search (minimax) and sampling-based search (MCTS)
4. Implications for algorithm selection in small vs. large game spaces

---

*For complete experimental results, see FINDINGS.md*
