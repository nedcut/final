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
    experiment_type: str  # "head_to_head", "baseline", "degradation"
    white_agent: str
    white_config: Dict[str, Any]
    black_agent: str
    black_config: Dict[str, Any]
    num_games: int
    swap_colors: bool
    seed: int
    description: str


@dataclass
class ExperimentResult:
    """Results from a single experiment."""
    config: ExperimentConfig
    white_wins: int
    draws: int
    black_wins: int
    avg_plies: float
    total_time: float
    white_agent_wins: int  # After color swapping
    black_agent_wins: int  # After color swapping


def create_experiment_matrix() -> List[ExperimentConfig]:
    """Create comprehensive experiment matrix."""
    experiments = []
    exp_id = 1

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

    for white, w_cfg, black, b_cfg, desc in time_matched_configs:
        experiments.append(ExperimentConfig(
            experiment_id=f"TM{exp_id:03d}",
            experiment_type="time_matched",
            white_agent=white,
            white_config=w_cfg,
            black_agent=black,
            black_config=b_cfg,
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
            white_agent="minimax",
            white_config={"depth": depth},
            black_agent="greedy",
            black_config={},
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
            white_agent="mcts",
            white_config={"simulations": sims},
            black_agent="greedy",
            black_config={},
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
            white_agent=agent,
            white_config=config,
            black_agent="random",
            black_config={},
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
                white_agent=mcts_agent,
                white_config=mcts_cfg,
                black_agent=mm_agent,
                black_config=mm_cfg,
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
        "--white", config.white_agent,
        "--black", config.black_agent,
        "--games", str(config.num_games),
        "--seed", str(config.seed),
    ]

    if config.swap_colors:
        cmd.append("--swap-colors")

    # Add white agent config
    for key, value in config.white_config.items():
        if config.white_agent == "minimax" and key == "depth":
            cmd.extend([f"--white-depth", str(value)])
        elif config.white_agent == "mcts" and key == "simulations":
            cmd.extend([f"--white-simulations", str(value)])

    # Add black agent config
    for key, value in config.black_config.items():
        if config.black_agent == "minimax" and key == "depth":
            cmd.extend([f"--black-depth", str(value)])
        elif config.black_agent == "mcts" and key == "simulations":
            cmd.extend([f"--black-simulations", str(value)])

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
    white_wins, draws, black_wins, avg_plies, agent1_wins, agent2_wins = \
        parse_match_output(result.stdout)

    print(f"Results: {config.white_agent} {agent1_wins} - {draws} - {agent2_wins} {config.black_agent}")
    print(f"Time: {elapsed_time:.1f}s")

    return ExperimentResult(
        config=config,
        white_wins=white_wins,
        draws=draws,
        black_wins=black_wins,
        avg_plies=avg_plies,
        total_time=elapsed_time,
        white_agent_wins=agent1_wins,
        black_agent_wins=agent2_wins
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
            'white_agent', 'white_config', 'black_agent', 'black_config',
            'num_games', 'swap_colors',
            'white_wins', 'draws', 'black_wins',
            'white_agent_wins', 'black_agent_wins',
            'avg_plies', 'total_time_sec'
        ])

        for result in results:
            writer.writerow([
                result.config.experiment_id,
                result.config.experiment_type,
                result.config.description,
                result.config.white_agent,
                json.dumps(result.config.white_config),
                result.config.black_agent,
                json.dumps(result.config.black_config),
                result.config.num_games,
                result.config.swap_colors,
                result.white_wins,
                result.draws,
                result.black_wins,
                result.white_agent_wins,
                result.black_agent_wins,
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
                'white_wins': r.white_wins,
                'draws': r.draws,
                'black_wins': r.black_wins,
                'white_agent_wins': r.white_agent_wins,
                'black_agent_wins': r.black_agent_wins,
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
    parser = argparse.ArgumentParser(description="Run comprehensive experiments")
    parser.add_argument("--pythonpath", default="/Users/nedcutler/Documents/Middlebury/CS311/final/src",
                       help="PYTHONPATH for imports")
    parser.add_argument("--output-dir", default="experiments/results",
                       help="Output directory for results")
    parser.add_argument("--experiment-types", nargs='+',
                       choices=['time_matched', 'degradation', 'baseline', 'head_to_head', 'all'],
                       default=['all'],
                       help="Which experiment types to run")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print experiments without running them")
    parser.add_argument("--yes", "-y", action="store_true",
                       help="Skip confirmation prompt")

    args = parser.parse_args()

    # Create experiments
    all_experiments = create_experiment_matrix()

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
