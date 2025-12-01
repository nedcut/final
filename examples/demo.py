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
    agent1: Agent,
    agent2: Agent,
    agent1_name: str,
    agent2_name: str,
    max_plies: int = 200,
    verbose: bool = True
) -> MiniChessState:
    """Play a single game and return the final state.

    Note: agent1 plays White position, agent2 plays Black position.
    """
    state = initial_state()
    agents = {"W": agent1, "B": agent2}  # agent1 plays W, agent2 plays B
    ply = 0

    if verbose:
        print(f"\nStarting game: {agent1_name} (playing White) vs {agent2_name} (playing Black)")
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
            # result > 0 means W wins (agent1), result < 0 means B wins (agent2)
            winner = agent1_name if result > 0 else agent2_name if result < 0 else "Draw"
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
  python examples/demo.py --agent1 random --agent2 random

  # Greedy vs Random
  python examples/demo.py --agent1 greedy --agent2 random

  # Greedy self-play
  python examples/demo.py --agent1 greedy --agent2 greedy

  # Minimax vs MCTS
  python examples/demo.py --agent1 minimax --agent1-depth 3 --agent2 mcts --agent2-simulations 100

  # MCTS self-play with custom parameters
  python examples/demo.py --agent1 mcts --agent1-simulations 200 --agent2 mcts --agent2-simulations 200

Available agents: random, greedy, minimax, mcts
Note: agent1 plays the White position, agent2 plays the Black position
        """
    )

    parser.add_argument("--agent1", default="greedy", choices=list(AGENT_TYPES.keys()),
                       help="First agent type (plays White position, default: greedy)")
    parser.add_argument("--agent2", default="random", choices=list(AGENT_TYPES.keys()),
                       help="Second agent type (plays Black position, default: random)")
    parser.add_argument("--max-plies", type=int, default=200,
                       help="Maximum plies before declaring draw (default: 200)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress verbose output")

    # Minimax parameters
    parser.add_argument("--agent1-depth", type=int, default=3,
                       help="Search depth for agent1 if using minimax (default: 3)")
    parser.add_argument("--agent2-depth", type=int, default=3,
                       help="Search depth for agent2 if using minimax (default: 3)")

    # MCTS parameters
    parser.add_argument("--agent1-simulations", type=int, default=100,
                       help="Number of simulations for agent1 if using MCTS (default: 100)")
    parser.add_argument("--agent2-simulations", type=int, default=100,
                       help="Number of simulations for agent2 if using MCTS (default: 100)")
    parser.add_argument("--agent1-rollout-depth", type=int, default=30,
                       help="Rollout depth for agent1 if using MCTS (default: 30)")
    parser.add_argument("--agent2-rollout-depth", type=int, default=30,
                       help="Rollout depth for agent2 if using MCTS (default: 30)")

    return parser.parse_args()


def main():
    args = parse_args()

    # Create agents with appropriate parameters
    agent1_kwargs = {
        "depth": args.agent1_depth,
        "simulations": args.agent1_simulations,
        "rollout_depth": args.agent1_rollout_depth,
    }
    agent2_kwargs = {
        "depth": args.agent2_depth,
        "simulations": args.agent2_simulations,
        "rollout_depth": args.agent2_rollout_depth,
    }

    agent1 = create_agent(args.agent1, **agent1_kwargs)
    agent2 = create_agent(args.agent2, **agent2_kwargs)

    # Create descriptive names
    agent1_name = args.agent1
    if args.agent1 == "minimax":
        agent1_name = f"Minimax(depth={args.agent1_depth})"
    elif args.agent1 == "mcts":
        agent1_name = f"MCTS(sims={args.agent1_simulations})"

    agent2_name = args.agent2
    if args.agent2 == "minimax":
        agent2_name = f"Minimax(depth={args.agent2_depth})"
    elif args.agent2 == "mcts":
        agent2_name = f"MCTS(sims={args.agent2_simulations})"

    # Play the game
    play_game(
        agent1=agent1,
        agent2=agent2,
        agent1_name=agent1_name,
        agent2_name=agent2_name,
        max_plies=args.max_plies,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()
