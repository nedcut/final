# MiniChess AI Project

A research project comparing Monte Carlo Tree Search (MCTS) and Minimax with alpha-beta pruning on Gardner MiniChess (5×5 variant).

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# Run example match
python examples/match_runner.py --agent1 minimax --agent2 mcts \
  --agent1-depth 3 --agent2-simulations 100 --games 50 --swap-colors

# Run tests
pytest
```

## Documentation

- **[RESEARCH.md](docs/RESEARCH.md)** - Research questions and methodology
- **[FINDINGS.md](docs/FINDINGS.md)** - Experimental results and analysis
- **[README.md](docs/README.md)** - Detailed usage guide and API reference

## Project Structure

```
src/minichess/          # Core game engine and AI agents
  ├── game.py           # MiniChess game logic
  └── agents/           # AI implementations (Random, Greedy, Minimax, MCTS)

tests/                  # Unit tests
examples/               # Demo scripts and match runner
experiments/            # Experimental framework and results
docs/                   # Documentation
```

## Research Findings

**TL;DR:** Minimax dominates MCTS on 5×5 MiniChess (60-80% win rate at equal computational budgets). The small state space and tactical nature favor exhaustive search over sampling.

See [FINDINGS.md](docs/FINDINGS.md) for complete analysis.

## Key Features

- **Minimax Agent:** Alpha-beta pruning, configurable depth, move ordering
- **MCTS Agent:** UCB1 selection, capture-biased rollouts, 4× optimized
- **Universal Match Runner:** CLI for running any agent matchup
- **Comprehensive Testing:** 1,870+ games analyzed across multiple configurations

## Usage Examples

### Basic Game Play

```python
from minichess.game import initial_state
from minichess.agents import MinimaxAgent, MCTSAgent

state = initial_state()
minimax = MinimaxAgent(depth=3)
mcts = MCTSAgent(simulations=100)

# Make moves
move = minimax.choose_move(state)
state = state.make_move(move)
```

### Run Matches

```bash
# Quick demo (single game with visualization)
python examples/demo.py --agent1 minimax --agent1-depth 3 \
  --agent2 mcts --agent2-simulations 100

# Batch matches (multiple games with statistics)
python examples/match_runner.py --agent1 minimax --agent2 mcts \
  --agent1-depth 3 --agent2-simulations 100 --games 100 --swap-colors

# Run comprehensive experiments
python experiments/run_experiments.py --yes

# Run custom high-MCTS experiments
python experiments/run_experiments.py \
  --custom-mcts 300,500,1000 --custom-minimax 2,3,4

# Analyze results
python experiments/analyze_results.py
```

See [docs/README.md](docs/README.md) for complete API reference and advanced usage.
