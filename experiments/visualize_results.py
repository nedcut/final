#!/usr/bin/env python3
"""Generate visualizations from experiment results."""
import csv
import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

# Style configuration for consistent, professional charts
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = {
    'minimax': '#2E86AB',  # Blue
    'mcts': '#A23B72',     # Magenta
    'draw': '#F18F01',     # Orange
    'neutral': '#6C757D',  # Gray
}


def load_results(results_file: Path) -> List[Dict]:
    """Load results from CSV file."""
    results = []
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def get_phase_results(results: List[Dict], phase: int) -> List[Dict]:
    """Filter results by phase number."""
    return [r for r in results if int(r['phase']) == phase]


def plot_head_to_head_heatmap(results: List[Dict], output_dir: Path):
    """Create heatmap of MCTS win rates vs Minimax depths."""
    phase3 = get_phase_results(results, 3)

    # Extract data into matrix
    mcts_sims = [50, 100, 150, 200, 300, 500]
    mm_depths = [2, 3, 4]

    matrix = np.zeros((len(mcts_sims), len(mm_depths)))

    for r in phase3:
        config1 = json.loads(r['agent1_config'])
        config2 = json.loads(r['agent2_config'])
        sims = config1['simulations']
        depth = config2['depth']

        # Win rate includes half credit for draws
        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        total = int(r['num_games'])
        win_rate = (wins + 0.5 * draws) / total * 100

        i = mcts_sims.index(sims)
        j = mm_depths.index(depth)
        matrix[i, j] = win_rate

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.grid(False)

    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=50)

    # Labels
    ax.set_xticks(range(len(mm_depths)))
    ax.set_xticklabels([f'Depth {d}' for d in mm_depths], fontsize=12)
    ax.set_yticks(range(len(mcts_sims)))
    ax.set_yticklabels([f'{s} sims' for s in mcts_sims], fontsize=12)

    ax.set_xlabel('Minimax Configuration', fontsize=14, fontweight='bold')
    ax.set_ylabel('MCTS Configuration', fontsize=14, fontweight='bold')
    ax.set_title('MCTS Win Rate vs Minimax\n(100 games per cell)', fontsize=16, fontweight='bold')

    # Add text annotations
    for i in range(len(mcts_sims)):
        for j in range(len(mm_depths)):
            value = matrix[i, j]
            color = 'white' if value < 15 or value > 35 else 'black'
            ax.text(j, i, f'{value:.1f}%', ha='center', va='center',
                   color=color, fontsize=14, fontweight='bold')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('MCTS Win Rate (%)', fontsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / 'heatmap_head_to_head.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Head-to-head heatmap")


def plot_mcts_scaling(results: List[Dict], output_dir: Path):
    """Line chart showing MCTS performance scaling against each Minimax depth."""
    phase3 = get_phase_results(results, 3)
    phase5 = get_phase_results(results, 5)

    mcts_sims = [50, 100, 150, 200, 300, 500]
    mm_depths = [2, 3, 4]

    # Build data structure
    data = {d: [] for d in mm_depths}

    for r in phase3:
        config1 = json.loads(r['agent1_config'])
        config2 = json.loads(r['agent2_config'])
        sims = config1['simulations']
        depth = config2['depth']

        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        total = int(r['num_games'])
        win_rate = (wins + 0.5 * draws) / total * 100

        data[depth].append((sims, win_rate))

    # Add high-resource MCTS data for depth 3
    for r in phase5:
        config1 = json.loads(r['agent1_config'])
        sims = config1['simulations']

        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        total = int(r['num_games'])
        win_rate = (wins + 0.5 * draws) / total * 100

        data[3].append((sims, win_rate))

    # Sort by simulations
    for d in data:
        data[d].sort(key=lambda x: x[0])

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['#2E86AB', '#E94F37', '#F6BD60']
    markers = ['o', 's', '^']

    for i, depth in enumerate(mm_depths):
        sims = [x[0] for x in data[depth]]
        rates = [x[1] for x in data[depth]]
        ax.plot(sims, rates, marker=markers[i], markersize=10, linewidth=2.5,
               color=colors[i], label=f'vs Minimax Depth {depth}')

    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Parity (50%)')

    ax.set_xlabel('MCTS Simulations', fontsize=14, fontweight='bold')
    ax.set_ylabel('MCTS Win Rate (%)', fontsize=14, fontweight='bold')
    ax.set_title('MCTS Performance Scaling', fontsize=16, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.set_ylim(0, 55)
    ax.set_xlim(0, 1050)

    ax.tick_params(axis='both', labelsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / 'mcts_scaling.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ MCTS scaling chart")


def plot_time_matched(results: List[Dict], output_dir: Path):
    """Bar chart for time-matched experiments (the fairest comparison)."""
    phase4 = get_phase_results(results, 4)

    budgets = ['~0.5s', '~1.0s', '~2.0s']
    mcts_rates = []
    minimax_rates = []
    draw_rates = []

    for r in sorted(phase4, key=lambda x: x['experiment_id']):
        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        losses = int(r['agent2_wins'])
        total = int(r['num_games'])

        mcts_rates.append(wins / total * 100)
        draw_rates.append(draws / total * 100)
        minimax_rates.append(losses / total * 100)

    x = np.arange(len(budgets))
    width = 0.6

    fig, ax = plt.subplots(figsize=(9, 6))

    # Stacked bar chart
    p1 = ax.bar(x, mcts_rates, width, label='MCTS Wins', color=COLORS['mcts'])
    p2 = ax.bar(x, draw_rates, width, bottom=mcts_rates, label='Draws', color=COLORS['draw'])
    p3 = ax.bar(x, minimax_rates, width, bottom=[m+d for m,d in zip(mcts_rates, draw_rates)],
                label='Minimax Wins', color=COLORS['minimax'])

    ax.set_xlabel('Computational Budget', fontsize=14, fontweight='bold')
    ax.set_ylabel('Outcome (%)', fontsize=14, fontweight='bold')
    ax.set_title('Time-Matched Comparison\n(Equal computational resources)', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(budgets, fontsize=12)
    ax.legend(fontsize=11, loc='upper right', bbox_to_anchor=(1.0, 1.15))
    ax.set_ylim(0, 105)

    # Add percentage labels on bars
    for i, (mcts, draw, mm) in enumerate(zip(mcts_rates, draw_rates, minimax_rates)):
        if mcts > 3:
            ax.text(i, mcts/2, f'{mcts:.0f}%', ha='center', va='center',
                   color='white', fontweight='bold', fontsize=11)
        if draw > 3:
            ax.text(i, mcts + draw/2, f'{draw:.0f}%', ha='center', va='center',
                   color='white', fontweight='bold', fontsize=11)
        ax.text(i, mcts + draw + mm/2, f'{mm:.0f}%', ha='center', va='center',
               color='white', fontweight='bold', fontsize=14)

    ax.tick_params(axis='both', labelsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / 'time_matched.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Time-matched comparison chart")


def plot_baseline_comparison(results: List[Dict], output_dir: Path):
    """Grouped bar chart comparing baseline performance against Random and Greedy."""
    phase2 = get_phase_results(results, 2)

    # Extract data
    minimax_vs_random = []
    mcts_vs_random = []
    minimax_vs_greedy = []
    mcts_vs_greedy = []

    minimax_labels = ['Depth 2', 'Depth 3', 'Depth 4']
    mcts_labels = ['50 sims', '100 sims', '200 sims']

    for r in phase2:
        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        total = int(r['num_games'])
        win_rate = (wins + 0.5 * draws) / total * 100

        desc = r['description']
        if 'Minimax' in desc and 'Random' in desc:
            minimax_vs_random.append(win_rate)
        elif 'MCTS' in desc and 'Random' in desc:
            mcts_vs_random.append(win_rate)
        elif 'Minimax' in desc and 'Greedy' in desc:
            minimax_vs_greedy.append(win_rate)
        elif 'MCTS' in desc and 'Greedy' in desc:
            mcts_vs_greedy.append(win_rate)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    x = np.arange(3)
    width = 0.35

    # Plot vs Random
    ax1 = axes[0]
    ax1.bar(x - width/2, minimax_vs_random, width, label='Minimax', color=COLORS['minimax'])
    ax1.bar(x + width/2, mcts_vs_random, width, label='MCTS', color=COLORS['mcts'])
    ax1.set_xlabel('Configuration', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('vs Random Agent', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['Low', 'Medium', 'High'], fontsize=11)
    ax1.legend(fontsize=10, loc='upper right', bbox_to_anchor=(1.0, 1.15))
    ax1.set_ylim(90, 101)
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.3)

    # Add value labels
    for i, (m, c) in enumerate(zip(minimax_vs_random, mcts_vs_random)):
        ax1.text(i - width/2, m + 0.3, f'{m:.0f}%', ha='center', fontsize=10, fontweight='bold')
        ax1.text(i + width/2, c + 0.3, f'{c:.0f}%', ha='center', fontsize=10, fontweight='bold')

    # Plot vs Greedy
    ax2 = axes[1]
    ax2.bar(x - width/2, minimax_vs_greedy, width, label='Minimax', color=COLORS['minimax'])
    ax2.bar(x + width/2, mcts_vs_greedy, width, label='MCTS', color=COLORS['mcts'])
    ax2.set_xlabel('Configuration', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold')
    ax2.set_title('vs Greedy Agent', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Low', 'Medium', 'High'], fontsize=11)
    ax2.legend(fontsize=10, loc='upper right', bbox_to_anchor=(1.0, 1.15))
    ax2.set_ylim(60, 105)
    ax2.axhline(y=100, color='gray', linestyle='--', alpha=0.3)

    # Add value labels
    for i, (m, c) in enumerate(zip(minimax_vs_greedy, mcts_vs_greedy)):
        ax2.text(i - width/2, m + 1, f'{m:.0f}%', ha='center', fontsize=10, fontweight='bold')
        ax2.text(i + width/2, c + 1, f'{c:.0f}%', ha='center', fontsize=10, fontweight='bold')

    fig.suptitle('Baseline Performance Comparison (50 games each)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'baseline_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Baseline comparison chart")


def plot_game_length_analysis(results: List[Dict], output_dir: Path):
    """Scatter plot showing relationship between MCTS win rate and game length."""
    phase3 = get_phase_results(results, 3)

    win_rates = []
    avg_plies = []
    labels = []
    colors = []

    depth_colors = {2: '#2E86AB', 3: '#E94F37', 4: '#F6BD60'}

    for r in phase3:
        config1 = json.loads(r['agent1_config'])
        config2 = json.loads(r['agent2_config'])
        sims = config1['simulations']
        depth = config2['depth']

        wins = int(r['agent1_wins'])
        draws = int(r['draws'])
        total = int(r['num_games'])
        win_rate = (wins + 0.5 * draws) / total * 100

        win_rates.append(win_rate)
        avg_plies.append(float(r['avg_plies']))
        labels.append(f'{sims}s vs d{depth}')
        colors.append(depth_colors[depth])

    fig, ax = plt.subplots(figsize=(10, 6))

    scatter = ax.scatter(avg_plies, win_rates, c=colors, s=150, alpha=0.7, edgecolors='black')

    # Create legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2E86AB', edgecolor='black', label='vs Depth 2'),
        Patch(facecolor='#E94F37', edgecolor='black', label='vs Depth 3'),
        Patch(facecolor='#F6BD60', edgecolor='black', label='vs Depth 4'),
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='upper left')

    ax.set_xlabel('Average Game Length (plies)', fontsize=14, fontweight='bold')
    ax.set_ylabel('MCTS Win Rate (%)', fontsize=14, fontweight='bold')
    ax.set_title('Game Length vs MCTS Success', fontsize=16, fontweight='bold')
    ax.set_ylim(0, 45)

    ax.tick_params(axis='both', labelsize=12)

    plt.tight_layout()
    plt.savefig(output_dir / 'game_length_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  ✓ Game length analysis chart")

def main():
    # Find the most recent results file
    results_dir = Path("experiments/results")
    results_files = list(results_dir.glob("final_results_*.csv"))

    if not results_files:
        print("Error: No results files found in experiments/results/")
        print("Run experiments first with: python experiments/run_final_experiments.py")
        return

    # Use most recent
    results_file = max(results_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading results from: {results_file.name}")

    results = load_results(results_file)
    print(f"Loaded {len(results)} experiments\n")

    # Create output directory for figures
    output_dir = Path("experiments/figures")
    output_dir.mkdir(exist_ok=True)

    print("Generating visualizations...")

    # Generate all charts
    plot_head_to_head_heatmap(results, output_dir)
    plot_mcts_scaling(results, output_dir)
    plot_time_matched(results, output_dir)
    plot_baseline_comparison(results, output_dir)
    plot_game_length_analysis(results, output_dir)

    print(f"\n✅ All visualizations saved to: {output_dir}/")
    print("\nGenerated files:")
    for f in sorted(output_dir.glob("*.png")):
        print(f"  • {f.name}")


if __name__ == "__main__":
    main()
