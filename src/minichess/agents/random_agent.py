from __future__ import annotations

import random

from minichess.game import MiniChessState, Move
from minichess.agents.base import Agent


class RandomAgent(Agent):
    """Chooses uniformly among the available legal moves."""

    def choose_move(self, state: MiniChessState) -> Move:
        """Return a random legal move; raises if no moves are available."""
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")
        # Uniform random pick among legal options
        return random.choice(moves)
