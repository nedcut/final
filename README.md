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
