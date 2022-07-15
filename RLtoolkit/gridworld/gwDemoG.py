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

from .gwguimain import *
from .gwobject import *
import argparse


def runDemo():
  makeGridworldSimulation(16, 16, 87, 15, 30)
  gMainloop()


def runObjDemo(
    width=16,
    height=16,
    start_state=87,
    goal_state=15,
    square_size=30,
):
  makeObjectGridworldSimulation(w=width,
                                h=height,
                                st=start_state,
                                g=goal_state,
                                size=square_size)
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
  args = parser.parse_args()

  runObjDemo(width=args.width, height=args.height, start_state=args.start,
             goal_state=args.goal, square_size=args.size)


if __name__ == '__main__':
  main()
