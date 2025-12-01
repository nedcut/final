#!/usr/bin/env python3
"""
High MCTS Simulation Experiments

Tests MCTS with very high simulation counts (300, 500, 1000) against
Minimax at all depths to determine performance ceiling.
"""

import argparse
import subprocess
import sys
import time
import csv
import json
from pathlib import Path
from datetime import datetime


def run_match(mcts_sims, minimax_depth, num_games=50):
    """Run a single match using match_runner.py CLI."""
    cmd = [
        sys.executable,
        "examples/match_runner.py",
        "--white", "mcts",
        "--black", "minimax",
        "--games", str(num_games),
        "--swap-colors",
        "--white-simulations", str(mcts_sims),
        "--black-depth", str(minimax_depth),
        "--print-every", "10",
    ]

    print(f"\nRunning: MCTS({mcts_sims}) vs Minimax({minimax_depth})")
    print(f"Command: {' '.join(cmd)}")

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env={"PYTHONPATH": "src"})
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return None

    # Parse output
    output = result.stdout
    print(output)

    # Extract results from output
    lines = output.strip().split('\n')

    # Find "By color" line: "By color -> White X | Draw Y | Black Z (avg plies: W.W)"
    color_line = [l for l in lines if "By color ->" in l][0]
    parts = color_line.split("->")[1].strip()
    color_parts = parts.split("|")

    white_wins = int(color_parts[0].split()[1])
    draws = int(color_parts[1].split()[1])
    black_wins = int(color_parts[2].split()[1])

    avg_plies_str = parts.split("(avg plies:")[1].strip().rstrip(")")
    avg_plies = float(avg_plies_str)

    # Find "By agent" line: "By agent  -> agent1 X | Draw Y | agent2 Z"
    agent_line = [l for l in lines if "By agent  ->" in l][0]
    agent_parts = agent_line.split("->")[1].strip().split("|")

    mcts_wins = int(agent_parts[0].split()[1])
    minimax_wins = int(agent_parts[2].split()[1])

    return {
        "mcts_wins": mcts_wins,
        "draws": draws,
        "minimax_wins": minimax_wins,
        "white_wins": white_wins,
        "black_wins": black_wins,
        "avg_plies": avg_plies,
        "elapsed_seconds": elapsed,
    }


def main():
    """Run all high MCTS experiments."""
    parser = argparse.ArgumentParser(description="Run high MCTS simulation experiments")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("="*80)
    print("HIGH MCTS SIMULATION EXPERIMENTS")
    print("="*80)
    print("\nResearch Question:")
    print("Can MCTS reach 30-40% competitiveness with massive simulation counts?")
    print("\nTesting: MCTS(300, 500, 1000) vs Minimax(2, 3, 4)")
    print("="*80)

    mcts_configs = [300, 500, 1000]
    minimax_configs = [2, 3, 4]

    total_experiments = len(mcts_configs) * len(minimax_configs)
    total_games = total_experiments * 50

    print(f"\nTotal experiments: {total_experiments}")
    print(f"Total games: {total_games}")
    print(f"Estimated time: 2-4 hours")

    if not args.yes:
        response = input("\nThis is a LONG experiment. Proceed? (yes/no): ").strip().lower()
        if response != "yes":
            print("Cancelled.")
            return
    else:
        print("\nAuto-confirmed with --yes flag, proceeding...")
        print()

    # Results storage
    results_dir = Path("experiments/results")
    results_dir.mkdir(exist_ok=True)

    csv_path = results_dir / "experiment_results.csv"
    json_path = results_dir / "experiment_results.json"

    # Load existing results
    if json_path.exists():
        with open(json_path, "r") as f:
            all_results = json.load(f)
    else:
        all_results = []

    start_total = time.time()
    exp_id = 30  # Continue from previous experiments

    for i, mcts_sims in enumerate(mcts_configs, 1):
        for j, mm_depth in enumerate(minimax_configs, 1):
            exp_num = (i - 1) * len(minimax_configs) + j
            print(f"\n{'='*80}")
            print(f"Progress: {exp_num}/{total_experiments}")
            print(f"{'='*80}")

            result = run_match(mcts_sims, mm_depth, num_games=50)

            if result is None:
                print("ERROR: Match failed!")
                continue

            # Calculate win rate
            win_rate = (result["mcts_wins"] + 0.5 * result["draws"]) / 50 * 100

            print(f"\nResults: mcts {result['mcts_wins']}-{result['draws']}-{result['minimax_wins']} minimax")
            print(f"Win rate: {win_rate:.1f}%")
            print(f"Avg plies: {result['avg_plies']:.1f}")
            print(f"Time: {result['elapsed_seconds']:.1f}s")

            # Save result
            result_record = {
                "experiment_id": f"HIGH{exp_id:03d}",
                "experiment_name": f"MCTS({mcts_sims}) vs Minimax({mm_depth})",
                "description": f"High MCTS: sims={mcts_sims} vs depth={mm_depth}",
                "white_agent": "mcts",
                "black_agent": "minimax",
                "white_config": mcts_sims,
                "black_config": mm_depth,
                "white_wins": result["white_wins"],
                "draws": result["draws"],
                "black_wins": result["black_wins"],
                "total_games": 50,
                "avg_plies": result["avg_plies"],
                "elapsed_seconds": result["elapsed_seconds"],
                "timestamp": datetime.now().isoformat(),
            }

            # Append to CSV
            write_header = not csv_path.exists() or csv_path.stat().st_size == 0

            with open(csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=result_record.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(result_record)

            # Append to JSON
            all_results.append(result_record)
            with open(json_path, "w") as f:
                json.dump(all_results, f, indent=2)

            print(f"Results saved to {csv_path}")

            exp_id += 1

            # Progress estimate
            elapsed_total = time.time() - start_total
            avg_per_exp = elapsed_total / exp_num
            remaining = total_experiments - exp_num
            eta_minutes = (avg_per_exp * remaining) / 60

            print(f"\nElapsed: {elapsed_total/60:.1f} min | ETA: {eta_minutes:.1f} min")

    total_elapsed = time.time() - start_total
    print(f"\n{'='*80}")
    print(f"EXPERIMENTS COMPLETE!")
    print(f"{'='*80}")
    print(f"Total time: {total_elapsed/60:.1f} minutes ({total_elapsed/3600:.2f} hours)")
    print(f"Results saved to: {results_dir}")


if __name__ == "__main__":
    main()
