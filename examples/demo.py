#!/usr/bin/env python3
"""Interactive demo for Gardner MiniChess agents.

This script demonstrates different agent matchups with a simple CLI interface.
"""

from __future__ import annotations

import argparse
from typing import Dict

from minichess.agents import RandomAgent, GreedyAgent, MinimaxAgent, MCTSAgent
from minichess.agents.base import Agent
from minichess.game import MiniChessState, initial_state


AGENT_TYPES = {
    "random": RandomAgent,
    "greedy": GreedyAgent,
    "minimax": MinimaxAgent,
    "mcts": MCTSAgent,
}


def create_agent(agent_type: str, **kwargs) -> Agent:
    """Create an agent instance with the given parameters."""
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unknown agent type: {agent_type}")

    agent_class = AGENT_TYPES[agent_type]

    # Filter kwargs to only include relevant parameters for this agent
    if agent_type in ("random", "greedy"):
        return agent_class()
    elif agent_type == "minimax":
        minimax_kwargs = {}
        if "depth" in kwargs:
            minimax_kwargs["depth"] = kwargs["depth"]
        return agent_class(**minimax_kwargs)
    elif agent_type == "mcts":
        mcts_kwargs = {}
        if "simulations" in kwargs:
            mcts_kwargs["simulations"] = kwargs["simulations"]
        if "rollout_depth" in kwargs:
            mcts_kwargs["rollout_depth"] = kwargs["rollout_depth"]
        return agent_class(**mcts_kwargs)

    return agent_class()


def play_game(
    white_agent: Agent,
    black_agent: Agent,
    white_name: str,
    black_name: str,
    max_plies: int = 200,
    verbose: bool = True
) -> MiniChessState:
    """Play a single game and return the final state."""
    state = initial_state()
    agents = {"W": white_agent, "B": black_agent}
    ply = 0

    if verbose:
        print(f"\nStarting game: {white_name} (White) vs {black_name} (Black)")
        print("=" * 60)

    while not state.is_terminal() and ply < max_plies:
        mover = agents[state.to_move]
        move = mover.choose_move(state)
        state = state.make_move(move, validate=False)
        ply += 1

    if verbose:
        print(state.render())
        if state.is_terminal():
            result = state.result()
            outcome = "1-0" if result > 0 else "0-1" if result < 0 else "½-½"
            winner = white_name if result > 0 else black_name if result < 0 else "Draw"
            print(f"\nGame over in {ply} plies: {outcome}")
            print(f"Result: {winner}")
        else:
            print(f"\nReached ply cap ({max_plies}); treating as draw.")

    return state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play demo games with different MiniChess agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Random vs Random
  python examples/demo.py --white random --black random

  # Greedy vs Random
  python examples/demo.py --white greedy --black random

  # Greedy self-play
  python examples/demo.py --white greedy --black greedy

  # Minimax vs MCTS
  python examples/demo.py --white minimax --white-depth 3 --black mcts --black-simulations 100

  # MCTS self-play with custom parameters
  python examples/demo.py --white mcts --white-simulations 200 --black mcts --black-simulations 200

Available agents: random, greedy, minimax, mcts
        """
    )

    parser.add_argument("--white", default="greedy", choices=list(AGENT_TYPES.keys()),
                       help="Agent type for White (default: greedy)")
    parser.add_argument("--black", default="random", choices=list(AGENT_TYPES.keys()),
                       help="Agent type for Black (default: random)")
    parser.add_argument("--max-plies", type=int, default=200,
                       help="Maximum plies before declaring draw (default: 200)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress verbose output")

    # Minimax parameters
    parser.add_argument("--white-depth", type=int, default=3,
                       help="Search depth for White if using minimax (default: 3)")
    parser.add_argument("--black-depth", type=int, default=3,
                       help="Search depth for Black if using minimax (default: 3)")

    # MCTS parameters
    parser.add_argument("--white-simulations", type=int, default=100,
                       help="Number of simulations for White if using MCTS (default: 100)")
    parser.add_argument("--black-simulations", type=int, default=100,
                       help="Number of simulations for Black if using MCTS (default: 100)")
    parser.add_argument("--white-rollout-depth", type=int, default=30,
                       help="Rollout depth for White if using MCTS (default: 30)")
    parser.add_argument("--black-rollout-depth", type=int, default=30,
                       help="Rollout depth for Black if using MCTS (default: 30)")

    return parser.parse_args()


def main():
    args = parse_args()

    # Create agents with appropriate parameters
    white_kwargs = {
        "depth": args.white_depth,
        "simulations": args.white_simulations,
        "rollout_depth": args.white_rollout_depth,
    }
    black_kwargs = {
        "depth": args.black_depth,
        "simulations": args.black_simulations,
        "rollout_depth": args.black_rollout_depth,
    }

    white_agent = create_agent(args.white, **white_kwargs)
    black_agent = create_agent(args.black, **black_kwargs)

    # Create descriptive names
    white_name = args.white
    if args.white == "minimax":
        white_name = f"Minimax(depth={args.white_depth})"
    elif args.white == "mcts":
        white_name = f"MCTS(sims={args.white_simulations})"

    black_name = args.black
    if args.black == "minimax":
        black_name = f"Minimax(depth={args.black_depth})"
    elif args.black == "mcts":
        black_name = f"MCTS(sims={args.black_simulations})"

    # Play the game
    play_game(
        white_agent=white_agent,
        black_agent=black_agent,
        white_name=white_name,
        black_name=black_name,
        max_plies=args.max_plies,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
