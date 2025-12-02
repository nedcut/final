#!/usr/bin/env python3
"""Comprehensive experimental evaluation framework for MiniChess agents.

This script runs systematic experiments comparing MCTS and Minimax agents under
various configurations to answer the research question:

    "How do depth-limited minimax with alpha-beta pruning and Monte Carlo Tree
    Search compare in playing strength and computational efficiency on Gardner
    MiniChess, under equal computational budgets?"

Results are saved to CSV files for analysis.
"""
import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment."""
    experiment_id: str
    experiment_type: str  # "head_to_head", "baseline", "degradation", "custom"
    agent1_type: str  # Agent type (e.g., "mcts", "minimax")
    agent1_config: Dict[str, Any]  # Agent configuration
    agent2_type: str
    agent2_config: Dict[str, Any]
    num_games: int
    swap_colors: bool
    seed: int
    description: str


@dataclass
class ExperimentResult:
    """Results from a single experiment."""
    config: ExperimentConfig
    board_white_wins: int  # Wins from White board position
    draws: int
    board_black_wins: int  # Wins from Black board position
    avg_plies: float
    total_time: float
    agent1_wins: int  # Wins by agent1 (regardless of color)
    agent2_wins: int  # Wins by agent2 (regardless of color)


def create_experiment_matrix(
    custom_mcts: Optional[List[int]] = None,
    custom_minimax: Optional[List[int]] = None,
    custom_games: int = 50
) -> List[ExperimentConfig]:
    """Create comprehensive experiment matrix.

    Args:
        custom_mcts: Optional list of MCTS simulation counts for custom experiments
        custom_minimax: Optional list of Minimax depths for custom experiments
        custom_games: Number of games per custom experiment (default: 50)
    """
    experiments = []
    exp_id = 1

    # =========================================================================
    # 0. CUSTOM EXPERIMENTS (if specified)
    # =========================================================================
    if custom_mcts or custom_minimax:
        print("Designing custom experiments...")
        mcts_configs = custom_mcts or []
        minimax_configs = custom_minimax or []

        # If only one side specified, use defaults for the other
        if not mcts_configs:
            mcts_configs = [100]  # Default MCTS
        if not minimax_configs:
            minimax_configs = [3]  # Default Minimax

        for mcts_sims in mcts_configs:
            for mm_depth in minimax_configs:
                experiments.append(ExperimentConfig(
                    experiment_id=f"CUSTOM{exp_id:03d}",
                    experiment_type="custom",
                    agent1_type="mcts",
                    agent1_config={"simulations": mcts_sims},
                    agent2_type="minimax",
                    agent2_config={"depth": mm_depth},
                    num_games=custom_games,
                    swap_colors=True,
                    seed=exp_id * 1000,
                    description=f"Custom: MCTS({mcts_sims}) vs Minimax({mm_depth})"
                ))
                exp_id += 1

        # Return early - custom flags mean "run only custom experiments"
        return experiments

    # =========================================================================
    # 1. TIME-MATCHED HEAD-TO-HEAD EXPERIMENTS
    # =========================================================================
    print("Designing time-matched head-to-head experiments...")

    time_matched_configs = [
        # ~0.5s per move budget
        ("mcts", {"simulations": 50}, "minimax", {"depth": 3}, "Time-matched: ~0.5s budget"),
        # ~1.0s per move budget
        ("mcts", {"simulations": 100}, "minimax", {"depth": 4}, "Time-matched: ~1.0s budget"),
        # ~2.0s per move budget
        ("mcts", {"simulations": 200}, "minimax", {"depth": 4}, "Time-matched: ~2.0s budget"),
    ]

    for a1_type, a1_cfg, a2_type, a2_cfg, desc in time_matched_configs:
        experiments.append(ExperimentConfig(
            experiment_id=f"TM{exp_id:03d}",
            experiment_type="time_matched",
            agent1_type=a1_type,
            agent1_config=a1_cfg,
            agent2_type=a2_type,
            agent2_config=a2_cfg,
            num_games=100,
            swap_colors=True,
            seed=exp_id * 1000,
            description=desc
        ))
        exp_id += 1

    # =========================================================================
    # 2. RESOURCE DEGRADATION EXPERIMENTS
    # =========================================================================
    print("Designing resource degradation experiments...")

    # Minimax degradation (vs Greedy baseline)
    for depth in [5, 4, 3, 2]:
        experiments.append(ExperimentConfig(
            experiment_id=f"DEG{exp_id:03d}",
            experiment_type="degradation",
            agent1_type="minimax",
            agent1_config={"depth": depth},
            agent2_type="greedy",
            agent2_config={},
            num_games=50,
            swap_colors=True,
            seed=exp_id * 1000,
            description=f"Minimax degradation: depth={depth} vs Greedy"
        ))
        exp_id += 1

    # MCTS degradation (vs Greedy baseline)
    for sims in [500, 300, 200, 150, 100, 50]:
        experiments.append(ExperimentConfig(
            experiment_id=f"DEG{exp_id:03d}",
            experiment_type="degradation",
            agent1_type="mcts",
            agent1_config={"simulations": sims},
            agent2_type="greedy",
            agent2_config={},
            num_games=50,
            swap_colors=True,
            seed=exp_id * 1000,
            description=f"MCTS degradation: sims={sims} vs Greedy"
        ))
        exp_id += 1

    # =========================================================================
    # 3. BASELINE COMPARISONS
    # =========================================================================
    print("Designing baseline comparison experiments...")

    # Strong configs vs Random
    baseline_configs = [
        ("minimax", {"depth": 3}, "Minimax(3) vs Random"),
        ("minimax", {"depth": 4}, "Minimax(4) vs Random"),
        ("mcts", {"simulations": 100}, "MCTS(100) vs Random"),
        ("mcts", {"simulations": 200}, "MCTS(200) vs Random"),
    ]

    for agent, config, desc in baseline_configs:
        experiments.append(ExperimentConfig(
            experiment_id=f"BASE{exp_id:03d}",
            experiment_type="baseline",
            agent1_type=agent,
            agent1_config=config,
            agent2_type="random",
            agent2_config={},
            num_games=30,
            swap_colors=True,
            seed=exp_id * 1000,
            description=desc
        ))
        exp_id += 1

    # =========================================================================
    # 4. HEAD-TO-HEAD MATRIX (comprehensive)
    # =========================================================================
    print("Designing comprehensive head-to-head matrix...")

    mcts_configs = [
        ("mcts", {"simulations": 50}, "MCTS(50)"),
        ("mcts", {"simulations": 100}, "MCTS(100)"),
        ("mcts", {"simulations": 150}, "MCTS(150)"),
        ("mcts", {"simulations": 200}, "MCTS(200)"),
    ]

    minimax_configs = [
        ("minimax", {"depth": 2}, "Minimax(2)"),
        ("minimax", {"depth": 3}, "Minimax(3)"),
        ("minimax", {"depth": 4}, "Minimax(4)"),
    ]

    for mcts_agent, mcts_cfg, mcts_name in mcts_configs:
        for mm_agent, mm_cfg, mm_name in minimax_configs:
            experiments.append(ExperimentConfig(
                experiment_id=f"H2H{exp_id:03d}",
                experiment_type="head_to_head",
                agent1_type=mcts_agent,
                agent1_config=mcts_cfg,
                agent2_type=mm_agent,
                agent2_config=mm_cfg,
                num_games=50,
                swap_colors=True,
                seed=exp_id * 1000,
                description=f"{mcts_name} vs {mm_name}"
            ))
            exp_id += 1

    print(f"Created {len(experiments)} experiments total")
    return experiments


def build_match_runner_command(config: ExperimentConfig, pythonpath: str) -> List[str]:
    """Build command to run match_runner.py with given config."""
    cmd = [
        sys.executable, "examples/match_runner.py",
        "--agent1", config.agent1_type,
        "--agent2", config.agent2_type,
        "--games", str(config.num_games),
        "--seed", str(config.seed),
    ]

    if config.swap_colors:
        cmd.append("--swap-colors")

    # Add agent1 config
    for key, value in config.agent1_config.items():
        if config.agent1_type == "minimax" and key == "depth":
            cmd.extend(["--agent1-depth", str(value)])
        elif config.agent1_type == "mcts" and key == "simulations":
            cmd.extend(["--agent1-simulations", str(value)])

    # Add agent2 config
    for key, value in config.agent2_config.items():
        if config.agent2_type == "minimax" and key == "depth":
            cmd.extend(["--agent2-depth", str(value)])
        elif config.agent2_type == "mcts" and key == "simulations":
            cmd.extend(["--agent2-simulations", str(value)])

    return cmd


def parse_match_output(output: str) -> tuple[int, int, int, float, int, int]:
    """Parse match_runner.py output to extract results.

    Returns: (white_wins, draws, black_wins, avg_plies, agent1_wins, agent2_wins)
    """
    lines = output.strip().split('\n')

    # Find "By color" line
    color_line = [l for l in lines if "By color ->" in l][0]
    # Parse: "By color -> White X | Draw Y | Black Z (avg plies: W.W)"
    parts = color_line.split("->")[1].strip()
    color_parts = parts.split("|")

    white_wins = int(color_parts[0].split()[1])
    draws = int(color_parts[1].split()[1])
    black_wins = int(color_parts[2].split()[1])

    avg_plies_str = parts.split("(avg plies:")[1].strip().rstrip(")")
    avg_plies = float(avg_plies_str)

    # Find "By agent" line
    agent_line = [l for l in lines if "By agent  ->" in l][0]
    # Parse: "By agent  -> agent1 X | Draw Y | agent2 Z"
    agent_parts = agent_line.split("->")[1].strip().split("|")

    agent1_wins = int(agent_parts[0].split()[1])
    agent2_wins = int(agent_parts[2].split()[1])

    return white_wins, draws, black_wins, avg_plies, agent1_wins, agent2_wins


def run_experiment(config: ExperimentConfig, pythonpath: str) -> ExperimentResult:
    """Run a single experiment and return results."""
    print(f"\n{'='*80}")
    print(f"Running: {config.experiment_id} - {config.description}")
    print(f"{'='*80}")

    cmd = build_match_runner_command(config, pythonpath)

    # Set environment
    env = {"PYTHONPATH": pythonpath}

    # Run experiment
    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path(pythonpath).parent)
    )
    elapsed_time = time.time() - start_time

    if result.returncode != 0:
        print(f"ERROR: Experiment failed!")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Experiment {config.experiment_id} failed")

    # Parse results
    board_white_wins, draws, board_black_wins, avg_plies, agent1_wins, agent2_wins = \
        parse_match_output(result.stdout)

    print(f"Results: {config.agent1_type} {agent1_wins} - {draws} - {agent2_wins} {config.agent2_type}")
    print(f"Time: {elapsed_time:.1f}s")

    return ExperimentResult(
        config=config,
        board_white_wins=board_white_wins,
        draws=draws,
        board_black_wins=board_black_wins,
        avg_plies=avg_plies,
        total_time=elapsed_time,
        agent1_wins=agent1_wins,
        agent2_wins=agent2_wins
    )


def save_results(results: List[ExperimentResult], output_dir: Path):
    """Save experiment results to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed CSV
    csv_path = output_dir / "experiment_results.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'experiment_id', 'experiment_type', 'description',
            'agent1_type', 'agent1_config', 'agent2_type', 'agent2_config',
            'num_games', 'swap_colors',
            'board_white_wins', 'draws', 'board_black_wins',
            'agent1_wins', 'agent2_wins',
            'avg_plies', 'total_time_sec'
        ])

        for result in results:
            writer.writerow([
                result.config.experiment_id,
                result.config.experiment_type,
                result.config.description,
                result.config.agent1_type,
                json.dumps(result.config.agent1_config),
                result.config.agent2_type,
                json.dumps(result.config.agent2_config),
                result.config.num_games,
                result.config.swap_colors,
                result.board_white_wins,
                result.draws,
                result.board_black_wins,
                result.agent1_wins,
                result.agent2_wins,
                result.avg_plies,
                result.total_time
            ])

    print(f"\nResults saved to {csv_path}")

    # Save JSON for programmatic access
    json_path = output_dir / "experiment_results.json"
    json_data = [
        {
            'config': asdict(r.config),
            'results': {
                'board_white_wins': r.board_white_wins,
                'draws': r.draws,
                'board_black_wins': r.board_black_wins,
                'agent1_wins': r.agent1_wins,
                'agent2_wins': r.agent2_wins,
                'avg_plies': r.avg_plies,
                'total_time': r.total_time
            }
        }
        for r in results
    ]

    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"Results saved to {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all standard experiments
  python experiments/run_experiments.py --yes

  # Run only time-matched experiments
  python experiments/run_experiments.py --experiment-types time_matched

  # Run custom high-MCTS experiments
  python experiments/run_experiments.py --custom-mcts 300,500,1000 --custom-minimax 2,3,4

  # Run ultra-high MCTS vs Minimax(3)
  python experiments/run_experiments.py --custom-mcts 2000,3000,5000 --custom-minimax 3

  # Run custom experiments with more games
  python experiments/run_experiments.py --custom-mcts 1000 --custom-minimax 3,4 --custom-games 100

  # Run a quick sanity check with at most 10 games per experiment
  python experiments/run_experiments.py --quick --yes
        """
    )
    parser.add_argument("--pythonpath", default="/Users/nedcutler/Documents/Middlebury/CS311/final/src",
                       help="PYTHONPATH for imports")
    parser.add_argument("--output-dir", default="experiments/results",
                       help="Output directory for results")
    parser.add_argument("--experiment-types", nargs='+',
                       choices=['time_matched', 'degradation', 'baseline', 'head_to_head', 'all', 'custom'],
                       default=['all'],
                       help="Which experiment types to run")
    parser.add_argument("--custom-mcts", type=str,
                       help="Comma-separated MCTS simulation counts for custom experiments (e.g., '300,500,1000')")
    parser.add_argument("--custom-minimax", type=str,
                       help="Comma-separated Minimax depths for custom experiments (e.g., '2,3,4')")
    parser.add_argument("--custom-games", type=int, default=50,
                       help="Number of games per custom experiment (default: 50)")
    parser.add_argument("--max-games", type=int,
                       help="Cap the number of games per experiment (useful for quick tests)")
    parser.add_argument("--quick", action="store_true",
                       help="Enable quick mode (limits each experiment to at most 10 games)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print experiments without running them")
    parser.add_argument("--yes", "-y", action="store_true",
                       help="Skip confirmation prompt")

    args = parser.parse_args()

    # Parse custom configurations
    custom_mcts = None
    custom_minimax = None
    if args.custom_mcts:
        custom_mcts = [int(x.strip()) for x in args.custom_mcts.split(',')]
    if args.custom_minimax:
        custom_minimax = [int(x.strip()) for x in args.custom_minimax.split(',')]

    # If custom configs specified, override experiment types
    if custom_mcts or custom_minimax:
        if 'all' in args.experiment_types or args.experiment_types == ['all']:
            args.experiment_types = ['custom']
        elif 'custom' not in args.experiment_types:
            args.experiment_types.append('custom')

    # Create experiments
    all_experiments = create_experiment_matrix(
        custom_mcts=custom_mcts,
        custom_minimax=custom_minimax,
        custom_games=args.custom_games
    )

    # Apply quick/maximum game caps
    game_cap = args.max_games
    if args.quick:
        game_cap = game_cap or 10

    if game_cap:
        print(f"Applying game cap: max {game_cap} games per experiment")
        for exp in all_experiments:
            if exp.num_games > game_cap:
                exp.num_games = game_cap

    # Filter by type
    if 'all' not in args.experiment_types:
        all_experiments = [
            e for e in all_experiments
            if e.experiment_type in args.experiment_types
        ]

    print(f"\n{'='*80}")
    print(f"EXPERIMENT PLAN: {len(all_experiments)} experiments")
    print(f"{'='*80}")

    for exp in all_experiments:
        print(f"{exp.experiment_id}: {exp.description}")

    if args.dry_run:
        print("\nDry run complete - no experiments executed")
        return

    # Confirm
    total_games = sum(e.num_games for e in all_experiments)
    print(f"\nTotal games to run: {total_games}")
    print(f"Estimated time: {total_games * 0.5 / 60:.1f} - {total_games * 2 / 60:.1f} minutes")

    if not args.yes:
        response = input("\nProceed with experiments? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            return
    else:
        print("\nAuto-confirmed with --yes flag, proceeding...")

    # Run experiments
    results = []
    output_dir = Path(args.output_dir)

    for i, exp in enumerate(all_experiments, 1):
        print(f"\n\nProgress: {i}/{len(all_experiments)}")
        try:
            result = run_experiment(exp, args.pythonpath)
            results.append(result)

            # Save intermediate results
            save_results(results, output_dir)

        except Exception as e:
            print(f"ERROR in experiment {exp.experiment_id}: {e}")
            print("Continuing with next experiment...")
            continue

    print(f"\n{'='*80}")
    print(f"EXPERIMENTS COMPLETE")
    print(f"{'='*80}")
    print(f"Completed: {len(results)}/{len(all_experiments)} experiments")
    print(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    main()
