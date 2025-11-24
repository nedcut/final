"""Greedy vs random demo game."""

from __future__ import annotations

from minichess.agents import GreedyAgent, RandomAgent
from minichess.game import initial_state


def play_game(max_plies: int = 200, verbose: bool = True):
    """Run a single game: Greedy (White) vs Random (Black)."""
    state = initial_state()
    agents = {"W": GreedyAgent(), "B": RandomAgent()}
    ply = 0

    while not state.is_terminal() and ply < max_plies:
        mover = agents[state.to_move]
        move = mover.choose_move(state)
        state = state.make_move(move, validate=False)  # move came from legal_moves()
        ply += 1

    if verbose:
        print(state.render())
        if state.is_terminal():
            result = state.result()
            outcome = "1-0" if result > 0 else "0-1" if result < 0 else "½-½"
            print(f"Game over in {ply} plies: {outcome} (Greedy vs Random)")
        else:
            print(f"Reached ply cap ({max_plies}); treating as drawish.")

    return state


if __name__ == "__main__":
    play_game()
