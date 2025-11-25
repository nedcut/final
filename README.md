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

### Random vs Random self-play
- Run the sample script: `python examples/random_self_play.py`
- It plays random vs random up to a ply cap and prints the final board/outcome.

### Universal match runner
- Run: `python examples/match_runner.py --white minimax --black greedy --games 100 --swap-colors --white-depth 3`
- Flags: `--white/--black` agent names (available: random, greedy, minimax), `--games`, `--max-plies`, `--swap-colors`, `--print-every N`, `--seed`, `--list-agents`.
- Minimax knobs (used only when the chosen side is `minimax`): `--white-depth/--black-depth` (default: 3), `--white-time-limit/--black-time-limit` (optional, in seconds).
- Example: `python examples/match_runner.py --white minimax --black random --games 200 --white-depth 2 --seed 42`

### Greedy vs Random
- Run: `python examples/greedy_vs_random.py`
- Greedy (White) plays Random (Black) up to a ply cap and prints the result.

### Greedy vs Greedy self-play
- Run: `python examples/greedy_self_play.py`
- One-ply material agents play until terminal or ply cap and print the result.

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
