"""Universal MiniChess match runner with pluggable agents."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from minichess.agents import GreedyAgent, MinimaxAgent, MCTSAgent, RandomAgent
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


def _mcts_factory(
    simulations: Optional[int] = None,
    time_limit: Optional[float] = None,
    exploration_c: Optional[float] = None,
    rollout_depth: Optional[int] = None,
    **_: object,
) -> Agent:
    kwargs: Dict[str, object] = {}
    if simulations is not None:
        kwargs["simulations"] = simulations
    if time_limit is not None:
        kwargs["time_limit"] = time_limit
    if exploration_c is not None:
        kwargs["exploration_c"] = exploration_c
    if rollout_depth is not None:
        kwargs["rollout_depth"] = rollout_depth
    return MCTSAgent(**kwargs) # type: ignore[arg-type]


AGENT_FACTORIES: Dict[str, Callable[..., Agent]] = {
    "random": lambda **_: RandomAgent(),
    "greedy": lambda **_: GreedyAgent(),
    "minimax": _minimax_factory,
    "mcts": _mcts_factory,
}


@dataclass
class Tally:
    agent1: str
    agent2: str
    white_wins: int = 0
    black_wins: int = 0
    draws: int = 0
    agent1_wins: int = 0
    agent2_wins: int = 0
    plies: int = 0  # total plies across games

    def record(self, result: float, white_name: str, black_name: str, plies: int) -> None:
        """Record game result. white_name/black_name are agent labels (not board positions)."""
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
            if winner == self.agent1:
                self.agent1_wins += 1
            elif winner == self.agent2:
                self.agent2_wins += 1

    def summary(self, total_games: int) -> str:
        avg_plies = self.plies / total_games if total_games else 0.0
        return (
            f"By color -> White {self.white_wins} | Draw {self.draws} | Black {self.black_wins} "
            f"(avg plies: {avg_plies:.1f})\n"
            f"By agent  -> {self.agent1} {self.agent1_wins} | Draw {self.draws} | "
            f"{self.agent2} {self.agent2_wins}"
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
    if "simulations" in cfg:
        parts.append(f"sims={cfg['simulations']}")
    if "rollout_depth" in cfg:
        parts.append(f"rollout={cfg['rollout_depth']}")
    if "exploration_c" in cfg:
        parts.append(f"c={cfg['exploration_c']}")
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
    agent1_name: str,
    agent2_name: str,
    num_games: int,
    max_plies: int,
    swap_colors: bool,
    print_every: int,
    agent1_cfg: Dict[str, object],
    agent2_cfg: Dict[str, object],
) -> Tally:
    """Run a batch of games between two agents.

    Args:
        agent1_name: Type of first agent (e.g., "minimax")
        agent2_name: Type of second agent (e.g., "mcts")
        swap_colors: If True, agents alternate playing White/Black positions
    """
    # Create unique labels that include configuration
    agent1_label = make_agent_label(agent1_name, agent1_cfg)
    agent2_label = make_agent_label(agent2_name, agent2_cfg)
    tally = Tally(agent1=agent1_label, agent2=agent2_label)
    agent_cache: Dict[Tuple[str, Tuple[Tuple[str, object], ...]], Agent] = {}

    def cached(name: str, cfg: Dict[str, object]) -> Agent:
        key = (name.lower(), tuple(sorted(cfg.items())))
        if key not in agent_cache:
            agent_cache[key] = make_agent(name, **cfg)
        return agent_cache[key]

    for game_idx in range(num_games):
        # Determine which agent plays which board position (W/B) for this game
        if swap_colors and game_idx % 2 == 1:
            # Swap: agent2 plays White, agent1 plays Black
            w_name, b_name = agent2_name, agent1_name
            w_cfg, b_cfg = agent2_cfg, agent1_cfg
            w_label, b_label = agent2_label, agent1_label
        else:
            # Normal: agent1 plays White, agent2 plays Black
            w_name, b_name = agent1_name, agent2_name
            w_cfg, b_cfg = agent1_cfg, agent2_cfg
            w_label, b_label = agent1_label, agent2_label

        result, plies, _ = play_game(cached(w_name, w_cfg), cached(b_name, b_cfg), max_plies)
        tally.record(result, w_label, b_label, plies)

        if print_every and (game_idx + 1) % print_every == 0:
            print(f"After {game_idx + 1} games:")
            print(tally.summary(game_idx + 1))
            print("-" * 40)

    return tally


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batches of MiniChess games between agents.")
    parser.add_argument("--agent1", default="greedy", help="First agent type (default: greedy).")
    parser.add_argument("--agent2", default="random", help="Second agent type (default: random).")
    parser.add_argument("--games", type=int, default=100, help="Number of games to run.")
    parser.add_argument("--max-plies", type=int, default=200, help="Ply cap per game before declaring draw-ish.")
    parser.add_argument(
        "--swap-colors",
        action="store_true",
        help="Alternate which agent plays White/Black each game (reduces bias).",
    )
    parser.add_argument("--seed", type=int, help="Optional RNG seed for reproducibility.")
    parser.add_argument(
        "--print-every",
        type=int,
        default=0,
        help="If >0, print running summary every N games.",
    )
    parser.add_argument(
        "--agent1-depth",
        type=int,
        help="Search depth for agent1 if using minimax.",
    )
    parser.add_argument(
        "--agent2-depth",
        type=int,
        help="Search depth for agent2 if using minimax.",
    )
    parser.add_argument(
        "--agent1-simulations",
        type=int,
        help="Number of simulations for agent1 if using MCTS.",
    )
    parser.add_argument(
        "--agent2-simulations",
        type=int,
        help="Number of simulations for agent2 if using MCTS.",
    )
    parser.add_argument(
        "--agent1-rollout-depth",
        type=int,
        help="Rollout depth for agent1 if using MCTS.",
    )
    parser.add_argument(
        "--agent2-rollout-depth",
        type=int,
        help="Rollout depth for agent2 if using MCTS.",
    )
    parser.add_argument(
        "--agent1-exploration-c",
        type=float,
        help="Exploration constant (UCT c) for agent1 if using MCTS.",
    )
    parser.add_argument(
        "--agent2-exploration-c",
        type=float,
        help="Exploration constant (UCT c) for agent2 if using MCTS.",
    )
    parser.add_argument(
        "--agent1-time-limit",
        type=float,
        help="Per-move time limit (seconds) for agent1 if using minimax or mcts.",
    )
    parser.add_argument(
        "--agent2-time-limit",
        type=float,
        help="Per-move time limit (seconds) for agent2 if using minimax or mcts.",
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

    agent1_cfg: Dict[str, object] = {}
    agent2_cfg: Dict[str, object] = {}
    if args.agent1_depth is not None:
        agent1_cfg["depth"] = args.agent1_depth
    if args.agent2_depth is not None:
        agent2_cfg["depth"] = args.agent2_depth
    if args.agent1_simulations is not None:
        agent1_cfg["simulations"] = args.agent1_simulations
    if args.agent2_simulations is not None:
        agent2_cfg["simulations"] = args.agent2_simulations
    if args.agent1_rollout_depth is not None:
        agent1_cfg["rollout_depth"] = args.agent1_rollout_depth
    if args.agent2_rollout_depth is not None:
        agent2_cfg["rollout_depth"] = args.agent2_rollout_depth
    if args.agent1_exploration_c is not None:
        agent1_cfg["exploration_c"] = args.agent1_exploration_c
    if args.agent2_exploration_c is not None:
        agent2_cfg["exploration_c"] = args.agent2_exploration_c
    if args.agent1_time_limit is not None:
        agent1_cfg["time_limit"] = args.agent1_time_limit
    if args.agent2_time_limit is not None:
        agent2_cfg["time_limit"] = args.agent2_time_limit

    tally = run_batch(
        agent1_name=args.agent1,
        agent2_name=args.agent2,
        num_games=args.games,
        max_plies=args.max_plies,
        swap_colors=args.swap_colors,
        print_every=args.print_every,
        agent1_cfg=agent1_cfg,
        agent2_cfg=agent2_cfg,
    )

    print(f"Ran {args.games} games: agent1={args.agent1}, agent2={args.agent2}, swap_colors={args.swap_colors}")
    print(tally.summary(args.games))


if __name__ == "__main__":
    main()
