# MiniChess AI Research Project

## Research Question

> **How do depth-limited minimax with alpha-beta pruning and Monte Carlo Tree Search compare in playing strength and computational efficiency on Gardner MiniChess, under equal computational budgets?**

## Game Environment: Gardner MiniChess

- **Board:** 5×5
- **Pieces:** Rook, Knight, Bishop, Queen, King, and five pawns per side
- **Rules:**
  - Same movement rules as standard chess
  - No double pawn moves, en passant, or castling
  - Pawns promote to Queen on the back rank
- **Objective:** Checkmate the opponent's king

This compact variant provides a tractable testbed for comparing search algorithms without the full complexity of standard chess (~10²⁰ vs ~10⁴⁶ game states).

## Algorithms

### Minimax with Alpha-Beta Pruning

**Core approach:** Exhaustive, depth-limited search assuming optimal play from both players.

**Implementation features:**
- **Alpha-beta pruning** to eliminate inferior branches
- **Transposition table** to cache and reuse position evaluations
- **Iterative deepening** for improved move ordering and any-time behavior
- **Material-based evaluation** (P=1, N=3, B=3, R=5, Q=9)
- **Move ordering** by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)

**Configurations tested:** Depth 2, 3, 4

### Monte Carlo Tree Search (MCTS)

**Core approach:** Build search tree through repeated simulations using UCB1 selection.

**Implementation features:**
- **UCB1 tree policy** for exploration-exploitation balance
- **Capture-biased rollout policy** for tactical play
- **Transposition table** for position reuse across simulations
- **Heuristic evaluation** for non-terminal rollouts
- **Early termination** for decisive material advantages
- **Move ordering** in expansion phase

**Configurations tested:** 50, 100, 150, 200, 300, 500, 750, 1000 simulations per move

## Experimental Design

### Phase 1: Validation
Verify both implementations work correctly against weak opponents (Random, Greedy).

### Phase 2: Baseline Performance
Establish performance baselines against Random and Greedy agents with larger sample sizes.

### Phase 3: Head-to-Head Matrix
Comprehensive comparison across the parameter space:
- MCTS: 50, 100, 150, 200, 300, 500 simulations
- Minimax: depths 2, 3, 4
- 100 games per configuration for statistical significance

### Phase 4: Time-Matched Experiments
Fair comparison using enforced per-move time limits. Both agents receive identical time budgets with high resource caps (MCTS: 10,000 sims; Minimax: depth 10 with iterative deepening), ensuring time is the binding constraint:
- 0.1 seconds per move
- 0.2 seconds per move
- 0.5 seconds per move
- 1.0 seconds per move
- 2.0 seconds per move

### Phase 5: High-Resource MCTS Scaling
Test MCTS performance ceiling with increased resources (500-1000 simulations).

## Evaluation Metrics

### Playing Strength
- **Win rate**: (Wins + 0.5 × Draws) / Total Games
- **Draw rate**: Proportion of drawn games
- **Average game length**: Mean number of plies per game

### Computational Efficiency
- **Time per move**: Wall-clock time per decision
- **Nodes/simulations per second**: Search throughput

### Test Parameters
- 50-100 games per matchup for statistical significance
- **Color swapping** to eliminate first-move bias
- **Fixed seeds** for reproducibility
- 200-ply game limit

## Expected Insights

This research aims to determine:
1. Which algorithm performs better at equal computational budgets
2. How each algorithm scales with additional resources
3. Where the trade-offs lie between exhaustive search (Minimax) and sampling-based search (MCTS)
4. Implications for algorithm selection based on game characteristics

## Theoretical Context

### Why Minimax Might Excel on MiniChess
- Small state space (~10²⁰ positions) makes exhaustive search tractable
- Tactical nature rewards precise calculation
- Low branching factor (~20-40 moves) enables deep search
- Short games (typically 40-80 plies) within Minimax horizon

### Why MCTS Might Excel
- Anytime behavior (always has a move ready)
- No handcrafted evaluation function required
- Naturally handles stochastic elements (if any)
- Scales to larger games where exhaustive search fails

---

*For experimental results, see RESULTS.md (generated after running experiments)*
