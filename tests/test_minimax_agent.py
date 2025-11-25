import math
import time

from minichess.agents import MinimaxAgent
from minichess.game import MiniChessState, Move, initial_state


def test_minimax_returns_legal_move():
    """Basic sanity check: minimax should return a legal move from the starting position."""
    state = initial_state()
    agent = MinimaxAgent(depth=2)
    move = agent.choose_move(state)
    assert move in state.legal_moves()


def test_minimax_depth_zero():
    """Depth=0 should work as evaluation-only mode without infinite recursion."""
    state = initial_state()
    agent = MinimaxAgent(depth=0)

    # Should return a legal move (though it's just picking based on immediate eval)
    move = agent.choose_move(state)
    assert move in state.legal_moves()

    # Should not hang or recurse infinitely
    # If this test completes quickly, depth=0 is handled correctly


def test_minimax_finds_checkmate_in_one():
    """Minimax should find an immediate checkmate when available."""
    # Position: White to move, can checkmate with Rook
    # Board:
    # 4  k . . . .
    # 3  . . . . .
    # 2  . . . . .
    # 1  R . . . .
    # 0  K . . . .
    #    a b c d e
    # White rook at a1 can move to a4 to deliver checkmate (king on a4 trapped at edge)
    board = (
        ("K", None, None, None, None),  # row 0
        ("R", None, None, None, None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        ("k", None, None, None, None),  # row 4
    )
    state = MiniChessState(board=board, to_move="W")

    agent = MinimaxAgent(depth=2)
    move = agent.choose_move(state)

    # Verify the chosen move leads to a win
    next_state = state.make_move(move, validate=False)
    # After white's move, black should have no legal moves (checkmate)
    # The rook should move to attack the king, ideally delivering mate
    # With depth=2, minimax should find the forced mate sequence
    assert next_state.is_terminal() and next_state.result() == 1.0, \
        f"Minimax should find checkmate, but chose {move}. Next state: {next_state.render()}"


def test_minimax_avoids_immediate_loss():
    """Minimax should avoid moves that lead to immediate checkmate."""
    # Position: Black to move, most moves lose immediately
    # Board:
    # 4  r . . . k
    # 3  . . . . .
    # 2  . . . . .
    # 1  . . . . .
    # 0  R . . . K
    #    a b c d e
    # Black king at e4, if it moves away from e-file, White's Ra0 can checkmate
    # Black should move rook to defend or attack
    board = (
        ("R", None, None, None, "K"),  # row 0
        (None, None, None, None, None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        ("r", None, None, None, "k"),  # row 4
    )
    state = MiniChessState(board=board, to_move="B")

    agent = MinimaxAgent(depth=3)
    move = agent.choose_move(state)

    # After black's move, white should not be able to checkmate immediately
    next_state = state.make_move(move, validate=False)
    white_agent = MinimaxAgent(depth=1)
    white_move = white_agent.choose_move(next_state)
    after_white = next_state.make_move(white_move, validate=False)

    # Black should still be alive after white's best response
    assert not (after_white.is_terminal() and after_white.result() == 1.0), \
        f"Minimax chose a move that allows immediate checkmate: {move}"


def test_minimax_depth_affects_play():
    """Deeper search should find better moves in tactical positions."""
    # Position where shallow search misses a winning combination
    # Board: White has a 2-move checkmate that depth-1 won't see
    # 4  . . . k .
    # 3  . . . . .
    # 2  . . . . .
    # 1  Q . . . .
    # 0  . . . . K
    #    a b c d e
    # Queen can move to d4 then d1 for mate (or direct tactics)
    board = (
        (None, None, None, None, "K"),  # row 0
        ("Q", None, None, None, None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        (None, None, None, "k", None),  # row 4
    )
    state = MiniChessState(board=board, to_move="W")

    # Depth-1 just evaluates immediate position
    shallow_agent = MinimaxAgent(depth=1)
    # Depth-3 can see 3 plies ahead and find forced mate
    deep_agent = MinimaxAgent(depth=3)

    shallow_move = shallow_agent.choose_move(state)
    deep_move = deep_agent.choose_move(state)

    # Both should be legal
    assert shallow_move in state.legal_moves()
    assert deep_move in state.legal_moves()

    # Play out both moves and evaluate the resulting positions
    # Deeper search should lead to a more dominant position
    shallow_result = state.make_move(shallow_move, validate=False)
    deep_result = state.make_move(deep_move, validate=False)

    # Use minimax itself to evaluate which position is better for White
    evaluator = MinimaxAgent(depth=2)

    # Get evaluation scores (higher is better for White)
    # We evaluate from the opponent's perspective (black's turn), so negate
    shallow_eval = -evaluator._search(
        shallow_result, depth=2, alpha=-math.inf, beta=math.inf,
        maximizing_color="W", deadline=None
    )
    deep_eval = -evaluator._search(
        deep_result, depth=2, alpha=-math.inf, beta=math.inf,
        maximizing_color="W", deadline=None
    )

    # Deep search should find at least as good a position
    # (Allow some tolerance for equal positions)
    assert deep_eval >= shallow_eval - 0.1, \
        f"Depth-3 eval ({deep_eval}) should be >= depth-1 eval ({shallow_eval})"


def test_minimax_respects_time_limit():
    """Time limit should prevent search from taking too long."""
    state = initial_state()
    time_limit = 0.1  # 100ms limit
    agent = MinimaxAgent(depth=10, time_limit=time_limit)  # depth=10 would take very long

    start = time.perf_counter()
    move = agent.choose_move(state)
    elapsed = time.perf_counter() - start

    assert move in state.legal_moves()
    # Allow some overhead, but should be roughly within time limit
    assert elapsed < time_limit * 2.0, f"Search took {elapsed:.3f}s, exceeded limit of {time_limit}s"


def test_minimax_as_black():
    """Minimax should work correctly when playing as Black."""
    # Position: Black to move, can capture white's queen
    # Board:
    # 4  r . . . k
    # 3  . . . . .
    # 2  . . . . .
    # 1  . . . . .
    # 0  R . Q . K
    #    a b c d e
    board = (
        ("R", None, "Q", None, "K"),  # row 0
        (None, None, None, None, None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        ("r", None, None, None, "k"),  # row 4
    )
    state = MiniChessState(board=board, to_move="B")

    agent = MinimaxAgent(depth=2)
    move = agent.choose_move(state)

    # Black should capture the queen (high value piece)
    # The rook should move from a4 to c0 (if that's the best capture)
    next_state = state.make_move(move, validate=False)

    # Verify black made a good move (should have good material advantage)
    # At minimum, should be a legal move
    assert move in state.legal_moves()


def test_minimax_prefers_material_advantage():
    """Minimax should prefer capturing more valuable pieces."""
    # Position: White to move, can capture queen or pawn
    # Board:
    # 4  . . . . .
    # 3  . k . . .
    # 2  . p q . .
    # 1  . . R . .
    # 0  . . . . K
    #    a b c d e
    # Rook at c1 can capture either pawn at b2 (value 1) or queen at c2 (value 9)
    board = (
        (None, None, None, None, "K"),  # row 0
        (None, None, "R", None, None),  # row 1
        (None, "p", "q", None, None),  # row 2
        (None, "k", None, None, None),  # row 3
        (None, None, None, None, None),  # row 4
    )
    state = MiniChessState(board=board, to_move="W")

    agent = MinimaxAgent(depth=2)
    move = agent.choose_move(state)

    # Rook should capture queen (at c2) rather than pawn (at b2)
    # Queen is worth 9, pawn is worth 1
    next_state = state.make_move(move, validate=False)
    # Check that white captured the queen (queen should be gone from c2)
    assert next_state.board[2][2] != "q", \
        f"Expected rook to capture queen at c2, but got {move}"


def test_minimax_evaluates_terminal_correctly_for_black():
    """
    Regression test: ensure terminal states are evaluated from correct perspective.
    Black should recognize when Black wins as good, and White wins as bad.
    """
    # Position: Black can checkmate in one move
    # Board:
    # 4  . . . . .
    # 3  . . . . .
    # 2  . . . . .
    # 1  . . . K .
    # 0  q . . . k
    #    a b c d e
    # Black queen at a0 can deliver checkmate by moving to d1 or nearby
    board = (
        ("q", None, None, None, "k"),  # row 0
        (None, None, None, "K", None),  # row 1
        (None, None, None, None, None),  # row 2
        (None, None, None, None, None),  # row 3
        (None, None, None, None, None),  # row 4
    )
    state = MiniChessState(board=board, to_move="B")

    agent = MinimaxAgent(depth=2)
    move = agent.choose_move(state)

    # Black should deliver checkmate
    next_state = state.make_move(move, validate=False)
    assert next_state.is_terminal() and next_state.result() == -1.0, \
        f"Black should find checkmate (result=-1.0 for black win), but chose {move}"
