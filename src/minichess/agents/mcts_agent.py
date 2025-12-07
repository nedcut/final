from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from minichess.agents.base import Agent
from minichess.evaluation import MATERIAL
from minichess.game import Board, MiniChessState, Move


@dataclass
class _Node:
    state: MiniChessState
    visits: int = 0
    value: float = 0.0  # accumulated reward from the player-to-move perspective
    untried_moves: List[Move] = field(default_factory=list)
    children: Dict[Move, "_Node"] = field(default_factory=dict)


class MCTSAgent(Agent):
    """Monte Carlo Tree Search agent with UCB1 selection and optimizations."""

    def __init__(
        self,
        simulations: int = 500,
        time_limit: Optional[float] = None,
        exploration_c: float = math.sqrt(2.0),
        rollout_depth: int = 20,
        rollout_policy: str = "capture_bias",
        seed: Optional[int] = None,
    ):
        if simulations <= 0:
            raise ValueError("simulations must be positive")
        if time_limit is not None and time_limit <= 0:
            raise ValueError("time_limit must be positive when provided")
        if rollout_depth <= 0:
            raise ValueError("rollout_depth must be positive")
        if exploration_c <= 0:
            raise ValueError("exploration_c must be positive")
        self.simulations = simulations
        self.time_limit = time_limit
        self.exploration_c = exploration_c
        self.rollout_depth = rollout_depth
        self.rollout_policy = rollout_policy
        self._rng = random.Random(seed) if seed is not None else random

    def choose_move(self, state: MiniChessState) -> Move:
        """Select the best move using Monte Carlo Tree Search."""
        legal = state.legal_moves()
        if not legal:
            raise ValueError("No legal moves available.")

        # Shortcut: single legal move
        if len(legal) == 1:
            return legal[0]

        # Key transpositions on position only (board + side to move), not history.
        nodes: Dict[Tuple[Board, str], _Node] = {}
        root = self._get_node(nodes, state, legal)
        deadline = time.perf_counter() + self.time_limit if self.time_limit else None

        simulations_run = 0
        while simulations_run < self.simulations and not self._timed_out(deadline):
            self._run_simulation(root, nodes, deadline)
            simulations_run += 1

        # Pick the child with the most visits (robust child)
        if not root.children:
            return legal[0]  # fallback, shouldn't happen
        best_move, _ = max(
            root.children.items(),
            key=lambda item: item[1].visits,
        )
        return best_move

    def _run_simulation(
        self,
        root: _Node,
        nodes: Dict[Tuple[Board, str], _Node],
        deadline: Optional[float],
    ) -> None:
        """Execute one MCTS simulation: Selection, Expansion, Simulation, Backpropagation."""
        path: List[_Node] = [root]
        node = root
        state = root.state

        # Selection
        while not node.untried_moves and node.children:
            node = self._select_child(node)
            state = node.state
            path.append(node)
            if self._timed_out(deadline):
                break

        # Expansion
        if not self._timed_out(deadline) and node.untried_moves:
            move = node.untried_moves.pop()
            next_state = state.make_move(move, validate=False)
            child_legal = next_state.legal_moves()
            child = self._get_node(nodes, next_state, child_legal)
            node.children[move] = child
            node = child
            state = next_state
            path.append(node)

        # Simulation
        result_white_perspective = self._rollout(state, deadline)

        # Backpropagation
        for n in path:
            n.visits += 1
            n.value += result_white_perspective if n.state.to_move == "W" else -result_white_perspective

    def _select_child(self, node: _Node) -> _Node:
        """Select best child using UCB1 formula."""
        # UCB1 selection; child values are from the child's player perspective,
        # so flip sign to evaluate from the parent player's perspective.
        assert node.visits > 0, "select_child called before node was visited"
        log_parent = math.log(node.visits)

        def score(child: _Node) -> float:
            if not child.visits:
                mean = 0.0
            else:
                sign = -1.0 if node.state.to_move != child.state.to_move else 1.0
                mean = sign * (child.value / child.visits)
            # Encourage low-visit nodes until they are explored
            explore = self.exploration_c * math.sqrt(log_parent / child.visits) if child.visits else float("inf")
            return mean + explore

        return max(node.children.values(), key=score)

    def _rollout(self, state: MiniChessState, deadline: Optional[float]) -> float:
        """Simulate random game play from given state to estimate value."""
        current = state
        depth = 0
        while depth < self.rollout_depth:
            if self._timed_out(deadline):
                break
            moves = current.legal_moves()
            if not moves:  # Terminal state (checkmate or stalemate)
                # Use _result_no_moves since we already know there are no moves
                return current._result_no_moves()

            # Early termination: overwhelming material advantage (saves ~10% rollout time)
            if depth > 5:  # Only check after some moves to avoid overhead
                eval_score = self._evaluate_position(current)
                if abs(eval_score) > 0.5:  # ~Queen advantage or more
                    return eval_score

            move = self._choose_rollout_move(current, moves)
            current = current.make_move(move, validate=False)
            depth += 1

        # Use heuristic evaluation for non-terminal positions
        return self._evaluate_position(current)

    def _choose_rollout_move(self, state: MiniChessState, moves: List[Move]) -> Move:
        """Select a move for rollout simulation according to the rollout policy."""
        if self.rollout_policy == "capture_bias":
            captures = [m for m in moves if state.board[m.to_sq[0]][m.to_sq[1]] is not None]
            if captures:
                return self._rng.choice(captures)
        return self._rng.choice(moves)

    @staticmethod
    def _evaluate_position(state: MiniChessState) -> float:
        """Heuristic evaluation of a non-terminal position from White's perspective.

        Returns a value in approximately [-1, 1] based on material advantage.
        Normalized by dividing by total material to keep values similar to terminal results.
        """
        score = 0
        total_material = 0

        for row in state.board:
            for piece in row:
                if piece is None:
                    continue
                value = MATERIAL[piece.upper()]
                # Skip kings from total material (they're always present)
                if piece.upper() != "K":
                    total_material += value
                score += value if piece.isupper() else -value

        # Normalize to approximately [-1, 1] range
        # Use max to avoid division by zero if only kings remain
        return score / max(total_material, 20)

    @staticmethod
    def _timed_out(deadline: Optional[float]) -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    @staticmethod
    def _get_node(nodes: Dict[Tuple[Board, str], _Node], state: MiniChessState, legal_moves: List[Move]) -> _Node:
        """Get or create a node for the given position (transposition table lookup)."""
        key = (state.board, state.to_move)
        if key not in nodes:
            # Order moves for better expansion: captures first, then quiet moves
            captures = [m for m in legal_moves if state.board[m.to_sq[0]][m.to_sq[1]] is not None]
            quiet = [m for m in legal_moves if state.board[m.to_sq[0]][m.to_sq[1]] is None]
            ordered_moves = captures + quiet
            nodes[key] = _Node(state=state, untried_moves=ordered_moves)
        return nodes[key]
