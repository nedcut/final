from __future__ import annotations

import math
import time
from typing import Optional

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


class MinimaxAgent(Agent):
    """Depth-limited minimax with alpha-beta pruning and material evaluation."""

    def __init__(self, depth: int = 3, time_limit: Optional[float] = None):
        """
        Args:
            depth: maximum search depth (plies). Use depth=0 for evaluation-only (no search),
                   depth=1 for single-ply lookahead, depth=2+ for full minimax search.
            time_limit: optional per-move wall-clock limit in seconds. If exceeded,
                the agent returns the best move evaluated so far.
        """
        if depth < 0:
            raise ValueError("depth must be non-negative (0 = evaluation only, 1+ = search)")
        self.depth = depth
        self.time_limit = time_limit

    def choose_move(self, state: MiniChessState) -> Move:
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")

        root_color = state.to_move
        best_move = moves[0]
        best_score = -math.inf
        alpha, beta = -math.inf, math.inf
        # Soft deadline so we can bail early if time-limited
        deadline = time.perf_counter() + self.time_limit if self.time_limit else None

        for move in self._order_moves(state, moves):
            child = state.make_move(move, validate=False)
            score = self._search(
                child,
                depth=self.depth - 1,
                alpha=alpha,
                beta=beta,
                maximizing_color=root_color,
                deadline=deadline,
            )
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if deadline is not None and time.perf_counter() >= deadline:
                break

        return best_move

    def _search(
        self,
        state: MiniChessState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_color: str,
        deadline: Optional[float],
    ) -> float:
        if depth <= 0 or state.is_terminal() or self._timed_out(deadline):
            return self._evaluate(state, maximizing_color)

        maximizing_turn = state.to_move == maximizing_color

        if maximizing_turn:
            value = -math.inf
            for move in self._order_moves(state, state.legal_moves()):
                child = state.make_move(move, validate=False)
                value = max(
                    value,
                    self._search(child, depth - 1, alpha, beta, maximizing_color, deadline),
                )
                # Standard alpha-beta cutoff
                alpha = max(alpha, value)
                if beta <= alpha or self._timed_out(deadline):
                    break
            return value

        value = math.inf
        for move in self._order_moves(state, state.legal_moves()):
            child = state.make_move(move, validate=False)
            value = min(
                value,
                self._search(child, depth - 1, alpha, beta, maximizing_color, deadline),
            )
            # Standard alpha-beta cutoff
            beta = min(beta, value)
            if beta <= alpha or self._timed_out(deadline):
                break
        return value

    @staticmethod
    def _evaluate(state: MiniChessState, perspective: str) -> float:
        if state.is_terminal():
            result = state.result()  # +1 white, -1 black
            terminal_score = result * 10000  # ensure terminal wins dominate heuristics
            # Apply perspective: White wants +score for white wins, Black wants -score for white wins
            return terminal_score if perspective == "W" else -terminal_score

        score = 0
        for row in state.board:
            for piece in row:
                if piece is None:
                    continue
                value = MATERIAL[piece.upper()]
                score += value if piece.isupper() else -value

        return score if perspective == "W" else -score

    @staticmethod
    def _order_moves(state: MiniChessState, moves: list[Move]) -> list[Move]:
        """Simple move ordering: captures first, then others."""
        def is_capture(m: Move) -> bool:
            return state.board[m.to_sq[0]][m.to_sq[1]] is not None

        captures = [m for m in moves if is_capture(m)]
        quiets = [m for m in moves if not is_capture(m)]
        return captures + quiets

    @staticmethod
    def _timed_out(deadline: Optional[float]) -> bool:
        return deadline is not None and time.perf_counter() >= deadline
