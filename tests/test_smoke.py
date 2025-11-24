from minichess.game import initial_board, initial_state


def test_initial_board_shape():
    board = initial_board()
    assert len(board) == 5
    assert all(len(row) == 5 for row in board)


def test_initial_state_render_runs():
    state = initial_state()
    rendered = state.render()
    assert "a b c d e" in rendered


def test_initial_legal_moves_count():
    state = initial_state()
    moves = state.legal_moves()
    # White can push five pawns or move the knight to two squares.
    assert len(moves) == 7
