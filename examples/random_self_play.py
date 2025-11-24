"""Random vs random self-play loop for Gardner MiniChess."""

from __future__ import annotations

from minichess.agents import RandomAgent
from minichess.game import MiniChessState, initial_state


def play_game(max_plies: int = 1000, verbose: bool = True) -> MiniChessState:
    """Run random self-play up to a ply cap; returns the final state."""
    state = initial_state()
    agents = {"W": RandomAgent(), "B": RandomAgent()}
    ply = 0

    while not state.is_terminal() and ply < max_plies:
        mover = agents[state.to_move]
        move = mover.choose_move(state)
        state = state.make_move(move, validate=False)  # move comes from legal_moves()
        ply += 1

    if verbose:
        print(state.render())
        if state.is_terminal():
            result = state.result()
            outcome = "1-0" if result > 0 else "0-1" if result < 0 else "draw"
            print(f"Game over in {ply} plies: {outcome}")
        else:
            print(f"Reached ply cap ({max_plies}); treating as drawish.")

    return state


if __name__ == "__main__":
    play_game()
