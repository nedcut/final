from __future__ import annotations

import random

from minichess.game import MiniChessState, Move
from minichess.agents.base import Agent


class RandomAgent(Agent):
    """Chooses a legal move uniformly at random."""

    def choose_move(self, state: MiniChessState) -> Move:
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")
        return random.choice(moves)
