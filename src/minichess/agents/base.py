from __future__ import annotations

from abc import ABC, abstractmethod

from minichess.game import MiniChessState, Move


class Agent(ABC):
    """Interface for agents that choose moves in MiniChess."""

    @abstractmethod
    def choose_move(self, state: MiniChessState) -> Move:
        """Select a move from the given state."""
        raise NotImplementedError
