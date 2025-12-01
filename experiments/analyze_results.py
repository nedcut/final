#!/usr/bin/env python3
"""Analyze experiment results and generate summary statistics."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_results(results_file: Path) -> List[Dict]:
    """Load results from CSV file."""
    results = []
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def calculate_win_rate(wins: int, draws: int, losses: int) -> float:
    """Calculate win rate (wins + 0.5*draws) / total."""
    total = wins + draws + losses
    if total == 0:
        return 0.0
    return (wins + 0.5 * draws) / total


def analyze_by_experiment_type(results: List[Dict]):
    """Analyze results grouped by experiment type."""
    by_type = defaultdict(list)

    for result in results:
        by_type[result['experiment_type']].append(result)

    print("\n" + "="*80)
    print("ANALYSIS BY EXPERIMENT TYPE")
    print("="*80)

    for exp_type, experiments in sorted(by_type.items()):
        print(f"\n{exp_type.upper()} ({len(experiments)} experiments)")
        print("-" * 80)

        for exp in experiments:
            agent1_wins = int(exp['agent1_wins'])
            draws = int(exp['draws'])
            agent2_wins = int(exp['agent2_wins'])

            win_rate = calculate_win_rate(agent1_wins, draws, agent2_wins)

            print(f"  {exp['experiment_id']}: {exp['description']}")
            print(f"    {exp['agent1_type']} {agent1_wins}-{draws}-{agent2_wins} {exp['agent2_type']}")
            print(f"    Win rate: {win_rate:.1%} | Avg plies: {float(exp['avg_plies']):.1f} | Time: {float(exp['total_time_sec']):.1f}s")


def analyze_head_to_head_matrix(results: List[Dict]):
    """Create win rate matrix for head-to-head experiments."""
    h2h_results = [r for r in results if r['experiment_type'] == 'head_to_head']

    if not h2h_results:
        return

    print("\n" + "="*80)
    print("HEAD-TO-HEAD WIN RATE MATRIX")
    print("="*80)
    print("\nMCTS (rows) vs Minimax (columns) - showing MCTS win rate\n")

    # Extract unique configs
    mcts_configs = set()
    minimax_configs = set()

    for result in h2h_results:
        if result['agent1_type'] == 'mcts':
            mcts_configs.add(json.loads(result['agent1_config'])['simulations'])
        if result['agent2_type'] == 'minimax':
            minimax_configs.add(json.loads(result['agent2_config'])['depth'])

    mcts_configs = sorted(mcts_configs)
    minimax_configs = sorted(minimax_configs)

    # Build matrix
    matrix = {}
    for result in h2h_results:
        mcts_sims = json.loads(result['agent1_config'])['simulations']
        mm_depth = json.loads(result['agent2_config'])['depth']

        agent1_wins = int(result['agent1_wins'])
        draws = int(result['draws'])
        agent2_wins = int(result['agent2_wins'])

        win_rate = calculate_win_rate(agent1_wins, draws, agent2_wins)
        matrix[(mcts_sims, mm_depth)] = win_rate

    # Print matrix
    header = "MCTS\\MM |" + "|".join(f" d={d:2d} " for d in minimax_configs)
    print(header)
    print("-" * len(header))

    for mcts_sim in mcts_configs:
        row = f"s={mcts_sim:4d} |"
        for mm_depth in minimax_configs:
            if (mcts_sim, mm_depth) in matrix:
                win_rate = matrix[(mcts_sim, mm_depth)]
                row += f" {win_rate:5.1%} |"
            else:
                row += "   -   |"
        print(row)


def analyze_degradation(results: List[Dict]):
    """Analyze resource degradation experiments."""
    deg_results = [r for r in results if r['experiment_type'] == 'degradation']

    if not deg_results:
        return

    print("\n" + "="*80)
    print("RESOURCE DEGRADATION ANALYSIS")
    print("="*80)

    # Group by agent type
    minimax_deg = [r for r in deg_results if r['agent1_type'] == 'minimax']
    mcts_deg = [r for r in deg_results if r['agent1_type'] == 'mcts']

    if minimax_deg:
        print("\nMinimax vs Greedy (varying depth):")
        print("-" * 40)
        for result in sorted(minimax_deg, key=lambda x: -int(json.loads(x['agent1_config'])['depth'])):
            depth = json.loads(result['agent1_config'])['depth']
            agent1_wins = int(result['agent1_wins'])
            draws = int(result['draws'])
            agent2_wins = int(result['agent2_wins'])
            win_rate = calculate_win_rate(agent1_wins, draws, agent2_wins)
            print(f"  Depth {depth}: {agent1_wins}-{draws}-{agent2_wins} (win rate: {win_rate:.1%})")

    if mcts_deg:
        print("\nMCTS vs Greedy (varying simulations):")
        print("-" * 40)
        for result in sorted(mcts_deg, key=lambda x: -int(json.loads(x['agent1_config'])['simulations'])):
            sims = json.loads(result['agent1_config'])['simulations']
            agent1_wins = int(result['agent1_wins'])
            draws = int(result['draws'])
            agent2_wins = int(result['agent2_wins'])
            win_rate = calculate_win_rate(agent1_wins, draws, agent2_wins)
            print(f"  Sims {sims:3d}: {agent1_wins}-{draws}-{agent2_wins} (win rate: {win_rate:.1%})")


def main():
    results_file = Path("experiments/results/experiment_results.csv")

    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        print("Run experiments first with: python experiments/run_experiments.py")
        return

    results = load_results(results_file)

    print(f"\nLoaded {len(results)} experiment results")

    analyze_by_experiment_type(results)
    analyze_head_to_head_matrix(results)
    analyze_degradation(results)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    total_games = sum(int(r['num_games']) for r in results)
    total_time = sum(float(r['total_time_sec']) for r in results)
    print(f"Total experiments: {len(results)}")
    print(f"Total games played: {total_games}")
    print(f"Total compute time: {total_time:.1f}s ({total_time/60:.1f} minutes)")


if __name__ == "__main__":
    main()
