import numpy as np
import matplotlib.pyplot as plt
import sys
import time
import os
import cPickle as pickle

np.random.seed(7)

if len(sys.argv) != 9:
    print "Wrong number of arguments.\nMAX_TIME, PROB_STAY, INF_TIME, R_VALUE, INC_LIMIT, CONSTRAIN_MOVEMENT, CONSTRAIN_NETWORK, OUT_DIR"
    exit(0)

# User controlled parameters
MAX_TIME = int(sys.argv[1])
PROB_STAY = float(sys.argv[2]) # Default = 0.9
INF_TIME =  int(sys.argv[3])   # Default = 8.0, from CDC avg time til death/removal
R_VALUE =  float(sys.argv[4])  # Default = 2.0, from CDC avg # of people infected by individual
INC_LIMIT = int(sys.argv[5])   # Default = 22 , from CDC time before becoming infected, upper limit
CONSTRAIN_MOVEMENT = (sys.argv[6] == "True")
CONSTRAIN_NETWORK = (sys.argv[7] == "True")
OUT_DIR = sys.argv[8]
try:
    if not os.path.isdir(OUT_DIR):
        os.mkdir(OUT_DIR)
except:
    pass

# Data Lookup Structures
NEIGHBOR_LIST = {}  # (x,y) -> neighbors of (x,y)
NEIGHBOR_LIST_KEYS = set()
NODE_STATS = {}     # (x,y) -> {  "numI": num infected, 
                                # "nonR": num non_removed,
                                # "S": [...],
                                # "E": [...],
                                # "I": [...],
                                # "R": [...]}
                                # "Svec": [...],
                                # "Evec": [...],
                                # "Ivec": [...],
                                # "Rvec": [...] }

# Global Model Params
GRAPH_SIZE = int(np.sqrt(174 - 1))  # sqrt(square area of city) / sqrt(scaling_factor)
NUM_AGENTS = int((1.6 * 10 ** 6))   # population / scaling factor
NUM_NODES = (GRAPH_SIZE + 1) ** 2
CUR_TIME = 0
NUM_INF = 1
NUM_R = 0
NEW_CASES = 1
PROB_LEAVE = 1 - PROB_STAY
R0 = (R_VALUE / INF_TIME)           # Probability of infecting someone per timestep

if not CONSTRAIN_NETWORK:
    EXCLUDE_EDGES = dict()
elif CONSTRAIN_NETWORK:
    EXCLUDE_EDGES = {   (0, 6): (0, 7),     # (x,y) -> [Neighbor to ignore]
                        (0, 7): (0, 6),
                        (1, 6): (1, 7),
                        (1, 7): (1, 6),
                        (2, 6): (2, 7),
                        (2, 7): (2, 6),
                        (3, 6): (3, 7),
                        (3, 7): (3, 6),
                        (4, 6): (4, 7),
                        (4, 7): (4, 6),
                        (5, 6): (5, 7),
                        (5, 7): (5, 6),
                        (6, 0): (7, 0),
                        (7, 0): (6, 0),
                        (6, 1): (7, 1),
                        (7, 1): (6, 1),
                        (6, 2): (7, 2),
                        (7, 2): (6, 2),
                        (6, 3): (7, 3),
                        (7, 3): (6, 3),
                        (6, 4): (7, 4),
                        (7, 4): (6, 4),
                        (6, 5): (7, 5),
                        (7, 5): (6, 5),
                        (6, 8): (7, 8),
                        (7, 8): (6, 8),
                        (6, 9): (7, 9),
                        (7, 9): (6, 9),
                        (6, 10): (7, 10),
                        (7, 10): (6, 10),
                        (6, 11): (7, 11),
                        (7, 11): (6, 11),
                        (6, 12): (7, 12),
                        (7, 12): (6, 12),
                        (6, 13): (7, 13),
                        (7, 13): (6, 13),
                        (8, 6): (8, 7),
                        (8, 7): (8, 6),
                        (9, 6): (9, 7),
                        (9, 7): (9, 6),
                        (10, 6): (10, 7),
                        (10, 7): (10, 6),
                        (11, 6): (11, 7),
                        (11, 7): (11, 6),
                        (12, 6): (12, 7),
                        (12, 7): (12, 6),
                        (13, 6): (13, 7),
                        (13, 7): (13, 6)}
EXCLUDE_EDGES_KEYS = set(EXCLUDE_EDGES.keys())


class Agent(object):
    """ An agent in the Ebola model. """

    def __init__(self, pos, state):
        self.pos = pos
        self.state = state
        self.exposed_time = None
        self.infected_time = None
        self.INC_TIME = np.random.randint(2, INC_LIMIT)
        self.neighbors = self.find_neighbors()
       
        # Update stats
        if state == "I":
            NODE_STATS[self.pos]["numI"] += 1
            self.infected_time = CUR_TIME
        if state != "R":
            NODE_STATS[self.pos]["nonR"] += 1

        if self.state is "S":
            NODE_STATS[self.pos]["S"] += 1
        if self.state is "I":
            NODE_STATS[self.pos]["I"] += 1

    def update_pos(self):
        # Remove self from stats
        if self.state == "I":
            NODE_STATS[self.pos]["numI"] -= 1
            NODE_STATS[self.pos]["I"] -= 1
        if self.state == "S":
            NODE_STATS[self.pos]["S"] -= 1
        if self.state == "R":
            NODE_STATS[self.pos]["R"] -= 1
        if self.state == "E":
            NODE_STATS[self.pos]["E"] -= 1
        if self.state != "R":
            NODE_STATS[self.pos]["nonR"] -= 1

        # Move to a neighboring position
        num_neighbors = len(self.neighbors) - 1
        if CONSTRAIN_MOVEMENT and self.state == "I":
            probability_dist = [PROB_STAY]
            for i in xrange(num_neighbors):
                probability_dist.append(PROB_LEAVE / num_neighbors)
            idx = np.random.choice(xrange(len(self.neighbors)), p=probability_dist)
            self.pos = self.neighbors[idx]
        else:
            self.pos = self.neighbors[np.random.randint(num_neighbors + 1)]

        # Add self to stats
        if self.state == "I":
            NODE_STATS[self.pos]["numI"] += 1
            NODE_STATS[self.pos]["I"] += 1
        if self.state != "R":
            NODE_STATS[self.pos]["nonR"] += 1
        if self.state == "S":
            NODE_STATS[self.pos]["S"] += 1
        if self.state == "R":
            NODE_STATS[self.pos]["R"] += 1
        if self.state == "E":
            NODE_STATS[self.pos]["E"] += 1

        # New neighbors
        self.neighbors = self.find_neighbors()

    def update_state(self):
        """ Updates the state of an Agent according to set rules. """
        global NUM_INF
        global NUM_R
        global NEW_CASES
        global NODE_STATS

        if self.state == "S":
            z = np.random.random()
            if z < (NODE_STATS[self.pos]["numI"] / NODE_STATS[self.pos]["nonR"]) * R0:
                self.state = "E"
                self.exposed_time = CUR_TIME
                NODE_STATS[self.pos]["S"] -= 1
                NODE_STATS[self.pos]["E"] += 1

        elif self.state == "E":
            if (CUR_TIME - self.exposed_time) >= self.INC_TIME:
                self.state = "I"
                self.infected_time = CUR_TIME
                NUM_INF += 1
                NODE_STATS[self.pos]["E"] -= 1
                NODE_STATS[self.pos]["I"] += 1
        elif self.state == "I":
            if (CUR_TIME - self.infected_time) >= INF_TIME:
                self.state = "R"
                NUM_R += 1
                NUM_INF -= 1
                NEW_CASES += 1
                NODE_STATS[self.pos]["I"] -= 1
                NODE_STATS[self.pos]["R"] += 1

    def find_neighbors(self):
        """ Returns a list of neighbors for this position on the graph. Attempts
            to load precomputed neighbors. """
        global NEIGHBOR_LIST
        global NEIGHBOR_LIST_KEYS
        if self.pos in NEIGHBOR_LIST_KEYS:
            return NEIGHBOR_LIST[self.pos]
        else:
            n = [self.pos]
            # Adds +1 and -1 to x and y separately
            for d in [-1, 1]:
                for idx in [0, 1]:
                    if idx == 0:
                        xy = (self.pos[0] + d, self.pos[1])
                    else:
                        xy = (self.pos[0], self.pos[1] + d)
                    x1, y1 = xy
                    # True if this neighbor should be excluded
                    exclude_neighbor = (self.pos in EXCLUDE_EDGES_KEYS) and ((x1, y1) == EXCLUDE_EDGES[self.pos])
                    if not (exclude_neighbor or x1 < 0 or y1 < 0 or x1 > GRAPH_SIZE or y1 > GRAPH_SIZE):
                        n.append((x1, y1))
            NEIGHBOR_LIST[self.pos] = n
            NEIGHBOR_LIST_KEYS.add(self.pos)
            return n

    def __repr__(self):
        return str(self.pos) + str(self.state)


def init_agents():
    agents = []
    agents_per_node = NUM_AGENTS / NUM_NODES
    left_over_agents = NUM_AGENTS % NUM_NODES

    print "agents_per_node", agents_per_node
    print "left_over_agents", left_over_agents

    for x in xrange(GRAPH_SIZE + 1):
        for y in xrange(GRAPH_SIZE + 1):

            if (x, y) not in NODE_STATS.keys():
                NODE_STATS[(x, y)] = {"numI": 0.0, "nonR": 0.0, "S": 0, "I":0, "E":0, "R":0, "Svec":np.zeros(MAX_TIME+1), "Ivec":np.zeros(MAX_TIME+1), "Evec":np.zeros(MAX_TIME+1), "Rvec":np.zeros(MAX_TIME+1) }
            if left_over_agents > 0:
                agents.append(Agent((x, y), "S"))
                left_over_agents -= 1

            for a in xrange(agents_per_node):
                state = "S"
                if x == 0 and y == 0 and a == 0:
                    state = "I"
                agents.append(Agent((x, y), state))

    return agents


def update_nodestats():
    """Keeps track of S, E, I, R counts in a vector over time for each node."""
    global NODE_STATS
    global CUR_TIME

    for pos, subdict in NODE_STATS.iteritems(): # pos = (x, y), subdict = { stats...}
        NODE_STATS[pos]["Rvec"][CUR_TIME] = NODE_STATS[pos]["R"]
        NODE_STATS[pos]["Svec"][CUR_TIME] = NODE_STATS[pos]["S"]
        NODE_STATS[pos]["Evec"][CUR_TIME] = NODE_STATS[pos]["E"]
        NODE_STATS[pos]["Ivec"][CUR_TIME] = NODE_STATS[pos]["I"]

def main():
    """ Primary simulation algorithm. Initializes Agents, then updates state and
        position for a given number of timesteps. """
    global CUR_TIME
    global NEW_CASES

    print "Constrain movement:", CONSTRAIN_MOVEMENT
    print "Constrain network:", CONSTRAIN_NETWORK
    print "Graph size:", GRAPH_SIZE, " Nodes:", NUM_NODES
    print "Num agents:", NUM_AGENTS

    start_time = time.strftime("%Y%m%d_%H%M%S")
    agents = init_agents()

    print "Agents initialized..."

    infected_only = []
    removed_only = []
    infected = []
    new_cases = []


    for t in xrange(MAX_TIME):
        CUR_TIME = t
        new_cases.append(NEW_CASES)
        NEW_CASES = 0
        update_nodestats()
        for a in agents:
            a.update_state()
            a.update_pos()
        print "t =", t, "infected =", NUM_INF + NUM_R
        infected.append(NUM_INF + NUM_R)
        infected_only.append(NUM_INF)
        removed_only.append(NUM_R)
    
    CUR_TIME += 1 # accounts for saving final state of system
    update_nodestats()

    # Save data and summary figures to disk
    NODE_STATS_FILE = open(get_filename(start_time, "NODE_STATS") + ".pkl", "w")
    pickle.dump(NODE_STATS, NODE_STATS_FILE, 2)
    NODE_STATS_FILE.close()

    np.save(get_filename(start_time, "INFECTED_") + ".npy", infected)
    np.save(get_filename(start_time, "INFCONLY_") + ".npy", infected_only)
    plt.plot(xrange(MAX_TIME), infected, color='b', label='Infected + Removed')
    plt.plot(xrange(MAX_TIME), infected_only, color='r', label='Infected')
    plt.ylabel('Number of cases')
    plt.xlabel('Timestep #')
    plt.legend(loc="upper left")
    plt.savefig(get_filename(start_time, "INFECTED_") + ".svg")
    plt.savefig(get_filename(start_time, "INFECTED_") + ".png")
    plt.close()

    plt.plot(xrange(len(new_cases)), new_cases, label='New cases')
    plt.ylabel('Number of cases')
    plt.xlabel('Timestep #')
    plt.legend(loc="upper left")
    plt.savefig(get_filename(start_time, "NEWCASE_") + ".svg")
    plt.savefig(get_filename(start_time, "NEWCASE_") + ".png")
    np.save(get_filename(start_time, "NEWCASE_") + ".npy", new_cases)


def get_filename(timestr, prefix=""):
    """ Returns a filename that incorporates a timestamp and a potential prefix.
        The filename summarizes the parameters of the model. """
    global GRAPH_SIZE
    global OUT_DIR
    global MAX_TIME
    if CONSTRAIN_MOVEMENT:
        const_mov = "True_"
    else:
        const_mov = "False"
    if CONSTRAIN_NETWORK:
        const_net = "True_"
    else:
        const_net = "False"
    return OUT_DIR + "/" + prefix + "size{0:03d}_agents{1}_cm{2}_cn{3}_days{4}_t{5}".format(GRAPH_SIZE, NUM_AGENTS,
                                                                                            const_mov, const_net,
                                                                                            MAX_TIME, timestr)


if __name__ == '__main__':
    main()
