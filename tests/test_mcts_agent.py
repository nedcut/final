import time

from minichess.agents import MCTSAgent
from minichess.game import MiniChessState, initial_state


def test_mcts_returns_legal_move():
    state = initial_state()
    agent = MCTSAgent(simulations=30, rollout_depth=10, seed=123)
    move = agent.choose_move(state)
    assert move in state.legal_moves()


def test_mcts_time_limit_respected():
    state = initial_state()
    agent = MCTSAgent(simulations=10_000, time_limit=0.05, rollout_depth=5, seed=123)
    start = time.perf_counter()
    move = agent.choose_move(state)
    elapsed = time.perf_counter() - start
    assert move in state.legal_moves()
    assert elapsed < 0.2, f"Search exceeded expected time budget: {elapsed:.3f}s"


def test_mcts_finds_checkmate_in_one():
    # White rook on a1 can capture the king on a4 for an immediate win.
    board = (
        ("K", None, None, None, None),  # row 0
        ("R", None, None, None, None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        ("k", None, None, None, None),  # row 4
    )
    state = MiniChessState(board=board, to_move="W")

    # Increase simulations for more reliable tactical play
    agent = MCTSAgent(simulations=200, rollout_depth=10, seed=123)
    move = agent.choose_move(state)

    next_state = state.make_move(move, validate=False)
    assert next_state.is_terminal() and next_state.result() == 1.0, \
        f"MCTS should find mate, but chose {move}"


def test_mcts_raises_when_no_legal_moves():
    empty_board = tuple((None,) * 5 for _ in range(5))
    state = MiniChessState(board=empty_board, to_move="W")
    agent = MCTSAgent(simulations=5, rollout_depth=2, seed=1)

    try:
        agent.choose_move(state)
        assert False, "Expected ValueError when no legal moves are available"
    except ValueError:
        pass
