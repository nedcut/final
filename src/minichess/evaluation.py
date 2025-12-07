"""Shared evaluation constants and utilities for MiniChess agents."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from minichess.game import MiniChessState

# Standard piece values (centipawn-like, but simplified)
# King value is high to ensure checkmate is always prioritized
MATERIAL: dict[str, int] = {
    "P": 1,   # Pawn
    "N": 3,   # Knight
    "B": 3,   # Bishop
    "R": 5,   # Rook
    "Q": 9,   # Queen
    "K": 1000,  # King (effectively infinite for material counting)
}


def material_balance(state: "MiniChessState") -> int:
    """Calculate material balance from White's perspective.

    Returns:
        Positive value if White has more material, negative if Black does.
    """
    score = 0
    for row in state.board:
        for piece in row:
            if piece is None:
                continue
            value = MATERIAL[piece.upper()]
            score += value if piece.isupper() else -value
    return score


def material_balance_for_player(state: "MiniChessState", perspective: str) -> int:
    """Calculate material balance from the specified player's perspective.

    Args:
        state: Current game state
        perspective: "W" for White's perspective, "B" for Black's

    Returns:
        Positive value if the specified player has more material.
    """
    balance = material_balance(state)
    return balance if perspective == "W" else -balance
