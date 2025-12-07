from __future__ import annotations

import random
from typing import Optional

from minichess.game import MiniChessState, Move
from minichess.agents.base import Agent


class RandomAgent(Agent):
    """Chooses uniformly among the available legal moves."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional random seed for reproducibility.

        Args:
            seed: Random seed. If None, uses a dedicated Random instance
                  (not the global random module) for isolation.
        """
        self._rng = random.Random(seed)

    def choose_move(self, state: MiniChessState) -> Move:
        """Return a random legal move; raises if no moves are available."""
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")
        return self._rng.choice(moves)
