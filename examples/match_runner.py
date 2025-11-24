"""Universal MiniChess match runner with pluggable agents."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Callable, Dict

from minichess.agents import GreedyAgent, RandomAgent
from minichess.agents.base import Agent
from minichess.game import MiniChessState, initial_state


# Register available agents here as we add new ones
AGENT_FACTORIES: Dict[str, Callable[[], Agent]] = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
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


def make_agent(name: str) -> Agent:
    key = name.lower()
    if key not in AGENT_FACTORIES:
        raise ValueError(f"Unknown agent '{name}'. Available: {', '.join(sorted(AGENT_FACTORIES))}")
    return AGENT_FACTORIES[key]()


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


def run_batch(white_name: str, black_name: str, num_games: int, max_plies: int, swap_colors: bool, print_every: int) -> Tally:
    tally = Tally(agent_a=white_name, agent_b=black_name)
    agent_cache: Dict[str, Agent] = {}

    def cached(name: str) -> Agent:
        if name not in agent_cache:
            agent_cache[name] = make_agent(name)
        return agent_cache[name]

    for game_idx in range(num_games):
        if swap_colors and game_idx % 2 == 1:
            w_name, b_name = black_name, white_name
        else:
            w_name, b_name = white_name, black_name

        result, plies, _ = play_game(cached(w_name), cached(b_name), max_plies)
        tally.record(result, w_name, b_name, plies)

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

    tally = run_batch(
        white_name=args.white,
        black_name=args.black,
        num_games=args.games,
        max_plies=args.max_plies,
        swap_colors=args.swap_colors,
        print_every=args.print_every,
    )

    print(f"Ran {args.games} games: White={args.white}, Black={args.black}, swap_colors={args.swap_colors}")
    print(tally.summary(args.games))


if __name__ == "__main__":
    main()
