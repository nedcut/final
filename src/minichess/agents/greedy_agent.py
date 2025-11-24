from __future__ import annotations

from minichess.agents.base import Agent
from minichess.game import MiniChessState, Move


MATERIAL = {
    "P": 1,
    "N": 3,
    "B": 3,
    "R": 5,
    "Q": 9,
    "K": 1000,
}


class GreedyAgent(Agent):
    """One-ply material maximizer (no search)."""

    def choose_move(self, state: MiniChessState) -> Move:
        """Pick the move that maximizes material after one ply (break ties arbitrarily)."""
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")

        best_move = moves[0]
        best_score = self._material_score(state.make_move(moves[0], validate=False))

        for move in moves[1:]:
            score = self._material_score(state.make_move(move, validate=False))
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    @staticmethod
    def _material_score(state: MiniChessState) -> int:
        score = 0
        for row in state.board:
            for piece in row:
                if piece is None:
                    continue
                value = MATERIAL[piece.upper()]
                score += value if piece.isupper() else -value
        return score if state.to_move == "W" else -score
