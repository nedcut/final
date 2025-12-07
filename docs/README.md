# MiniChess AI Project

A research project comparing Minimax with alpha-beta pruning and Monte Carlo Tree Search (MCTS) on Gardner MiniChess (5×5).

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

## Quick Start

```python
from minichess.game import initial_state
from minichess.agents import MinimaxAgent, MCTSAgent

# Create game state
state = initial_state()
print(state.render())

# Create agents
minimax = MinimaxAgent(depth=3)
mcts = MCTSAgent(simulations=100)

# Make moves
move = minimax.choose_move(state)
state = state.make_move(move)
```

## Available Agents

| Agent | Description | Key Parameters |
|-------|-------------|----------------|
| `RandomAgent` | Uniform random move selection | `seed` (optional) |
| `GreedyAgent` | One-ply material maximizer | - |
| `MinimaxAgent` | Alpha-beta with transposition table & iterative deepening | `depth`, `time_limit` |
| `MCTSAgent` | UCB1 selection with capture-biased rollouts | `simulations`, `time_limit`, `seed` |

### MinimaxAgent Features
- **Alpha-beta pruning** for efficient tree search
- **Transposition table** to avoid re-searching positions
- **Iterative deepening** for better move ordering and any-time behavior
- **Move ordering** (captures first, MVV-LVA)

### MCTSAgent Features
- **UCB1 tree policy** for exploration-exploitation balance
- **Capture-biased rollouts** for tactical play
- **Early termination** for decisive positions
- **Heuristic evaluation** for non-terminal rollouts

## Running Games

### Interactive Demo
```bash
# Watch a single game
python examples/demo.py --agent1 minimax --agent1-depth 3 \
  --agent2 mcts --agent2-simulations 100

# Available agents: random, greedy, minimax, mcts
python examples/demo.py --help
```

### Batch Games
```bash
# Run 100 games with statistics
python examples/match_runner.py \
  --agent1 minimax --agent1-depth 3 \
  --agent2 mcts --agent2-simulations 100 \
  --games 100 --swap-colors --seed 42
```

**Key Options:**
- `--swap-colors`: Alternate which agent plays White/Black (reduces bias)
- `--seed`: Random seed for reproducibility
- `--print-every N`: Show progress every N games

## Running Experiments

### Final Research Experiments
For comprehensive, statistically significant results:

```bash
# Full experiment suite (~2-3 hours, 2930 games)
python experiments/run_final_experiments.py --yes

# Quick test run (~15 minutes)
python experiments/run_final_experiments.py --quick --yes

# Run specific phase only
python experiments/run_final_experiments.py --phase 3 --yes

# Preview what would run
python experiments/run_final_experiments.py --dry-run
```

**Experiment Phases:**
1. **Validation** - Verify implementations work correctly
2. **Baseline** - Performance against weak opponents (Random, Greedy)
3. **Head-to-Head** - Comprehensive MCTS vs Minimax matrix (18 configurations)
4. **Time-Matched** - Fair comparison at equal computational budgets
5. **High-Resource** - Test MCTS performance ceiling

### Custom Experiments
```bash
# Custom MCTS vs Minimax configurations
python experiments/run_experiments.py \
  --custom-mcts 300,500,1000 \
  --custom-minimax 2,3,4 \
  --custom-games 50
```

Results are saved to `experiments/results/` as CSV and JSON.

## Running Tests

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_minimax_agent.py  # Specific test file
```

## Project Structure

```
.
├── src/minichess/
│   ├── game.py           # Game rules and state management
│   ├── evaluation.py     # Shared evaluation constants
│   └── agents/
│       ├── base.py       # Agent interface
│       ├── random_agent.py
│       ├── greedy_agent.py
│       ├── minimax_agent.py
│       └── mcts_agent.py
├── examples/
│   ├── demo.py           # Single game demo
│   └── match_runner.py   # Batch game runner
├── experiments/
│   ├── run_final_experiments.py  # Comprehensive research experiments
│   ├── run_experiments.py        # Flexible experiment runner
│   └── results/                  # Experiment output
├── tests/                # Unit tests
└── docs/                 # Documentation
```

## Research Documentation

- `docs/RESEARCH.md` - Research question and methodology
- `docs/RESULTS.md` - Experimental findings (generated after experiments)

---

*CS311 - Artificial Intelligence, Middlebury College*
