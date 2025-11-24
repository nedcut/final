from __future__ import annotations

from abc import ABC, abstractmethod

from minichess.game import MiniChessState, Move


class Agent(ABC):
    """Interface for anything that chooses a legal move in MiniChess."""

    @abstractmethod
    def choose_move(self, state: MiniChessState) -> Move:
        """Return a legal move for the given state (implementations should raise if none exist)."""
        raise NotImplementedError
