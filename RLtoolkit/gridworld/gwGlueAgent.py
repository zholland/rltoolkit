""" This is gridworld code for use standalone, with or without display onto 
an arbitrary gview, or in conjunction with the standard RL interface.  For standalone use with a display, a simple gridworldwindow is provided.

There are three main objects:
   Gridworld          Just the environment with no graphics stuff
   Gridworldview     A gridworld with view (graphics related stuff)
   Gridworldwindow   A gridworldview that happens to be a window

The walls are stateaction pairs which leave you in the same square rather than taking you to your neighboring square.  If there were no walls, wraparound would occur at the gridworld edges# we start with walls all around the edges.

The barriers (squares you can't pass into) are overlaid on top of this.

The goal square is a terminal state.  Reward is +1 for reaching the goal, 0 else.
"""

from RLtoolkit.utilities import egreedy

from random import *
from math import *

import numpy as np

changeDiff = 0.0001  # difference in Q values needed to notice change


###

class GridAgent:
    def __init__(self, numactions, numstates, epsilon=0, alpha=0.5,
                 gamma=.9, initialvalue=0.1, agentlambda=0.8, *args, **kwargs):
        self.alpha = alpha
        self.initialvalue = initialvalue
        self.gamma = gamma
        self.epsilon = epsilon
        self.agentlambda = agentlambda
        self.numactions = numactions
        self.numstates = numstates
        self.Q = None
        self.changedstates = None
        self.recentsensations = None
        self.recentactions = None
        self.z = None
        self.v_old = None

    def agentchangestate(self, s):
        if s not in self.changedstates:
            self.changedstates.append(s)

    def agent_init(self):
        self.Q = (np.zeros((self.numstates, self.numactions))
                  + self.initialvalue)
        self.z = np.zeros((self.numstates, self.numactions))
        self.v_old = 0
        self.changedstates = []
        self.recentsensations = []
        self.recentactions = []

    def agent_start(self, state):
        self.recentsensations = [state]

        a = self.policy(state)
        self.recentactions = [a]

        return a

    def actionvalues(self, s):
        return [self.Q[s][a] for a in range(self.numactions)]

    def statevalue(self, s):
        if s is None:
            return 0
        elif s == 'terminal':
            return 0
        else:
            return max(self.actionvalues(s))

    def policy(self, state):
        return egreedy(self.epsilon, self.numactions, self.actionvalues(state))

    def agentChoose(self, sprime):  # epsilon greedy
        self.recentsensations = [sprime] + self.recentsensations
        if sprime != 'terminal':
            self.recentactions = [self.policy(sprime)] + self.recentactions
            return self.recentactions[0]

    def agent_learn(self, s, a, r, sp=None, verbose=False):
        next_val = 0 if sp is None else self.gamma * self.statevalue(sp)
        self.Q[s][a] += self.alpha * (r + next_val - self.Q[s][a])

    def agent_step(self, reward, sprime, verbose=False):  # default is one
        # step q
        s = self.recentsensations[0]
        a = self.recentactions[0]

        self.agent_learn(s, a, reward, sprime, verbose)

        return self.agentChoose(sprime)

    def agent_end(self, reward, verbose=False):
        s = self.recentsensations[0]
        a = self.recentactions[0]

        self.agent_learn(s, a, reward, verbose=verbose)


class SarsaGridAgent(GridAgent):

    def agent_learn(self, s, a, r, sp=None):
        oldq = self.Q[s][a]

        if sp is not None:
            ap = self.agentChoose(sp)
            next_val = self.gamma * self.Q[sp][ap]
        else:
            next_val = 0
            ap = None

        self.Q[s][a] += self.alpha * (r + next_val - oldq)

        if abs(self.Q[s][a] - oldq) > changeDiff:
            self.agentchangestate(s)

        return ap

    def agent_step(self, reward, sprime):
        s = self.recentsensations[0]
        a = self.recentactions[0]

        return self.agent_learn(s, a, reward, sprime)

    def agent_end(self, reward):
        s = self.recentsensations[0]
        a = self.recentactions[0]

        self.agent_learn(s, a, reward)


class SarsaLambdaGridAgent(SarsaGridAgent):
    """Replacing traces"""

    def agent_learn(self, s, a, r, sp=None):
        if sp is not None:
            ap = self.agentChoose(sp)
            next_val = self.gamma * self.Q[sp][ap]
        else:
            next_val = 0
            ap = None

        alpha_delta = self.alpha * (r + next_val - self.Q[s][a])

        trace = 1
        i = 0
        while trace > 0.01 and i < len(self.recentactions):
            s = self.recentsensations[i]
            a = self.recentactions[i]
            if s not in self.recentsensations[0:i]:
                oldq = self.Q[s][a]
                self.Q[s][a] += alpha_delta * trace

                if abs(self.Q[s][a] - oldq) > changeDiff:
                    self.agentchangestate(s)
            trace = trace * self.gamma * self.agentlambda
            i += 1

        return ap


class QlambdaGridAgent(GridAgent):
    """accumulating traces, greedy target policy"""

    def agent_learn(self, s, a, r, sp=None, verbose=False):
        phi = np.zeros_like(self.Q, dtype=np.bool)
        phi[s][a] += True

        if np.max(self.Q[s]) == self.Q[s][a]:  # use traces if action was greedy
            self.z *= self.gamma * self.agentlambda
        else:
            self.z *= 0

        self.z += phi

        next_val = 0 if sp is None else self.gamma * np.max(self.Q[sp])
        oldq = np.copy(self.Q)
        self.Q += self.alpha * (r + next_val - self.Q[s][a]) * self.z

        if verbose:
            print(s, r, r + next_val - self.Q[s][a], self.actionvalues(s))
            if sp is None:
                print("Terminal Reward: {}".format(r))
                try:
                    print("Max Avg: {}".format(self.max_avg_reward))
                    print("Current Avg: {}".format(self.task_agent.avg_reward))
                except AttributeError:
                    pass

        changed_states = set(np.where(np.abs(self.Q - oldq) > changeDiff)[0])
        self.changedstates = list(changed_states.union(set(self.changedstates)))


class QonestepGridAgent(GridAgent):
    def agent_learn(self, s, a, r, sp=None):  # onestep qLearning
        oldq = self.Q[s][a]

        next_val = 0 if sp is None else self.gamma * self.statevalue(sp)

        self.Q[s][a] += self.alpha * (r + next_val - self.Q[s][a])
        if abs(self.Q[s][a] - oldq) > changeDiff:
            self.agentchangestate(s)


class ABQ(GridAgent):
    def agent_learn(self, s, a, r, sp=None):
        phi = np.zeros_like(self.Q)
        phi[s][a] += 1
        phi_prime = None
        if sp is not None:
            phi_prime = np.zeros_like(self.Q)
            phi_prime[s][a] += 1

        self.z *= self.gamma * self.agentlambda
        self.z += phi

        next_val = 0 if sp is None else self.gamma * np.max(self.Q[s])
        oldq = np.copy(self.Q)
        self.Q += self.alpha * (r + next_val - self.Q[s][a]) * self.z

        changed_states = set(
            np.where(np.abs(self.Q - oldq) > changeDiff)[0])
        self.changedstates = list(
            changed_states.union(set(self.changedstates)))


### Forward Models

class DeterministicForwardModel:
    def __init__(self, numactions, numstates, initialvalue=0.1):
        self.numactions = numactions
        self.numstates = numstates
        self.initialvalue = initialvalue
        self.predictedreward = None
        self.predictednextstate = None
        self.savedpredictednextstate = None
        self.savedpredictedreward = None
        self.q = None

    def agent_init(self):
        self.predictedreward = [[None for _ in range(self.numactions)]
                                for _ in range(self.numstates)]
        self.predictednextstate = [[None for _ in range(self.numactions)]
                                   for _ in range(self.numstates)]
        self.savedpredictednextstate = [[None for _ in range(self.numactions)]
                                        for _ in range(self.numstates)]
        self.savedpredictedreward = [[None for _ in range(self.numactions)]
                                     for _ in range(self.numstates)]
        self.q = [[self.initialvalue for _ in range(self.numactions)]
                  for _ in range(self.numstates)]

    def learnworldmodel(self, x, a, y, r):
        self.setpredictednextstate(x, a, y)
        self.setpredictedreward(x, a, r)

    def setpredictednextstate(self, x, a, y):
        self.predictednextstate[x][a] = y

    def setpredictedreward(self, x, a, r):
        self.predictedreward[x][a] = r

    def getpredictednextstate(self, x, a):
        return self.predictednextstate[x][a]

    def getpredictedreward(self, x, a):
        return self.predictedreward[x][a]


def setupEmptyGridModel(glue):
    agent = glue.agent
    env = glue.environment
    saveModel(agent)
    for x in range(agent.numstates):
        for a in range(agent.numactions):
            agent.setpredictednextstate(x, a, env.neighboringSquare(x, a))
            agent.setpredictedreward(x, a, 0)


def revealGoalLocation(glue):
    agent = glue.agent
    env = glue.environment
    for x in range(agent.numstates):
        for a in range(agent.numactions):
            s = env.neighboringSquare(x, a)
            if s == env.goalsquare:
                agent.setpredictedreward(x, a, 1)
                agent.setpredictednextstate(x, a, 'terminal')


def setupAccurateModel(glue):
    agent = glue.agent
    saveModel(agent)
    for x in range(agent.numstates):
        for a in range(agent.numactions):
            sp = glue.environment.gridworldnextstate(x, a)
            agent.setpredictednextstate(x, a, sp)
            if sp == 'terminal':
                r = 1
            else:
                r = 0
            agent.setpredictedreward(x, a, r)


def setupNullModel(glue):
    agent = glue.agent
    saveModel(agent)
    for x in range(agent.numstates):
        for a in range(agent.numactions):
            agent.setpredictednextstate(x, a, None)  # 0 ?


def setupStayModel(agent):
    saveModel(agent)
    for x in range(agent.numstates):
        for a in range(agent.numactions):
            agent.setpredictednextstate(x, a, x)
            agent.setpredictedreward(x, a, 0)


def saveModel(agent):
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            agent.savedpredictednextstate[s][a] = agent.predictednextstate[s][a]
            agent.savedpredictedreward[s][a] = agent.predictedreward[s][a]


def saveModelAndQ(agent):
    saveModel(agent)
    saveQ(agent)


def restoreModelAndQ(agent):
    restoreModel(agent)
    restoreQ(agent)


def restoreModel(agent):
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            agent.predictednextstate[s][a] = agent.savedpredictednextstate[s][a]


def qLearn(agent, s, a, sprime, r):
    if r is None:
        r = 0
    td_error = (r + (agent.gamma * agent.statevalue(sprime)) - agent.Q[s][a])
    agent.Q[s][a] += agent.alpha * td_error


class DynaGridAgent(DeterministicForwardModel, GridAgent):
    def __init__(self, numactions, numstates, epsilon=0.05, alpha=0.5,
                 gamma=.9, initialvalue=0.1, agentlambda=0.8,
                 expbonus=0.0):  # .0001
        GridAgent.__init__(self, numactions, numstates, epsilon, alpha,
                           gamma, initialvalue, agentlambda)
        self.agenttime = None
        self.nummodelsteps = None
        self.explorationbonus = None
        self.Q = None
        self.savedQ = None
        self.predictednextstate = None
        self.predictedreward = None
        self.savedpredictednextstate = None
        self.savedpredictedreward = None
        self.changedstates = None
        self.agenttime = 0
        self.nummodelsteps = 20
        self.explorationbonus = expbonus
        self.timeoflasttry = None

    def agent_init(self):
        # num states and numactions should be set by call to DynaGridAgent
        self.Q = [[self.initialvalue for _ in range(self.numactions)]
                  for _ in range(self.numstates)]
        self.savedQ = [[self.initialvalue for _ in range(self.numactions)]
                       for _ in range(self.numstates)]
        self.predictednextstate = [[None for _ in range(self.numactions)]
                                   for _ in range(self.numstates)]
        self.predictedreward = [[None for _ in range(self.numactions)]
                                for _ in range(self.numstates)]
        self.savedpredictednextstate = [[None for _ in range(self.numactions)]
                                        for _ in range(self.numstates)]
        self.savedpredictedreward = [[None for _ in range(self.numactions)]
                                     for _ in range(self.numstates)]
        self.changedstates = list(range(self.numstates))
        self.timeoflasttry = [[0 for _ in range(self.numactions)]
                              for _ in range(self.numstates)]
        setupStayModel(self)

    def learn_model(self, x, a, y, r):
        self.learnworldmodel(x, a, y, r)
        self.agenttime += 1
        self.timeoflasttry[x][a] = self.agenttime

    def explore_reward(self, r, s, a):
        x = self.explorationbonus
        x *= sqrt(self.agenttime - self.timeoflasttry[s][a])

        return r + x

    def agent_step(self, reward, sprime):  # onestep dyna
        s = self.recentsensations[0]
        a = self.recentactions[0]
        qLearn(self, s, a, sprime, reward)
        self.learn_model(s, a, sprime, reward)
        for i in range(self.nummodelsteps):
            for j in range(10 * self.nummodelsteps):
                s = randrange(self.numstates)
                a = randrange(self.numactions)
                sp = self.getpredictednextstate(s, a)
                r = self.getpredictedreward(s, a)
                if r is None:
                    r = 0
                if sp is not None and sp != s:  # sp != s added
                    oldq = self.Q[s][a]
                    r = self.explore_reward(r, s, a)
                    qLearn(self, s, a, sp, r)
                    if abs(self.Q[s][a] - oldq) >= changeDiff:
                        self.agentchangestate(s)
                    break

        return self.agentChoose(sprime)

    def agent_end(self, reward):
        s = self.recentsensations[0]
        a = self.recentactions[0]

        self.Q[s][a] += self.alpha * (reward - self.Q[s][a])

        self.learn_model(s, a, 'terminal', reward)
        for i in range(self.nummodelsteps):
            for j in range(10 * self.nummodelsteps):
                s = randrange(self.numstates)
                a = randrange(self.numactions)
                sp = self.getpredictednextstate(s, a)
                r = self.getpredictedreward(s, a)
                if r is None:
                    r = 0
                if sp is not None and sp != s:
                    oldq = self.Q[s][a]
                    r = self.explore_reward(r, s, a)
                    qLearn(self, s, a, sp, r)
                    if abs(self.Q[s][a] - oldq) >= changeDiff:
                        self.agentchangestate(s)
                    break

class ReducedDynaGridAgent(DynaGridAgent):
    def __init__(self, numactions, numstates, epsilon=0.05, alpha=0.5, \
                 gamma=.9, initialvalue=0.1, agentlambda=0.0, expbonus=0.0):
        DynaGridAgent.__init__(self, numactions, numstates, epsilon, alpha, \
                               gamma, initialvalue, agentlambda, expbonus)
        self.nummodelsteps = 0


class PreloadedDynaGridAgent(DynaGridAgent):
    def __init__(self, numactions, numstates, epsilon=0.05, alpha=0.5, \
                 gamma=.9, initialvalue=0.1, agentlambda=0.0, expbonus=0.0):
        DynaGridAgent.__init__(self, numactions, numstates, epsilon, alpha, \
                               gamma, initialvalue, agentlambda, expbonus)
        self.nummodelsteps = 1000

    def agentInit(self):
        self.timeoflasttry = [[0 for i in range(self.numactions)] \
                              for j in range(self.numstates)]
        setupAccurateModel(self.sim)


def changeAgentLearnMethod(env, newlearn):
    # also need to reset agent before using new method
    print(("Setting up agent with new learning method:", newlearn))
    newagent = None
    if newlearn == 'qlambdareplace':  # Q(lambda), replace traces
        newagent = QlambdaGridAgent(env.numactions(), env.numstates())
    elif newlearn == 'onestepq':  # one step Q learner
        newagent = QonestepGridAgent(env.numactions(), env.numstates())
    elif newlearn == 'onestepdyna':  # one step dyna
        newagent = DynaGridAgent(env.numactions(), env.numstates())
    elif newlearn == 'sarsalambdatraces':  # Sarsa(lambda), replace traces
        newagent = SarsaLambdaGridAgent(env.numactions(), env.numstates())
    elif newlearn == 'sarsa':  # Sarsa(lambda), replace traces
        newagent = SarsaGridAgent(env.numactions(), env.numstates())
    else:
        print(("Error: Learning method requested", newlearn, "not implemented"))

    return newagent


def saveQ(agent):
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            agent.savedQ[s][a] = agent.Q[s][a]


def restoreQ(agent):
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            agent.Q[s][a] = agent.savedQ[s][a]


def avi(agent):
    saveQ(agent)
    keepon = True
    while keepon:
        delta = 0
        for s in range(agent.numstates):
            for a in range(agent.numactions):
                sp = agent.getpredictednextstate(s, a)
                r = agent.getpredictedreward(s, a)
                qtemp = agent.Q[s][a]
                qLearn(agent, s, a, sp, r)
                delta = max(delta, abs(qtemp - agent.Q[s][a]))
        if delta < 0.0001:
            keepon = False


## Value Iteration
def vi1(agent):
    saveQ(agent)
    for s in range(agent.numstates):
        agent.Q[s][0] = max(
            [agent.savedQ[s][a] for a in range(agent.numactions)])
    saveQ(agent)
    for s in range(agent.numstates):
        values = []
        for a in range(agent.numactions):
            sp = agent.getpredictednextstate(s, a)
            r = agent.getpredictedreward(s, a)
            if r is None:
                r = 0
            if sp is None or sp == 'terminal':
                spq = 0
            else:
                spq = agent.savedQ[sp][0]
            values.append(r + (agent.gamma * spq))
        mx = max(values)
        for a in range(agent.numactions):
            v = values[a]
            if v == mx:
                agent.Q[s][a] = v
            else:
                agent.Q[s][a] = 0


def ape(agent=None):
    saveQ(agent)
    delta = 0
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            sp = agent.getpredictednextstate(s, a)
            r = agent.getpredictedreward(s, a)
            qtemp = agent.Q[s][a]
            ap = agent.policy(sp)
            agent.Q[s][a] = r + (agent.gamma * agent.savedQ[sp][ap])
            delta = max(delta, abs(qtemp - agent.Q[s][a]))
    return delta < 0.0001


def aperandom(agent=None):
    saveQ(agent)
    delta = 0
    for s in range(agent.numstates):
        for a in range(agent.numactions):
            sp = agent.getpredictednextstate(s, a)
            r = agent.getpredictedreward(s, a)
            qtemp = agent.Q[s][a]
            ap = agent.policy(sp)
            if sp == 'terminal':
                newq = 0
            else:
                newq = 0
                for ap in range(agent.numactions):
                    newq += agent.savedQ[sp][ap]
                newq = float(newq) / agent.numactions
            agent.Q[s][a] = r + (agent.gamma * newq)
            delta = max(delta, abs(qtemp - agent.Q[s][a]))
    return delta < 0.0001


def resetParameters(agent=None, alpha=None, gamma=None, epsilon=None,
                    agentlambda=None, \
                    explorationbonus=None, initialvalue=None):
    "Changes agent's parameters"
    if alpha is not None:
        agent.alpha = alpha
    if gamma is not None:
        agent.gamma = gamma
    if epsilon is not None:
        agent.epsilon = epsilon
    if agentlambda is not None:
        agent.agentlambda = agentlambda
    if isinstance(agent, DynaGridAgent):
        if explorationbonus is not None:
            agent.explorationbonus = explorationbonus
        if initialvalue is not None:
            agent.initialvalue = initialvalue
            # how about num model steps too?