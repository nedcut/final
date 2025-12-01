"""Profile MCTS performance to identify bottlenecks."""
import cProfile
import pstats
import sys
from io import StringIO

sys.path.insert(0, '/Users/nedcutler/Documents/Middlebury/CS311/final/src')

from minichess.game import initial_state
from minichess.agents import MCTSAgent


def run_mcts():
    """Run MCTS agent for profiling."""
    state = initial_state()
    agent = MCTSAgent(simulations=100, rollout_depth=40, seed=42)

    # Make several moves to get good profiling data
    for _ in range(3):
        move = agent.choose_move(state)
        state = state.make_move(move, validate=False)
        if state.is_terminal():
            break


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    run_mcts()

    profiler.disable()

    # Print stats
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    print(s.getvalue())
