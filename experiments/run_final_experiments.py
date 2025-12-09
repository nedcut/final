#!/usr/bin/env python3
"""Final comprehensive experimental evaluation for MiniChess AI research.

This script runs all experiments needed for final research results in a single
execution. It produces statistically significant data (100+ games per config)
to definitively answer the research question:

    "How do depth-limited minimax with alpha-beta pruning and Monte Carlo Tree
    Search compare in playing strength and computational efficiency on Gardner
    MiniChess, under equal computational budgets?"

Usage:
    # Run all experiments (recommended for final results)
    python experiments/run_final_experiments.py

    # Quick test run (10 games per experiment)
    python experiments/run_final_experiments.py --quick

    # Run specific phase only
    python experiments/run_final_experiments.py --phase 3

    # Dry run to see what would be executed
    python experiments/run_final_experiments.py --dry-run

Results are saved to experiments/results/final_results_TIMESTAMP.{csv,json}
"""

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment."""
    phase: int
    experiment_id: str
    description: str
    agent1_type: str
    agent1_config: dict[str, Any]
    agent2_type: str
    agent2_config: dict[str, Any]
    num_games: int
    seed: int


@dataclass
class ExperimentResult:
    """Results from a single experiment."""
    config: ExperimentConfig
    agent1_wins: int
    draws: int
    agent2_wins: int
    white_wins: int
    black_wins: int
    avg_plies: float
    elapsed_time: float
    agent1_win_rate: float = field(init=False)
    agent2_win_rate: float = field(init=False)

    def __post_init__(self):
        total = self.config.num_games
        self.agent1_win_rate = (self.agent1_wins + 0.5 * self.draws) / total * 100
        self.agent2_win_rate = (self.agent2_wins + 0.5 * self.draws) / total * 100


def create_experiment_suite(games_multiplier: float = 1.0) -> list[ExperimentConfig]:
    """Create the complete experiment suite for final research.

    Args:
        games_multiplier: Scale factor for number of games (0.1 for quick tests)

    Returns:
        List of experiment configurations organized by phase
    """
    experiments = []
    exp_counter = 0

    def scaled_games(n: int) -> int:
        return max(2, int(n * games_multiplier))

    # =========================================================================
    # PHASE 1: VALIDATION (Quick sanity check)
    # Purpose: Verify both implementations work correctly
    # =========================================================================
    phase1_configs = [
        ("minimax", {"depth": 3}, "random", {}, "Minimax(3) vs Random"),
        ("mcts", {"simulations": 100}, "random", {}, "MCTS(100) vs Random"),
        ("minimax", {"depth": 3}, "greedy", {}, "Minimax(3) vs Greedy"),
        ("mcts", {"simulations": 100}, "greedy", {}, "MCTS(100) vs Greedy"),
    ]

    for a1, a1_cfg, a2, a2_cfg, desc in phase1_configs:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=1,
            experiment_id=f"P1_{exp_counter:03d}",
            description=f"[Validation] {desc}",
            agent1_type=a1,
            agent1_config=a1_cfg,
            agent2_type=a2,
            agent2_config=a2_cfg,
            num_games=scaled_games(20),
            seed=1000 + exp_counter,
        ))

    # =========================================================================
    # PHASE 2: BASELINE PERFORMANCE
    # Purpose: Establish performance against weak opponents
    # =========================================================================

    # Minimax vs Random at various depths
    for depth in [2, 3, 4]:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=2,
            experiment_id=f"P2_{exp_counter:03d}",
            description=f"[Baseline] Minimax(depth={depth}) vs Random",
            agent1_type="minimax",
            agent1_config={"depth": depth},
            agent2_type="random",
            agent2_config={},
            num_games=scaled_games(50),
            seed=2000 + exp_counter,
        ))

    # MCTS vs Random at various simulation counts
    for sims in [50, 100, 200]:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=2,
            experiment_id=f"P2_{exp_counter:03d}",
            description=f"[Baseline] MCTS(sims={sims}) vs Random",
            agent1_type="mcts",
            agent1_config={"simulations": sims},
            agent2_type="random",
            agent2_config={},
            num_games=scaled_games(50),
            seed=2000 + exp_counter,
        ))

    # Minimax vs Greedy at various depths
    for depth in [2, 3, 4]:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=2,
            experiment_id=f"P2_{exp_counter:03d}",
            description=f"[Baseline] Minimax(depth={depth}) vs Greedy",
            agent1_type="minimax",
            agent1_config={"depth": depth},
            agent2_type="greedy",
            agent2_config={},
            num_games=scaled_games(50),
            seed=2000 + exp_counter,
        ))

    # MCTS vs Greedy at various simulation counts
    for sims in [50, 100, 200]:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=2,
            experiment_id=f"P2_{exp_counter:03d}",
            description=f"[Baseline] MCTS(sims={sims}) vs Greedy",
            agent1_type="mcts",
            agent1_config={"simulations": sims},
            agent2_type="greedy",
            agent2_config={},
            num_games=scaled_games(50),
            seed=2000 + exp_counter,
        ))

    # =========================================================================
    # PHASE 3: HEAD-TO-HEAD MATRIX (Core Research Data)
    # Purpose: Comprehensive comparison across parameter space
    # This is the main data for the research question
    # =========================================================================
    mcts_sims = [50, 100, 150, 200, 300, 500]
    minimax_depths = [2, 3, 4]

    for sims in mcts_sims:
        for depth in minimax_depths:
            exp_counter += 1
            experiments.append(ExperimentConfig(
                phase=3,
                experiment_id=f"P3_{exp_counter:03d}",
                description=f"[H2H] MCTS({sims}) vs Minimax({depth})",
                agent1_type="mcts",
                agent1_config={"simulations": sims},
                agent2_type="minimax",
                agent2_config={"depth": depth},
                num_games=scaled_games(100),
                seed=3000 + exp_counter,
            ))

    # =========================================================================
    # PHASE 4: TIME-MATCHED EXPERIMENTS (with enforced time limits)
    # Purpose: Fair comparison at equal computational budgets
    #
    # Both agents get identical per-move time budgets enforced via time_limit.
    # - MCTS: high simulation cap (10000) so time is the only constraint
    # - Minimax: high depth cap (10) with iterative deepening fills time budget
    # =========================================================================
    time_budgets = [0.1, 0.2, 0.5, 1.0, 2.0]  # seconds per move

    for time_budget in time_budgets:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=4,
            experiment_id=f"P4_{exp_counter:03d}",
            description=f"[Time-Matched {time_budget}s] MCTS vs Minimax",
            agent1_type="mcts",
            # High simulation cap ensures time_limit is the binding constraint
            agent1_config={"simulations": 10000, "time_limit": time_budget},
            agent2_type="minimax",
            # High depth cap with iterative deepening ensures time_limit is binding
            agent2_config={"depth": 10, "time_limit": time_budget},
            num_games=scaled_games(100),
            seed=4000 + exp_counter,
        ))

    # =========================================================================
    # PHASE 5: HIGH-RESOURCE MCTS SCALING
    # Purpose: Test MCTS performance ceiling with abundant resources
    # =========================================================================
    high_mcts_sims = [500, 750, 1000]

    for sims in high_mcts_sims:
        exp_counter += 1
        experiments.append(ExperimentConfig(
            phase=5,
            experiment_id=f"P5_{exp_counter:03d}",
            description=f"[High-MCTS] MCTS({sims}) vs Minimax(3)",
            agent1_type="mcts",
            agent1_config={"simulations": sims},
            agent2_type="minimax",
            agent2_config={"depth": 3},
            num_games=scaled_games(50),
            seed=5000 + exp_counter,
        ))

    return experiments


def build_command(config: ExperimentConfig, pythonpath: str) -> list[str]:
    """Build command to run match_runner.py with given config."""
    cmd = [
        sys.executable, "examples/match_runner.py",
        "--agent1", config.agent1_type,
        "--agent2", config.agent2_type,
        "--games", str(config.num_games),
        "--seed", str(config.seed),
        "--swap-colors",  # Always swap colors for fairness
    ]

    # Add agent1 config
    if config.agent1_type == "minimax" and "depth" in config.agent1_config:
        cmd.extend(["--agent1-depth", str(config.agent1_config["depth"])])
    if config.agent1_type == "mcts" and "simulations" in config.agent1_config:
        cmd.extend(["--agent1-simulations", str(config.agent1_config["simulations"])])
    if "time_limit" in config.agent1_config:
        cmd.extend(["--agent1-time-limit", str(config.agent1_config["time_limit"])])

    # Add agent2 config
    if config.agent2_type == "minimax" and "depth" in config.agent2_config:
        cmd.extend(["--agent2-depth", str(config.agent2_config["depth"])])
    if config.agent2_type == "mcts" and "simulations" in config.agent2_config:
        cmd.extend(["--agent2-simulations", str(config.agent2_config["simulations"])])
    if "time_limit" in config.agent2_config:
        cmd.extend(["--agent2-time-limit", str(config.agent2_config["time_limit"])])

    return cmd


def parse_output(output: str) -> tuple[int, int, int, int, int, float]:
    """Parse match_runner.py output.

    Returns: (agent1_wins, draws, agent2_wins, white_wins, black_wins, avg_plies)
    """
    lines = output.strip().split('\n')

    # Find "By color" line
    color_line = next(l for l in lines if "By color ->" in l)
    parts = color_line.split("->")[1].strip()
    color_parts = parts.split("|")

    white_wins = int(color_parts[0].split()[1])
    draws = int(color_parts[1].split()[1])
    black_wins = int(color_parts[2].split()[1])

    avg_plies_str = parts.split("(avg plies:")[1].strip().rstrip(")")
    avg_plies = float(avg_plies_str)

    # Find "By agent" line
    agent_line = next(l for l in lines if "By agent  ->" in l)
    agent_parts = agent_line.split("->")[1].strip().split("|")

    # Use [-1] to get the last token (win count) since agent labels may contain spaces
    # e.g., "mcts(sims=10000, time=0.05s) 0" -> split gives ['mcts(sims=10000,', 'time=0.05s)', '0']
    agent1_wins = int(agent_parts[0].split()[-1])
    agent2_wins = int(agent_parts[2].split()[-1])

    return agent1_wins, draws, agent2_wins, white_wins, black_wins, avg_plies


def run_experiment(config: ExperimentConfig, pythonpath: str) -> ExperimentResult:
    """Run a single experiment and return results."""
    cmd = build_command(config, pythonpath)

    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": pythonpath},
        cwd=str(Path(pythonpath).parent),
    )
    elapsed = time.time() - start_time

    if result.returncode != 0:
        print(f"ERROR: {config.experiment_id} failed!")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Experiment {config.experiment_id} failed")

    a1_wins, draws, a2_wins, w_wins, b_wins, avg_plies = parse_output(result.stdout)

    return ExperimentResult(
        config=config,
        agent1_wins=a1_wins,
        draws=draws,
        agent2_wins=a2_wins,
        white_wins=w_wins,
        black_wins=b_wins,
        avg_plies=avg_plies,
        elapsed_time=elapsed,
    )


def save_results(results: list[ExperimentResult], output_dir: Path, timestamp: str):
    """Save results to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"final_results_{timestamp}.csv"
    json_path = output_dir / f"final_results_{timestamp}.json"

    # Save CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'phase', 'experiment_id', 'description',
            'agent1_type', 'agent1_config', 'agent2_type', 'agent2_config',
            'num_games', 'agent1_wins', 'draws', 'agent2_wins',
            'agent1_win_rate', 'agent2_win_rate',
            'white_wins', 'black_wins', 'avg_plies', 'elapsed_time'
        ])

        for r in results:
            writer.writerow([
                r.config.phase,
                r.config.experiment_id,
                r.config.description,
                r.config.agent1_type,
                json.dumps(r.config.agent1_config),
                r.config.agent2_type,
                json.dumps(r.config.agent2_config),
                r.config.num_games,
                r.agent1_wins,
                r.draws,
                r.agent2_wins,
                f"{r.agent1_win_rate:.1f}",
                f"{r.agent2_win_rate:.1f}",
                r.white_wins,
                r.black_wins,
                r.avg_plies,
                f"{r.elapsed_time:.1f}",
            ])

    print(f"Results saved to: {csv_path}")

    # Save JSON
    json_data = {
        "metadata": {
            "timestamp": timestamp,
            "total_experiments": len(results),
            "total_games": sum(r.config.num_games for r in results),
        },
        "results": [
            {
                "config": asdict(r.config),
                "results": {
                    "agent1_wins": r.agent1_wins,
                    "draws": r.draws,
                    "agent2_wins": r.agent2_wins,
                    "agent1_win_rate": r.agent1_win_rate,
                    "agent2_win_rate": r.agent2_win_rate,
                    "white_wins": r.white_wins,
                    "black_wins": r.black_wins,
                    "avg_plies": r.avg_plies,
                    "elapsed_time": r.elapsed_time,
                }
            }
            for r in results
        ]
    }

    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)

    print(f"Results saved to: {json_path}")


def print_summary(results: list[ExperimentResult]):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)

    # Group by phase
    phases = {}
    for r in results:
        phase = r.config.phase
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(r)

    phase_names = {
        1: "Validation",
        2: "Baseline Performance",
        3: "Head-to-Head Matrix",
        4: "Time-Matched",
        5: "High-Resource MCTS",
    }

    for phase in sorted(phases.keys()):
        phase_results = phases[phase]
        print(f"\n--- Phase {phase}: {phase_names.get(phase, 'Unknown')} ---")
        print(f"{'Experiment':<40} {'Games':>6} {'A1 Wins':>8} {'Draws':>6} {'A2 Wins':>8} {'A1 Win%':>8}")
        print("-" * 80)

        for r in phase_results:
            desc = r.config.description.replace(f"[{phase_names.get(phase, 'Unknown').split()[0]}] ", "")
            if len(desc) > 38:
                desc = desc[:35] + "..."
            print(f"{desc:<40} {r.config.num_games:>6} {r.agent1_wins:>8} {r.draws:>6} {r.agent2_wins:>8} {r.agent1_win_rate:>7.1f}%")

    # Overall statistics
    total_games = sum(r.config.num_games for r in results)
    total_time = sum(r.elapsed_time for r in results)
    print(f"\n{'=' * 80}")
    print(f"TOTAL: {len(results)} experiments, {total_games} games, {total_time/60:.1f} minutes")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive experiments for final research results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full experiment suite (~2-3 hours)
  python experiments/run_final_experiments.py

  # Quick test (10% of games, ~15 minutes)
  python experiments/run_final_experiments.py --quick

  # Run only Phase 3 (head-to-head matrix)
  python experiments/run_final_experiments.py --phase 3

  # See what would run without executing
  python experiments/run_final_experiments.py --dry-run
        """
    )

    parser.add_argument(
        "--pythonpath",
        default="/Users/nedcutler/Documents/Middlebury/CS311/final/src",
        help="PYTHONPATH for imports"
    )
    parser.add_argument(
        "--output-dir",
        default="experiments/results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run only specific phase (1-5)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 10%% of games per experiment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Create experiment suite
    multiplier = 0.1 if args.quick else 1.0
    experiments = create_experiment_suite(games_multiplier=multiplier)

    # Filter by phase if specified
    if args.phase:
        experiments = [e for e in experiments if e.phase == args.phase]

    # Print experiment plan
    print("=" * 80)
    print("FINAL EXPERIMENT SUITE")
    print("=" * 80)

    phase_names = {
        1: "Validation",
        2: "Baseline Performance",
        3: "Head-to-Head Matrix",
        4: "Time-Matched",
        5: "High-Resource MCTS",
    }

    current_phase = None
    for exp in experiments:
        if exp.phase != current_phase:
            current_phase = exp.phase
            print(f"\n=== Phase {current_phase}: {phase_names.get(current_phase, 'Unknown')} ===")
        print(f"  {exp.experiment_id}: {exp.description} ({exp.num_games} games)")

    total_games = sum(e.num_games for e in experiments)
    est_time_min = total_games * 1.5 / 60  # ~1.5s per game average
    est_time_max = total_games * 3 / 60    # ~3s per game with high MCTS

    print(f"\n{'=' * 80}")
    print(f"Total: {len(experiments)} experiments, {total_games} games")
    print(f"Estimated time: {est_time_min:.0f} - {est_time_max:.0f} minutes")
    print("=" * 80)

    if args.dry_run:
        print("\nDry run complete - no experiments executed")
        return

    # Confirm
    if not args.yes:
        response = input("\nProceed with experiments? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted")
            return
    else:
        print("\nAuto-confirmed with --yes flag, proceeding...")

    # Run experiments
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir)
    results = []

    start_time = time.time()
    for i, exp in enumerate(experiments, 1):
        print(f"\n[{i}/{len(experiments)}] {exp.experiment_id}: {exp.description}")
        print(f"  Running {exp.num_games} games...")

        try:
            result = run_experiment(exp, args.pythonpath)
            results.append(result)

            print(f"  → Agent1: {result.agent1_wins} wins ({result.agent1_win_rate:.1f}%)")
            print(f"  → Agent2: {result.agent2_wins} wins ({result.agent2_win_rate:.1f}%)")
            print(f"  → Draws: {result.draws}, Avg plies: {result.avg_plies:.1f}")
            print(f"  → Time: {result.elapsed_time:.1f}s")

            # Save intermediate results
            save_results(results, output_dir, timestamp)

        except Exception as e:
            print(f"  ERROR: {e}")
            print("  Continuing with next experiment...")

    # Final summary
    elapsed_total = time.time() - start_time
    print(f"\n{'=' * 80}")
    print(f"EXPERIMENTS COMPLETE")
    print(f"Time: {elapsed_total/60:.1f} minutes")
    print(f"{'=' * 80}")

    print_summary(results)


if __name__ == "__main__":
    main()
