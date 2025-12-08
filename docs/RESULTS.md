# Experimental Results

## Overview

**Date:** December 7, 2025
**Total Experiments:** 40
**Total Games:** 2,930
**Research Question:** How do Minimax and MCTS compare on Gardner MiniChess under equal computational budgets?

---

## Executive Summary

### Key Findings
1. **Minimax dominates MCTS at all tested resource levels** — Even at 500 simulations, MCTS achieves only 38% win rate against Minimax depth 2, and under 5% against depth 4.
2. **Minimax is remarkably efficient** — Depth 3 achieves 100% win rates against both Random and Greedy with fast game times (~17-27 plies).
3. **MCTS scaling shows diminishing returns** — Increasing from 500 to 1000 simulations does not meaningfully improve performance against Minimax.

### Bottom Line
For Gardner MiniChess, Minimax with alpha-beta pruning is the clear winner. The game's small state space (5×5 board) and tactical nature strongly favor exhaustive deterministic search. MCTS requires significantly more computation to remain competitive and still cannot match Minimax's precision in exploiting tactical opportunities. This suggests that for small, tactical games, classical search algorithms outperform Monte Carlo methods.

---

## Phase 1: Validation

**Purpose:** Verify both implementations work correctly.

| Agent | Opponent | Games | Wins | Draws | Losses | Win Rate |
|-------|----------|-------|------|-------|--------|----------|
| Minimax(3) | Random | 20 | 20 | 0 | 0 | 100.0% |
| MCTS(100) | Random | 20 | 19 | 0 | 1 | 95.0% |
| Minimax(3) | Greedy | 20 | 20 | 0 | 0 | 100.0% |
| MCTS(100) | Greedy | 20 | 10 | 8 | 2 | 70.0% |

**Observation:** Both agents easily defeat Random. Against Greedy, Minimax wins 100% while MCTS wins only 70% with many draws, an early indicator of MCTS's tactical limitations.

---

## Phase 2: Baseline Performance

**Purpose:** Establish performance against weak opponents.

### Minimax vs Random

| Depth | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------|-------|------|-------|--------|----------|-----------|
| 2 | 50 | 49 | 1 | 0 | 99.0% | 26.4 |
| 3 | 50 | 50 | 0 | 0 | 100.0% | 17.4 |
| 4 | 50 | 50 | 0 | 0 | 100.0% | 18.9 |

### MCTS vs Random

| Simulations | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------------|-------|------|-------|--------|----------|-----------|
| 50 | 50 | 45 | 3 | 2 | 93.0% | 30.1 |
| 100 | 50 | 47 | 3 | 0 | 97.0% | 25.2 |
| 200 | 50 | 48 | 2 | 0 | 98.0% | 25.1 |

### Minimax vs Greedy

| Depth | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------|-------|------|-------|--------|----------|-----------|
| 2 | 50 | 50 | 0 | 0 | 100.0% | 74.5 |
| 3 | 50 | 50 | 0 | 0 | 100.0% | 26.5 |
| 4 | 50 | 50 | 0 | 0 | 100.0% | 28.5 |

### MCTS vs Greedy

| Simulations | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------------|-------|------|-------|--------|----------|-----------|
| 50 | 50 | 18 | 29 | 3 | 65.0% | 35.4 |
| 100 | 50 | 27 | 22 | 1 | 76.0% | 33.2 |
| 200 | 50 | 42 | 8 | 0 | 92.0% | 27.4 |

**Observation:** Minimax achieves perfect scores at all depths. MCTS requires 200 simulations to reach 92% against Greedy, while drawing frequently at lower simulation counts.

---

## Phase 3: Head-to-Head Matrix

**Purpose:** Comprehensive comparison across the parameter space (100 games each).

### MCTS Win Rate vs Minimax

| MCTS \ Minimax | Depth 2 | Depth 3 | Depth 4 |
|----------------|---------|---------|---------|
| 50 sims | 5.5% | 2.0% | 0.0% |
| 100 sims | 11.0% | 5.5% | 1.0% |
| 150 sims | 18.5% | 8.5% | 0.5% |
| 200 sims | 24.0% | 11.5% | 2.0% |
| 300 sims | 30.0% | 20.5% | 3.5% |
| 500 sims | 38.0% | 21.5% | 4.5% |

### Average Game Length (Plies)

| MCTS \ Minimax | Depth 2 | Depth 3 | Depth 4 |
|----------------|---------|---------|---------|
| 50 sims | 46.5 | 27.0 | 29.7 |
| 100 sims | 51.8 | 36.9 | 32.9 |
| 150 sims | 67.5 | 44.4 | 32.3 |
| 200 sims | 74.6 | 50.2 | 43.8 |
| 300 sims | 81.2 | 57.4 | 47.5 |
| 500 sims | 85.0 | 58.0 | 51.2 |

### Draw Rates

| MCTS \ Minimax | Depth 2 | Depth 3 | Depth 4 |
|----------------|---------|---------|---------|
| 50 sims | 7% | 0% | 0% |
| 100 sims | 10% | 5% | 2% |
| 150 sims | 27% | 9% | 1% |
| 200 sims | 18% | 9% | 2% |
| 300 sims | 24% | 9% | 7% |
| 500 sims | 24% | 15% | 7% |

**Observation:** MCTS win rates improve with more simulations but plateau around 500 sims. Against Minimax depth 4, MCTS never exceeds 5% win rate regardless of simulation count.

---

## Phase 4: Time-Matched Experiments

**Purpose:** Fair comparison at equal computational budgets (100 games each).

| Budget | MCTS Config | Minimax Config | MCTS Win Rate | Minimax Win Rate | Draws | Avg Plies |
|--------|-------------|----------------|---------------|------------------|-------|-----------|
| ~0.5s | 50 sims | depth=3 | 1.5% | 98.5% | 1% | 31.5 |
| ~1.0s | 100 sims | depth=4 | 1.5% | 98.5% | 1% | 34.3 |
| ~2.0s | 200 sims | depth=4 | 4.0% | 96.0% | 6% | 43.6 |

**Observation:** Under time-matched conditions, Minimax wins over 96% of games at every budget level. This is the most fair comparison and demonstrates Minimax's clear superiority.

---

## Phase 5: High-Resource MCTS Scaling

**Purpose:** Test MCTS performance ceiling (50 games each vs Minimax depth=3).

| MCTS Sims | Wins | Draws | Losses | Win Rate | Avg Plies | Time (s) |
|-----------|------|-------|--------|----------|-----------|----------|
| 500 | 6 | 8 | 36 | 20.0% | 53.9 | 457.8 |
| 750 | 7 | 15 | 28 | 29.0% | 59.3 | 769.8 |
| 1000 | 8 | 6 | 36 | 22.0% | 57.9 | 1037.4 |

**Observation:** Even with 1000 simulations (20× the baseline), MCTS only achieves ~22% win rate against depth-3 Minimax. The increase from 500→1000 sims shows no meaningful improvement, suggesting a performance ceiling.

---

## Analysis

### Algorithm Comparison

| Aspect | Minimax | MCTS |
|--------|---------|------|
| **Best Win Rate** | 100% (vs all baselines) | 98% (vs Random at 200 sims) |
| **vs Each Other** | 95.5-100% win rate | 0.5-38% win rate |
| **Computational Efficiency** | Excellent (fast, decisive) | Poor (needs 10-20× compute) |
| **Scaling Behavior** | Depth 3→4 solidifies wins | Diminishing returns past 300 sims |
| **Tactical Precision** | Perfect exploitation | Misses tactical sequences |

### Key Observations

1. **Minimax's Tactical Superiority**
   Minimax's exhaustive search finds and exploits precise tactical sequences that MCTS's random simulations miss. This is especially evident in the near-perfect win rates against MCTS at depth 4.

2. **MCTS Scaling Limitations**
   While MCTS improves from 50→300 simulations, gains plateau beyond that. Against depth 3, it goes from 2%→21.5% but at 1000 sims still only reaches 22%. This suggests a fundamental limitation in MCTS's approach for this game.

3. **Game Length Patterns**
   - Minimax wins quickly (17-27 plies) when dominant
   - Games against depth-2 Minimax last longer (50-85 plies) as MCTS can sometimes survive
   - High draw rates against shallower Minimax suggest MCTS can avoid losing but cannot find wins

4. **Time-Matched Results Are Decisive**
   The fairest comparison (equal computational budget) shows Minimax winning 96-98.5% of games. This is the key finding: at equal resources, Minimax dramatically outperforms MCTS.

---

## Conclusions

### Research Question Answer

> **How do Minimax and MCTS compare on Gardner MiniChess?**

**Minimax with alpha-beta pruning decisively outperforms MCTS on Gardner MiniChess.** Under time-matched conditions, Minimax wins 96-98.5% of games. Even with 10× more computational resources, MCTS cannot achieve parity with a depth-3 Minimax search.

The primary reason is **tactical precision**: Gardner MiniChess, with its small 5×5 board, is highly tactical. Games are often decided by forcing sequences (checks, captures, threats) that Minimax evaluates exhaustively while MCTS samples probabilistically and often misses.

### Implications for Algorithm Selection

| Choose Minimax When: | Choose MCTS When: |
|---------------------|-------------------|
| State space is small | State space is enormous |
| Game is highly tactical | Position evaluation is difficult |
| Good heuristics exist | No good heuristic function |
| Search depth matters | Simulation quality matters |
| Deterministic solutions needed | Approximation is acceptable |

For MiniChess and similar tactical games, **Minimax is strongly recommended**. MCTS may be more appropriate for larger games (Go, complex card games) where exhaustive search is infeasible and position evaluation is challenging.

### Limitations

1. **Single game variant** — Results may not generalize to standard chess or other variants
2. **Fixed evaluation function** — Minimax used simple material balance; a weaker heuristic might change results
3. **Basic MCTS implementation** — More advanced MCTS variants (RAVE, progressive bias) were not tested
4. **No time controls** — Real gameplay may differ from our fixed-depth/simulation experiments

### Future Work

1. **Test on larger boards** — 6×6, 8×8 variants to see where MCTS becomes competitive
2. **Neural network evaluation** — Replace random rollouts with learned value functions (AlphaZero-style)
3. **Hybrid approaches** — Combine Minimax opening with MCTS endgame
4. **Opening book analysis** — Pre-computed openings might change the balance

---

## Appendix: Experimental Metadata

- **Hardware:** macOS (Darwin 25.1.0)
- **Software:** Python 3.12+
- **Seeds Used:** Fixed per experiment for reproducibility
- **Color Swapping:** Yes, all experiments (equal games as White and Black)
- **Game Limit:** 200 plies maximum
- **Draw Detection:** Threefold repetition, 50-move rule, insufficient material
- **Total Runtime:** ~4.5 hours

---

*Generated from experiments run on December 7, 2025*
