from __future__ import annotations

import math
import time
from enum import IntEnum
from typing import Optional

from minichess.agents.base import Agent
from minichess.evaluation import MATERIAL
from minichess.game import Board, MiniChessState, Move


class _TTFlag(IntEnum):
    """Transposition table entry type."""
    EXACT = 0    # Exact score
    LOWER = 1    # Score is a lower bound (alpha cutoff)
    UPPER = 2    # Score is an upper bound (beta cutoff)


class MinimaxAgent(Agent):
    """Depth-limited minimax with alpha-beta pruning, transposition table, and iterative deepening."""

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
        # Transposition table: (board, to_move) -> (depth, score, flag, best_move)
        self._tt: dict[tuple[Board, str], tuple[int, float, _TTFlag, Optional[Move]]] = {}

    def choose_move(self, state: MiniChessState) -> Move:
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal moves available.")

        # Clear transposition table for new search (prevents stale entries)
        self._tt.clear()

        root_color = state.to_move
        deadline = time.perf_counter() + self.time_limit if self.time_limit else None

        # Use iterative deepening: search depth 1, 2, ... up to target depth
        # This improves move ordering and provides any-time behavior
        best_move = moves[0]
        best_score = -math.inf

        for current_depth in range(1, self.depth + 1):
            if self._timed_out(deadline):
                break

            # Get move ordering from previous iteration (principal variation first)
            ordered_moves = self._order_moves_with_pv(state, moves, best_move)

            iteration_best_move = ordered_moves[0]
            iteration_best_score = -math.inf
            alpha, beta = -math.inf, math.inf

            for move in ordered_moves:
                if self._timed_out(deadline):
                    break

                child = state.make_move(move, validate=False)
                score = self._search(
                    child,
                    depth=current_depth - 1,
                    alpha=alpha,
                    beta=beta,
                    maximizing_color=root_color,
                    deadline=deadline,
                )

                if score > iteration_best_score:
                    iteration_best_score = score
                    iteration_best_move = move
                alpha = max(alpha, iteration_best_score)

            # Only update if we completed this iteration (not timed out)
            if not self._timed_out(deadline):
                best_move = iteration_best_move
                best_score = iteration_best_score

                # Early exit if we found a winning move
                if best_score >= 9000:  # Near terminal win
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
        # Check for terminal or timeout first
        if self._timed_out(deadline):
            return self._evaluate(state, maximizing_color)

        # Check terminal state
        is_terminal, terminal_result = state.terminal_result()
        if is_terminal:
            terminal_score = terminal_result * 10000
            return terminal_score if maximizing_color == "W" else -terminal_score

        if depth <= 0:
            return self._evaluate(state, maximizing_color)

        # Transposition table lookup
        tt_key = (state.board, state.to_move)
        tt_entry = self._tt.get(tt_key)
        tt_move: Optional[Move] = None

        if tt_entry is not None:
            tt_depth, tt_score, tt_flag, tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == _TTFlag.EXACT:
                    return tt_score
                elif tt_flag == _TTFlag.LOWER:
                    alpha = max(alpha, tt_score)
                elif tt_flag == _TTFlag.UPPER:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        maximizing_turn = state.to_move == maximizing_color
        moves = state.legal_moves()

        # Order moves: TT move first, then captures, then quiet moves
        ordered_moves = self._order_moves_with_pv(state, moves, tt_move)

        if maximizing_turn:
            value = -math.inf
            best_move_here: Optional[Move] = None

            for move in ordered_moves:
                child = state.make_move(move, validate=False)
                child_value = self._search(child, depth - 1, alpha, beta, maximizing_color, deadline)

                if child_value > value:
                    value = child_value
                    best_move_here = move

                alpha = max(alpha, value)
                if beta <= alpha or self._timed_out(deadline):
                    break

            # Store in transposition table
            if not self._timed_out(deadline):
                if value <= alpha:
                    flag = _TTFlag.UPPER
                elif value >= beta:
                    flag = _TTFlag.LOWER
                else:
                    flag = _TTFlag.EXACT
                self._tt[tt_key] = (depth, value, flag, best_move_here)

            return value

        # Minimizing
        value = math.inf
        best_move_here = None

        for move in ordered_moves:
            child = state.make_move(move, validate=False)
            child_value = self._search(child, depth - 1, alpha, beta, maximizing_color, deadline)

            if child_value < value:
                value = child_value
                best_move_here = move

            beta = min(beta, value)
            if beta <= alpha or self._timed_out(deadline):
                break

        # Store in transposition table
        if not self._timed_out(deadline):
            if value <= alpha:
                flag = _TTFlag.UPPER
            elif value >= beta:
                flag = _TTFlag.LOWER
            else:
                flag = _TTFlag.EXACT
            self._tt[tt_key] = (depth, value, flag, best_move_here)

        return value

    @staticmethod
    def _evaluate(state: MiniChessState, perspective: str) -> float:
        """Evaluate position from perspective player's point of view."""
        score = 0
        for row in state.board:
            for piece in row:
                if piece is None:
                    continue
                value = MATERIAL[piece.upper()]
                score += value if piece.isupper() else -value

        return score if perspective == "W" else -score

    def _order_moves_with_pv(
        self, state: MiniChessState, moves: list[Move], pv_move: Optional[Move]
    ) -> list[Move]:
        """Order moves: PV/TT move first, then captures, then quiet moves."""
        if not moves:
            return moves

        def move_score(m: Move) -> int:
            if m == pv_move:
                return 1000  # Highest priority
            target = state.board[m.to_sq[0]][m.to_sq[1]]
            if target is not None:
                return 100 + MATERIAL.get(target.upper(), 0)  # Captures by value
            return 0  # Quiet moves

        return sorted(moves, key=move_score, reverse=True)

    @staticmethod
    def _timed_out(deadline: Optional[float]) -> bool:
        return deadline is not None and time.perf_counter() >= deadline
