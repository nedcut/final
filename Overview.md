# MiniChess Solvers – Project Overview

## High-Level Goal

Our goal is to design, implement, and compare two AI agents for **Gardner MiniChess** using two classic adversarial search strategies:

- **Minimax with Alpha–Beta pruning**
- **Monte Carlo Tree Search (MCTS)**

We’re not trying to fully solve MiniChess. Instead, we treat it as a compact testbed to study how these algorithms perform under realistic computational constraints (limited depth, limited simulations, limited time per move).

---

## Research Question

> **How do depth-limited minimax with alpha–beta pruning and Monte Carlo Tree Search compare in playing strength and computational efficiency on Gardner MiniChess, under equal computational budgets?**  
>  
> A follow-up angle: **How does each algorithm’s performance degrade as we systematically restrict its resources** (shallower search depth, fewer simulations, simpler heuristics)?

---

## Game Environment

We will use the **Gardner MiniChess** variant:

- **Board:** 5×5
- **Pieces:** Rook, Knight, Bishop, Queen, King, and five pawns per side (reduced from full chess)
- **Rules:**
  - Same movement rules as standard chess
  - No double pawn moves
  - No en passant
  - No castling
- **Objective:** Checkmate the opponent’s king (checkmating conditions adapted to the 5×5 board)

We will implement the game logic ourselves in Python (either entirely custom or lightly inspired by `python-chess`), so that we can precisely control:

- State representation
- Legal move generation
- Terminal conditions (checkmate/stalemate)
- Search depth, branching factor, and time per move

We may also define a **smaller “TinyChess” variant** (e.g., fewer pieces or a 4×4 board) to explore deeper search and scaling behavior if the full 5×5 version is too large for some experiments.

---

## Algorithms

### 1. Minimax with Alpha–Beta Pruning

- **Core idea:** Exhaustive, depth-limited search of the game tree, assuming optimal play from both players.
- **Enhancements:**
  - Alpha–beta pruning to avoid exploring obviously inferior branches
  - Heuristic evaluation function at leaf nodes (e.g., material + simple positional features)
  - Potential move ordering, iterative deepening, and transposition tables (if time permits)

We will define **“strong” and “weaker” minimax agents** by adjusting:

- Search depth (e.g., depth 6 vs depth 4 vs depth 2)
- Evaluation function complexity (material-only vs material + positional terms)
- Degree of pruning / move ordering

### 2. Monte Carlo Tree Search (MCTS)

- **Core idea:** Build a search tree using repeated simulations (rollouts) from the current position.
- **Standard UCT framework:**
  - **Selection:** Follow the tree using an upper-confidence bound formula to balance exploration vs exploitation.
  - **Expansion:** Add a new child node when a leaf is not fully expanded (with move ordering: captures first).
  - **Simulation:** Run a capture-biased playout until a terminal position, depth cutoff, or overwhelming advantage.
  - **Backpropagation:** Propagate the game outcome back up the tree.
- **Implementation knobs (now wired in code/CLI):** simulations (or time limit), rollout depth, exploration constant `c`, rollout policy (capture_bias by default).
- **Optimizations implemented:** Heuristic evaluation for non-terminal rollouts, move ordering in expansion, early rollout termination for decisive positions.

We will define **“strong” and “weaker” MCTS agents** by adjusting:

- Number of simulations per move (e.g., 10,000 vs 2,000 vs 500 rollouts)
- Quality of the rollout policy (pure random vs simple heuristics like “prefer captures”)
- Exploration parameter settings (tuned vs intentionally suboptimal)

---

## Evaluation Plan

We will evaluate the agents along three main dimensions:

1. **Playing Strength**
   - Head-to-head matches:
     - Strong minimax vs strong MCTS
     - Each algorithm vs its weaker variants
   - Baseline comparisons:
     - Each algorithm vs a **random agent**
     - Each algorithm vs a **simple 1-ply greedy agent** (moves that maximize material gain)
   - Metrics: win rate, loss rate, draw rate over many games (e.g., 50–100 per matchup)

2. **Computational Efficiency**
   - Average time per move
   - Nodes expanded (for minimax) vs simulations per move (for MCTS)
   - How performance scales as we increase depth/simulations, and where diminishing returns kick in

3. **Robustness and Behavior**
   - How gracefully each algorithm degrades as we reduce its resources
   - Positions where minimax and MCTS disagree strongly on the “best” move, and which algorithm tends to be correct from those positions

All matches will use **identical time controls or equivalent computational budgets** to keep comparisons fair.

---

## Expected Outcomes

By the end of the project, we expect to have:

- A working **MiniChess environment** in Python
- Two fully implemented AI agents:
  - Minimax + alpha–beta (with tunable depth and heuristics)
  - MCTS (with tunable simulation count and rollout policies)
- Experimental results showing:
  - Which algorithm performs better under various resource settings
  - How each algorithm trades off between **strength** and **computational cost**
  - Insights into when structured search (minimax) vs sampling-based search (MCTS) is more effective on a small, tactical board game like MiniChess

These results will be summarized in our final report with:
- Plots/tables of win rates vs depth/simulations
- Example games highlighting key strengths/weaknesses
- Discussion relating our findings back to the literature on MiniChess and game-playing AI
