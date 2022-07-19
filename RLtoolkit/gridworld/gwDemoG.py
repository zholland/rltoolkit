"""
This is gridworld code with a graphical display and user interface.
For non graphical gridworld, use gwDemoN.py

There are three main objects:
   Gridworld          Just the environment with no graphics stuff
   Gridworldview      A gridworld with view (graphics related stuff)
   GridworldWindow    A simulation window to hold the gridworldview with buttons for simulation

The walls are stateaction pairs which leave you in the same square rather
than taking you to your neighboring square.  If there were no walls, wraparound
would occur at the gridworld edges.
We start with walls all around the edges.

The barriers (squares you can't pass into) are overlaid on top of this.

The goal square is a terminal state.  Reward is +1 for reaching the goal, 0 else.
"""

###
import functools

from .gwguimain import *
from .gwobject import *
import argparse
import random

AGENT_CLASSES = {
    "Sarsa": SarsaGridAgent,
    "SarsaLambda": SarsaLambdaGridAgent,
    "Qlambda": QlambdaGridAgent,
    "Qonestep": QonestepGridAgent,
    "Dyna": DynaGridAgent,
}


# TRACE_AGENTS = set([QlambdaGridAgent, SarsaLambdaGridAgent])

def runDemo():
  makeGridworldSimulation(16, 16, 87, 15, 30)
  gMainloop()


def runObjDemo(
    width=16,
    height=16,
    start_state=87,
    goal_state=15,
    square_size=30,
    speed=0,
    agent_class=DynaGridAgent,
    alpha=0.5,
    epsilon=0.05,
    lambda_=0.8,
    walls=None,
):
  random.seed(42)

  agent_class = functools.partial(agent_class, alpha=alpha, epsilon=epsilon,
                                  agentlambda=lambda_)

  window = makeObjectGridworldSimulation(w=width,
                                         h=height,
                                         st=start_state,
                                         g=goal_state,
                                         size=square_size,
                                         agentclass=agent_class)
  if walls:
    for s in walls:
      window.gridview.toggleBarrier(s)

  if speed < 0:
    for _ in range(0, speed, -1):
      print(f'speed slow')
      window.simSlower()
  elif speed > 0:
    for _ in range(speed):
      print(f'speed fast')
      window.simFaster()

  gMainloop()


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-w", "--width", help="Gridworld width (in cells).",
                      default=16, type=int)
  parser.add_argument("-ht", "--height", help="Gridworld height (in cells).",
                      default=16, type=int)
  parser.add_argument("-s", "--start", help="The starting state for the agent.",
                      default=87, type=int)
  parser.add_argument("-g", "--goal", help="The the goal state.", default=15,
                      type=int)
  parser.add_argument("-sz", "--size",
                      help="The size of each grid cell in pixels.",
                      default=30, type=int)
  parser.add_argument("-sp", "--speed",
                      help=("The starting speed of the simulation relative "
                            "to the default speed (default=0)."),
                      default=0, type=int)
  parser.add_argument("-a", "--agent",
                      help=(f"The agent class to run. "
                            f"Options are: {list(AGENT_CLASSES.keys())}."),
                      default="Dyna", type=str)
  parser.add_argument("--alpha", help="The agent step size.", default=0.5,
                      type=float)
  parser.add_argument("--epsilon",
                      help=("The exploration probability for "
                            "the epsilon-greedy policy."),
                      default=0.05, type=float)
  parser.add_argument("--trace_decay",
                      help=("The eligibility trace decay rate. For agents "
                            "without traces, this argument has no effect."),
                      default=0.8, type=float)
  parser.add_argument("--walls",
                      nargs='+', default=[], type=int,
                      help=("A list of locations to place barriers "
                            "in the gridworld."))
  args = parser.parse_args()

  print(args.walls)

  runObjDemo(width=args.width, height=args.height, start_state=args.start,
             goal_state=args.goal, square_size=args.size, speed=args.speed,
             agent_class=AGENT_CLASSES[args.agent], alpha=args.alpha,
             epsilon=args.epsilon, lambda_=args.trace_decay, walls=args.walls)


if __name__ == '__main__':
  main()
