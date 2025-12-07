# Experimental Results

## Overview

**Date:** December 2025
**Total Experiments:** 40
**Total Games:** 2,930
**Research Question:** How do Minimax and MCTS compare on Gardner MiniChess under equal computational budgets?

---

## Executive Summary

> *This section will be populated after experiments complete.*

### Key Findings
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

### Bottom Line
[One-paragraph conclusion]

---

## Phase 1: Validation

**Purpose:** Verify both implementations work correctly.

| Agent | Opponent | Games | Wins | Draws | Losses | Win Rate |
|-------|----------|-------|------|-------|--------|----------|
| Minimax(3) | Random | 20 | - | - | - | - |
| MCTS(100) | Random | 20 | - | - | - | - |
| Minimax(3) | Greedy | 20 | - | - | - | - |
| MCTS(100) | Greedy | 20 | - | - | - | - |

---

## Phase 2: Baseline Performance

**Purpose:** Establish performance against weak opponents.

### Minimax vs Random

| Depth | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------|-------|------|-------|--------|----------|-----------|
| 2 | 50 | - | - | - | - | - |
| 3 | 50 | - | - | - | - | - |
| 4 | 50 | - | - | - | - | - |

### MCTS vs Random

| Simulations | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------------|-------|------|-------|--------|----------|-----------|
| 50 | 50 | - | - | - | - | - |
| 100 | 50 | - | - | - | - | - |
| 200 | 50 | - | - | - | - | - |

### Minimax vs Greedy

| Depth | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------|-------|------|-------|--------|----------|-----------|
| 2 | 50 | - | - | - | - | - |
| 3 | 50 | - | - | - | - | - |
| 4 | 50 | - | - | - | - | - |

### MCTS vs Greedy

| Simulations | Games | Wins | Draws | Losses | Win Rate | Avg Plies |
|-------------|-------|------|-------|--------|----------|-----------|
| 50 | 50 | - | - | - | - | - |
| 100 | 50 | - | - | - | - | - |
| 200 | 50 | - | - | - | - | - |

---

## Phase 3: Head-to-Head Matrix

**Purpose:** Comprehensive comparison across the parameter space (100 games each).

### MCTS Win Rate vs Minimax

| MCTS \ Minimax | Depth 2 | Depth 3 | Depth 4 |
|----------------|---------|---------|---------|
| 50 sims | - | - | - |
| 100 sims | - | - | - |
| 150 sims | - | - | - |
| 200 sims | - | - | - |
| 300 sims | - | - | - |
| 500 sims | - | - | - |

### Average Game Length (Plies)

| MCTS \ Minimax | Depth 2 | Depth 3 | Depth 4 |
|----------------|---------|---------|---------|
| 50 sims | - | - | - |
| 100 sims | - | - | - |
| 150 sims | - | - | - |
| 200 sims | - | - | - |
| 300 sims | - | - | - |
| 500 sims | - | - | - |

---

## Phase 4: Time-Matched Experiments

**Purpose:** Fair comparison at equal computational budgets (100 games each).

| Budget | MCTS Config | Minimax Config | MCTS Win Rate | Minimax Win Rate | Draws | Avg Plies |
|--------|-------------|----------------|---------------|------------------|-------|-----------|
| ~0.5s | 50 sims | depth=3 | - | - | - | - |
| ~1.0s | 100 sims | depth=4 | - | - | - | - |
| ~2.0s | 200 sims | depth=4 | - | - | - | - |

---

## Phase 5: High-Resource MCTS Scaling

**Purpose:** Test MCTS performance ceiling (50 games each vs Minimax depth=3).

| MCTS Sims | Wins | Draws | Losses | Win Rate | Avg Plies | Time/Move |
|-----------|------|-------|--------|----------|-----------|-----------|
| 500 | - | - | - | - | - | - |
| 750 | - | - | - | - | - | - |
| 1000 | - | - | - | - | - | - |

---

## Analysis

### Algorithm Comparison

| Aspect | Minimax | MCTS |
|--------|---------|------|
| **Best Win Rate** | - | - |
| **Computational Efficiency** | - | - |
| **Scaling Behavior** | - | - |
| **Tactical Precision** | - | - |

### Key Observations

1. **[Observation about relative performance]**

2. **[Observation about computational efficiency]**

3. **[Observation about scaling behavior]**

4. **[Observation about game characteristics]**

---

## Conclusions

### Research Question Answer

> **How do Minimax and MCTS compare on Gardner MiniChess?**

[Detailed answer based on experimental data]

### Implications for Algorithm Selection

[Discussion of when to use each algorithm]

### Limitations

1. [Limitation 1]
2. [Limitation 2]
3. [Limitation 3]

### Future Work

1. [Potential extension 1]
2. [Potential extension 2]

---

## Appendix: Experimental Metadata

- **Hardware:** [Platform details]
- **Software:** Python 3.12+
- **Seeds Used:** Fixed per experiment for reproducibility
- **Color Swapping:** Yes, all experiments
- **Game Limit:** 200 plies

---

*Generated from experiments run on [DATE]*
