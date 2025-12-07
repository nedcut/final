from __future__ import annotations

from minichess.agents.base import Agent
from minichess.evaluation import material_balance_for_player
from minichess.game import MiniChessState, Move


class GreedyAgent(Agent):
    """One-ply material maximizer (no search)."""

    def choose_move(self, state: MiniChessState) -> Move:
        """Pick the move that maximizes material after one ply (break ties arbitrarily)."""
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")

        player = state.to_move  # Who is making the move
        best_move = moves[0]
        best_score = material_balance_for_player(
            state.make_move(moves[0], validate=False), player
        )

        for move in moves[1:]:
            score = material_balance_for_player(
                state.make_move(move, validate=False), player
            )
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
