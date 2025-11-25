"""Universal MiniChess match runner with pluggable agents."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from minichess.agents import GreedyAgent, MinimaxAgent, RandomAgent
from minichess.agents.base import Agent
from minichess.game import MiniChessState, initial_state


# Register available agents here as we add new ones
def _minimax_factory(depth: Optional[int] = None, time_limit: Optional[float] = None, **_: object) -> Agent:
    kwargs: Dict[str, object] = {}
    if depth is not None:
        kwargs["depth"] = depth
    if time_limit is not None:
        kwargs["time_limit"] = time_limit
    return MinimaxAgent(**kwargs) # type: ignore[arg-type]


AGENT_FACTORIES: Dict[str, Callable[..., Agent]] = {
    "random": lambda **_: RandomAgent(),
    "greedy": lambda **_: GreedyAgent(),
    "minimax": _minimax_factory,
}


@dataclass
class Tally:
    agent_a: str
    agent_b: str
    white_wins: int = 0
    black_wins: int = 0
    draws: int = 0
    agent_a_wins: int = 0
    agent_b_wins: int = 0
    plies: int = 0  # total plies across games

    def record(self, result: float, white_name: str, black_name: str, plies: int) -> None:
        self.plies += plies
        if result > 0:
            self.white_wins += 1
            winner = white_name
        elif result < 0:
            self.black_wins += 1
            winner = black_name
        else:
            self.draws += 1
            winner = None

        if winner is not None:
            if winner == self.agent_a:
                self.agent_a_wins += 1
            elif winner == self.agent_b:
                self.agent_b_wins += 1

    def summary(self, total_games: int) -> str:
        avg_plies = self.plies / total_games if total_games else 0.0
        return (
            f"By color -> White {self.white_wins} | Draw {self.draws} | Black {self.black_wins} "
            f"(avg plies: {avg_plies:.1f})\n"
            f"By agent  -> {self.agent_a} {self.agent_a_wins} | Draw {self.draws} | "
            f"{self.agent_b} {self.agent_b_wins}"
        )


def make_agent(name: str, **kwargs: object) -> Agent:
    key = name.lower()
    if key not in AGENT_FACTORIES:
        raise ValueError(f"Unknown agent '{name}'. Available: {', '.join(sorted(AGENT_FACTORIES))}")
    return AGENT_FACTORIES[key](**kwargs)


def make_agent_label(name: str, cfg: Dict[str, object]) -> str:
    """Create a unique label for an agent including its configuration."""
    if not cfg:
        return name

    parts = [name]
    if "depth" in cfg:
        parts.append(f"depth={cfg['depth']}")
    if "time_limit" in cfg:
        parts.append(f"time={cfg['time_limit']}s")

    return f"{parts[0]}({', '.join(parts[1:])})" if len(parts) > 1 else parts[0]


def play_game(white: Agent, black: Agent, max_plies: int) -> tuple[float, int, MiniChessState]:
    """Return (result, plies, final_state); result is +1 white win, -1 black win, 0 draw."""
    state: MiniChessState = initial_state()
    ply = 0
    while not state.is_terminal() and ply < max_plies:
        mover = white if state.to_move == "W" else black
        move = mover.choose_move(state)
        state = state.make_move(move, validate=False)  # move came from legal_moves()
        ply += 1
    if state.is_terminal():
        return state.result(), ply, state
    return 0.0, ply, state  # treat ply-cap as draw-ish


def run_batch(
    white_name: str,
    black_name: str,
    num_games: int,
    max_plies: int,
    swap_colors: bool,
    print_every: int,
    white_cfg: Dict[str, object],
    black_cfg: Dict[str, object],
) -> Tally:
    # Create unique labels that include configuration
    white_label = make_agent_label(white_name, white_cfg)
    black_label = make_agent_label(black_name, black_cfg)
    tally = Tally(agent_a=white_label, agent_b=black_label)
    agent_cache: Dict[Tuple[str, Tuple[Tuple[str, object], ...]], Agent] = {}

    def cached(name: str, cfg: Dict[str, object]) -> Agent:
        key = (name.lower(), tuple(sorted(cfg.items())))
        if key not in agent_cache:
            agent_cache[key] = make_agent(name, **cfg)
        return agent_cache[key]

    for game_idx in range(num_games):
        if swap_colors and game_idx % 2 == 1:
            w_name, b_name = black_name, white_name
            w_cfg, b_cfg = black_cfg, white_cfg
            w_label, b_label = black_label, white_label
        else:
            w_name, b_name = white_name, black_name
            w_cfg, b_cfg = white_cfg, black_cfg
            w_label, b_label = white_label, black_label

        result, plies, _ = play_game(cached(w_name, w_cfg), cached(b_name, b_cfg), max_plies)
        tally.record(result, w_label, b_label, plies)

        if print_every and (game_idx + 1) % print_every == 0:
            print(f"After {game_idx + 1} games:")
            print(tally.summary(game_idx + 1))
            print("-" * 40)

    return tally


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batches of MiniChess games between agents.")
    parser.add_argument("--white", default="greedy", help="Agent playing White (default: greedy).")
    parser.add_argument("--black", default="random", help="Agent playing Black (default: random).")
    parser.add_argument("--games", type=int, default=100, help="Number of games to run.")
    parser.add_argument("--max-plies", type=int, default=200, help="Ply cap per game before declaring draw-ish.")
    parser.add_argument(
        "--swap-colors",
        action="store_true",
        help="Alternate colors every game to reduce starting-side bias.",
    )
    parser.add_argument("--seed", type=int, help="Optional RNG seed for reproducibility.")
    parser.add_argument(
        "--print-every",
        type=int,
        default=0,
        help="If >0, print running summary every N games.",
    )
    parser.add_argument(
        "--white-depth",
        type=int,
        help="Search depth for White if using minimax.",
    )
    parser.add_argument(
        "--black-depth",
        type=int,
        help="Search depth for Black if using minimax.",
    )
    parser.add_argument(
        "--white-time-limit",
        type=float,
        help="Per-move time limit (seconds) for White if using minimax.",
    )
    parser.add_argument(
        "--black-time-limit",
        type=float,
        help="Per-move time limit (seconds) for Black if using minimax.",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List available agent names and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_agents:
        print("Available agents:", ", ".join(sorted(AGENT_FACTORIES)))
        return

    if args.seed is not None:
        random.seed(args.seed)

    white_cfg: Dict[str, object] = {}
    black_cfg: Dict[str, object] = {}
    if args.white_depth is not None:
        white_cfg["depth"] = args.white_depth
    if args.black_depth is not None:
        black_cfg["depth"] = args.black_depth
    if args.white_time_limit is not None:
        white_cfg["time_limit"] = args.white_time_limit
    if args.black_time_limit is not None:
        black_cfg["time_limit"] = args.black_time_limit

    tally = run_batch(
        white_name=args.white,
        black_name=args.black,
        num_games=args.games,
        max_plies=args.max_plies,
        swap_colors=args.swap_colors,
        print_every=args.print_every,
        white_cfg=white_cfg,
        black_cfg=black_cfg,
    )

    print(f"Ran {args.games} games: White={args.white}, Black={args.black}, swap_colors={args.swap_colors}")
    print(tally.summary(args.games))


if __name__ == "__main__":
    main()
