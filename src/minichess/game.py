from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

BOARD_SIZE = 5
Board = Tuple[Tuple[Optional[str], ...], ...]  # 5x5 grid of piece codes or None


@dataclass(frozen=True)
class Move:
    """A discrete move (from_row, from_col) -> (to_row, to_col), with optional promotion piece."""

    from_sq: Tuple[int, int]
    to_sq: Tuple[int, int]
    promotion: Optional[str] = None  # e.g., 'Q' for pawn promotions


@dataclass(frozen=True)
class MiniChessState:
    """Immutable Gardner MiniChess state (5x5, no castling/en passant, single pawn push)."""

    board: Board
    to_move: str  # 'W' or 'B'
    move_history: Tuple[Move, ...] = field(default_factory=tuple)
    # For draw detection:
    halfmove_clock: int = 0  # Moves since last pawn move or capture (50-move rule)
    position_history: Tuple[Tuple[Board, str], ...] = field(default_factory=tuple)  # For repetition

    def legal_moves(self) -> List[Move]:
        """Enumerate all legal moves that do not leave the side to move in check."""
        pseudo_moves: List[Move] = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece is None or _piece_color(piece) != self.to_move:
                    continue
                pseudo_moves.extend(_piece_moves(self.board, r, c, piece))

        legal: List[Move] = []
        for move in pseudo_moves:
            next_board = _apply_move(self.board, move)
            # Only keep moves that leave our king safe
            if not _is_in_check(next_board, self.to_move):
                legal.append(move)
        return legal

    def make_move(self, move: Move, validate: bool = True) -> "MiniChessState":
        """Apply a move and return a new state.

        Leave `validate=True` when consuming user/agent input; set `validate=False` only if the
        move already came from `legal_moves()` to avoid duplicate generation work."""
        if validate and move not in self.legal_moves():
            raise ValueError("Illegal move")

        # Check if this is a pawn move or capture (resets halfmove clock)
        moving_piece = self.board[move.from_sq[0]][move.from_sq[1]]
        is_capture = self.board[move.to_sq[0]][move.to_sq[1]] is not None
        is_pawn_move = moving_piece is not None and moving_piece.upper() == "P"

        next_board = _apply_move(self.board, move)
        next_history = self.move_history + (move,)
        next_player = "B" if self.to_move == "W" else "W"

        # Update halfmove clock (reset on pawn move or capture)
        next_halfmove = 0 if (is_pawn_move or is_capture) else self.halfmove_clock + 1

        # Track position for repetition detection
        next_position_history = self.position_history + ((self.board, self.to_move),)

        return MiniChessState(
            board=next_board,
            to_move=next_player,
            move_history=next_history,
            halfmove_clock=next_halfmove,
            position_history=next_position_history,
        )

    def is_draw(self) -> bool:
        """Check for draw by repetition, 50-move rule, or insufficient material."""
        # Threefold repetition
        current_pos = (self.board, self.to_move)
        repetitions = self.position_history.count(current_pos)
        if repetitions >= 2:  # Current position + 2 in history = 3 total
            return True

        # 50-move rule (100 halfmoves = 50 full moves)
        if self.halfmove_clock >= 100:
            return True

        # Insufficient material (just kings remaining)
        if self._insufficient_material():
            return True

        return False

    def _insufficient_material(self) -> bool:
        """Check if neither side can checkmate (only kings remain)."""
        pieces = []
        for row in self.board:
            for piece in row:
                if piece is not None and piece.upper() != "K":
                    pieces.append(piece)
        # Only kings remaining = draw
        # (Could extend to K+B vs K, K+N vs K, but keeping simple)
        return len(pieces) == 0

    def is_terminal(self) -> bool:
        """True when game is over (checkmate, stalemate, or draw)."""
        if self.is_draw():
            return True
        return not self.legal_moves()

    def result(self) -> float:
        """Return +1 for white win, -1 for black win, 0 for draw; requires terminal state."""
        if not self.is_terminal():
            raise ValueError("Game not finished")

        # Check for draws first (repetition, 50-move, insufficient material)
        if self.is_draw():
            return 0.0

        # No legal moves - check if checkmate or stalemate
        in_check = _is_in_check(self.board, self.to_move)
        if in_check:
            # Checkmate: current player lost
            return 1.0 if self.to_move == "B" else -1.0
        # Stalemate
        return 0.0

    def terminal_result(self) -> tuple[bool, float]:
        """Check if terminal and get result in one call, avoiding duplicate move generation.

        Returns:
            Tuple of (is_terminal, result). If not terminal, result is 0.0.
            Result is +1 for white win, -1 for black win, 0 for draw/stalemate.
        """
        # Check draws first (doesn't require move generation)
        if self.is_draw():
            return True, 0.0

        if self.legal_moves():
            return False, 0.0
        return True, self._result_no_moves()

    def _result_no_moves(self) -> float:
        """Get result when already known there are no legal moves (internal optimization).

        Call this only after confirming legal_moves() is empty.
        Returns +1 for white win, -1 for black win, 0 for stalemate.
        """
        in_check = _is_in_check(self.board, self.to_move)
        if in_check:
            # Checkmate: current player lost
            return 1.0 if self.to_move == "B" else -1.0
        # Stalemate
        return 0.0

    def render(self) -> str:
        """Return a simple text diagram with ranks/files labeled for debugging/CLI play."""
        rows: List[str] = []
        for r, rank in enumerate(self.board):
            rendered = []
            for piece in rank:
                rendered.append("." if piece is None else piece)
            rows.append(f"{4 - r} " + " ".join(rendered))  # rank labels from white's perspective
        rows.append("  a b c d e")
        return "\n".join(rows)


def initial_board() -> Board:
    """Canonical 5x5 starting position from Gardner MiniChess (white at rows 0–1)."""
    # R N B Q K
    # P P P P P
    # . . . . .
    # p p p p p
    # k q b n r
    top = ("r", "n", "b", "q", "k")
    top_pawns = ("p",) * 5
    empty = (None,) * 5
    bottom_pawns = tuple(p.upper() for p in top_pawns)
    bottom = tuple(p.upper() for p in top)
    return (
        bottom,
        bottom_pawns,
        empty,
        top_pawns,
        top,
    )


def initial_state() -> MiniChessState:
    """Starting state helper (white to move)."""
    return MiniChessState(board=initial_board(), to_move="W")


# --- Internal helpers ---


def _piece_color(piece: str) -> str:
    return "W" if piece.isupper() else "B"


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def _apply_move(board: Board, move: Move) -> Board:
    brd = [list(row) for row in board]
    piece = brd[move.from_sq[0]][move.from_sq[1]]
    brd[move.from_sq[0]][move.from_sq[1]] = None
    # Use promoted piece if provided (otherwise keep original)
    dest_piece = move.promotion if move.promotion is not None else piece
    brd[move.to_sq[0]][move.to_sq[1]] = dest_piece
    return tuple(tuple(row) for row in brd)


def _piece_moves(board: Board, r: int, c: int, piece: str) -> List[Move]:
    color = _piece_color(piece)
    p = piece.upper()
    if p == "P":
        return _pawn_moves(board, r, c, color)
    if p == "N":
        return _knight_moves(board, r, c, color)
    if p == "B":
        return _slider_moves(board, r, c, color, diagonals=True, orthogonals=False)
    if p == "R":
        return _slider_moves(board, r, c, color, diagonals=False, orthogonals=True)
    if p == "Q":
        return _slider_moves(board, r, c, color, diagonals=True, orthogonals=True)
    if p == "K":
        return _king_moves(board, r, c, color)
    return []


def _pawn_moves(board: Board, r: int, c: int, color: str) -> List[Move]:
    moves: List[Move] = []
    direction = 1 if color == "W" else -1
    promotion_rank = BOARD_SIZE - 1 if color == "W" else 0
    one_forward = (r + direction, c)
    if _in_bounds(*one_forward) and board[one_forward[0]][one_forward[1]] is None:
        if one_forward[0] == promotion_rank:
            moves.append(Move((r, c), one_forward, promotion="Q" if color == "W" else "q"))
        else:
            moves.append(Move((r, c), one_forward))
    for dc in (-1, 1):
        target = (r + direction, c + dc)
        if not _in_bounds(*target):
            continue
        target_piece = board[target[0]][target[1]]
        if target_piece is None or _piece_color(target_piece) == color:
            continue
        if target[0] == promotion_rank:
            moves.append(Move((r, c), target, promotion="Q" if color == "W" else "q"))
        else:
            moves.append(Move((r, c), target))
    return moves


def _knight_moves(board: Board, r: int, c: int, color: str) -> List[Move]:
    moves: List[Move] = []
    deltas = [
        (2, 1),
        (2, -1),
        (-2, 1),
        (-2, -1),
        (1, 2),
        (1, -2),
        (-1, 2),
        (-1, -2),
    ]
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if not _in_bounds(nr, nc):
            continue
        target = board[nr][nc]
        if target is None or _piece_color(target) != color:
            moves.append(Move((r, c), (nr, nc)))
    return moves


def _slider_moves(board: Board, r: int, c: int, color: str, *, diagonals: bool, orthogonals: bool) -> List[Move]:
    moves: List[Move] = []
    directions = []
    if diagonals:
        directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    if orthogonals:
        directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while _in_bounds(nr, nc):
            target = board[nr][nc]
            if target is None:
                moves.append(Move((r, c), (nr, nc)))
            else:
                if _piece_color(target) != color:
                    moves.append(Move((r, c), (nr, nc)))
                break
            nr += dr
            nc += dc
    return moves


def _king_moves(board: Board, r: int, c: int, color: str) -> List[Move]:
    moves: List[Move] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if not _in_bounds(nr, nc):
                continue
            target = board[nr][nc]
            if target is None or _piece_color(target) != color:
                moves.append(Move((r, c), (nr, nc)))
    return moves


def _find_king(board: Board, color: str) -> Optional[Tuple[int, int]]:
    target = "K" if color == "W" else "k"
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == target:
                return r, c
    return None


def _is_in_check(board: Board, color: str) -> bool:
    king_pos = _find_king(board, color)
    if king_pos is None:
        return True  # treat missing king as checked
    opponent = "B" if color == "W" else "W"
    return _square_attacked(board, king_pos[0], king_pos[1], by_color=opponent)


def _square_attacked(board: Board, r: int, c: int, *, by_color: str) -> bool:
    # Pawn attacks
    pawn_dir = 1 if by_color == "W" else -1
    for dc in (-1, 1):
        pr, pc = r - pawn_dir, c - dc
        if _in_bounds(pr, pc):
            if board[pr][pc] == ("P" if by_color == "W" else "p"):
                return True
    # Knight attacks
    for dr, dc in [
        (2, 1),
        (2, -1),
        (-2, 1),
        (-2, -1),
        (1, 2),
        (1, -2),
        (-1, 2),
        (-1, -2),
    ]:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            piece = board[nr][nc]
            if piece == ("N" if by_color == "W" else "n"):
                return True
    # Sliding attacks: bishops/queens (diagonals)
    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nr, nc = r + dr, c + dc
        while _in_bounds(nr, nc):
            piece = board[nr][nc]
            if piece is None:
                nr += dr
                nc += dc
                continue
            if _piece_color(piece) == by_color and piece.upper() in {"B", "Q"}:
                return True
            break
    # Sliding attacks: rooks/queens (orthogonals)
    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nr, nc = r + dr, c + dc
        while _in_bounds(nr, nc):
            piece = board[nr][nc]
            if piece is None:
                nr += dr
                nc += dc
                continue
            if _piece_color(piece) == by_color and piece.upper() in {"R", "Q"}:
                return True
            break
    # King attacks (adjacent squares)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if _in_bounds(nr, nc):
                piece = board[nr][nc]
                if piece == ("K" if by_color == "W" else "k"):
                    return True
    return False
