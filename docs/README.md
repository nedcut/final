# MiniChess AI Project

## Setup
- Create a virtual environment: `python3 -m venv .venv`
- Activate it:
  - macOS/Linux: `source .venv/bin/activate`
  - Windows (PowerShell): `.venv\\Scripts\\Activate.ps1`
- Upgrade pip (recommended): `python -m pip install --upgrade pip`
- Install dependencies: `pip install -r requirements.txt`
- Install the package in editable mode: `pip install -e .`

## Usage

### Basic Game Play
```python
from minichess.game import initial_state
from minichess.agents import RandomAgent

# Create initial board state
state = initial_state()
print(state.render())

# Get legal moves
moves = state.legal_moves()
print(f"Legal moves: {len(moves)}")

# Make a move
move = moves[0]
state = state.make_move(move)
```

### Interactive Demo
The `demo.py` script provides a simple way to watch different agents play:

```bash
# Random vs Random
python examples/demo.py --agent1 random --agent2 random

# Greedy vs Random
python examples/demo.py --agent1 greedy --agent2 random

# Minimax vs MCTS
python examples/demo.py --agent1 minimax --agent1-depth 3 \
  --agent2 mcts --agent2-simulations 100

# For full options
python examples/demo.py --help
```

**Available agents:** random, greedy, minimax, mcts

**Note:** agent1 plays the White board position, agent2 plays the Black board position

### Universal match runner
For running batches of games and collecting statistics:

```bash
# Basic usage
python examples/match_runner.py --agent1 minimax --agent2 greedy \
  --games 100 --swap-colors --agent1-depth 3

# Advanced example with MCTS
python examples/match_runner.py --agent1 mcts --agent1-simulations 800 \
  --agent2 minimax --agent2-depth 2 --games 200 --seed 42
```

**Flags:**
- `--agent1/--agent2`: Agent names (random, greedy, minimax, mcts)
- `--games`: Number of games to play
- `--max-plies`: Ply cap per game (default: 200)
- `--swap-colors`: Alternate which agent plays White/Black each game to reduce bias
- `--print-every N`: Print progress every N games
- `--seed`: Random seed for reproducibility

**Minimax options:** `--agent1-depth/--agent2-depth` (default: 3), `--agent1-time-limit/--agent2-time-limit`

**MCTS options:** `--agent1-simulations/--agent2-simulations`, `--agent1-rollout-depth/--agent2-rollout-depth`, `--agent1-exploration-c/--agent2-exploration-c`

**Terminology:**
- **Agent1/Agent2**: Player identity (which algorithm/configuration)
- **White/Black**: Board position (which side of the board)
- With `--swap-colors`, agents alternate playing White and Black positions

### Running Experiments
The experiment runner provides comprehensive testing with flexible configuration:

```bash
# Run all standard experiments (time-matched, degradation, baseline, head-to-head)
python experiments/run_experiments.py --yes

# Run specific experiment types
python experiments/run_experiments.py --experiment-types time_matched baseline

# Run custom high-MCTS experiments
python experiments/run_experiments.py \
  --custom-mcts 300,500,1000 --custom-minimax 2,3,4

# Run ultra-high MCTS vs Minimax(3) only
python experiments/run_experiments.py \
  --custom-mcts 2000,3000,5000 --custom-minimax 3

# Customize number of games per experiment
python experiments/run_experiments.py \
  --custom-mcts 1000 --custom-minimax 3,4 --custom-games 100

# Dry run to see experiment plan
python experiments/run_experiments.py --dry-run
```

**Options:**
- `--experiment-types`: Choose which standard experiments to run (time_matched, degradation, baseline, head_to_head, all)
- `--custom-mcts`: Comma-separated MCTS simulation counts
- `--custom-minimax`: Comma-separated Minimax depths
- `--custom-games`: Number of games per custom experiment (default: 50)
- `--output-dir`: Where to save results (default: experiments/results)
- `--dry-run`: Preview experiments without running
- `--yes`: Skip confirmation prompt

Results are saved to CSV and JSON files in the output directory.

### Analyzing Results
After running experiments, analyze the data:

```bash
python experiments/analyze_results.py
```

This generates:
- Win rate matrices for head-to-head matchups
- Resource degradation curves
- Baseline comparison statistics
- Summary tables and visualizations

### Using the greedy baseline
```python
from minichess.game import initial_state
from minichess.agents import GreedyAgent

state = initial_state()
agent = GreedyAgent()
move = agent.choose_move(state)
state = state.make_move(move)
print(state.render())
```

### Using the MCTS agent
```python
from minichess.game import initial_state
from minichess.agents import MCTSAgent

state = initial_state()
# Create agent with default optimized parameters
agent = MCTSAgent(simulations=500, rollout_depth=20)
# Or customize with available options:
# agent = MCTSAgent(
#     simulations=500,          # Number of MCTS simulations per move
#     rollout_depth=20,          # Max depth of rollout simulations
#     rollout_policy="capture_bias",  # "capture_bias" or "random"
#     exploration_c=1.414,       # UCB1 exploration constant (sqrt(2))
#     time_limit=None,           # Optional time limit in seconds
#     seed=42                    # Optional seed for reproducibility
# )
move = agent.choose_move(state)
state = state.make_move(move)
print(state.render())
```

**MCTS Agent Features:**
- **Optimized for tactical play** with heuristic evaluation, move ordering, and early termination
- **Capture-biased rollouts** by default (prioritizes captures for more realistic play)
- **12× faster** than initial implementation through profiling-driven optimizations
- **Competitive with Minimax** at moderate simulation counts (150+ simulations)
