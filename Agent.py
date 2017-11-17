import numpy as np
import matplotlib.pyplot as plt
import sys
import time
import os


if len(sys.argv) != 9:
    print "ARGS: timesteps prob_stay time_til_death r_value"
    exit(0)

# User controlled parameters
MAX_TIME = int(sys.argv[1])
PROB_STAY = float(sys.argv[2])#0.9
INF_TIME =  int(sys.argv[3])#8.0  # From CDC avg time til death/removal
R_VALUE =  float(sys.argv[4])#2.0  # From CDC avg # of people infected by individual
INC_LIMIT = int(sys.argv[5]) # time before becoming infected, upper limit
CONSTRAIN_MOVEMENT = (sys.argv[6] == True)#False
CONSTRAIN_NETWORK = (sys.argv[7] == True)#False
OUT_DIR = sys.argv[8]
if not os.path.isdir(OUT_DIR):
    os.mkdir(OUT_DIR)

# Data Lookup Structures
NEIGHBOR_LIST = {}  # (x,y) -> neighbors of (x,y)
NEIGHBOR_LIST_KEYS = set()
NODE_STATS = {}  # (x,y) -> {"numI": # infected, "nonR": # non_removed}

# Global Model Params
GRAPH_SIZE = int(np.sqrt(174 - 1))  # sqrt(square area of city) / sqrt(scaling_factor)
NUM_AGENTS = int((1.6 * 10 ** 6))  # population / scaling factor
NUM_NODES = (GRAPH_SIZE + 1) ** 2
CUR_TIME = 0
NUM_INF = 1
NUM_R = 0
NEW_CASES = 1



PROB_LEAVE = 1 - PROB_STAY

R0 = R_VALUE / INF_TIME  # Probability of infecting someone per timestep

if not CONSTRAIN_NETWORK:
    EXCLUDE_EDGES = dict()
elif CONSTRAIN_NETWORK:
    # (x,y) -> [Neighbors to ignore]
    EXCLUDE_EDGES = {(0, 6): (0, 7),
                     (1, 6): (1, 7),
                     (2, 6): (2, 7),
                     (3, 6): (3, 7),
                     (4, 6): (4, 7),
                     (5, 6): (5, 7),
                     (6, 0): (7, 0),
                     (6, 1): (7, 1),
                     (6, 2): (7, 2),
                     (6, 3): (7, 3),
                     (6, 4): (7, 4),
                     (6, 5): (7, 5),
                     (6, 8): (7, 8),
                     (6, 9): (7, 9),
                     (6, 10): (7, 10),
                     (6, 11): (7, 11),
                     (6, 12): (7, 12),
                     (6, 13): (7, 13),
                     (8, 6): (8, 7),
                     (9, 6): (9, 7),
                     (10, 6): (10, 7),
                     (11, 6): (11, 7),
                     (12, 6): (12, 7),
                     (13, 6): (13, 7)}
EXCLUDE_EDGES_KEYS = set(EXCLUDE_EDGES.keys())


class Agent(object):
    """ An agent in the Ebola model. """

    def __init__(self, pos, state):
        self.pos = pos
        self.state = state
        self.exposed_time = None
        self.infected_time = None
        self.INC_TIME = np.random.randint(2, INC_LIMIT)#np.random.randint(2, 21 + 1)  # From WHO incubation time
        self.neighbors = self.find_neighbors()

        # Update stats
        if state == "I":
            NODE_STATS[self.pos]["numI"] += 1
            self.infected_time = CUR_TIME
        if state != "R":
            NODE_STATS[self.pos]["nonR"] += 1

    def update_pos(self):
        # Remove self from stats
        if self.state == "I":
            NODE_STATS[self.pos]["numI"] -= 1
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
        if self.state != "R":
            NODE_STATS[self.pos]["nonR"] += 1

        # New neighbors
        self.neighbors = self.find_neighbors()

    def update_state(self):
        global NUM_INF
        global NUM_R
        global NEW_CASES
        if self.state == "S":
            z = np.random.random()
            if z < (NODE_STATS[self.pos]["numI"] / NODE_STATS[self.pos]["nonR"]) * R0:
                self.state = "E"
                self.exposed_time = CUR_TIME
        elif self.state == "E":
            if (CUR_TIME - self.exposed_time) >= self.INC_TIME:
                self.state = "I"
                self.infected_time = CUR_TIME
                NUM_INF += 1
        elif self.state == "I":
            if (CUR_TIME - self.infected_time) >= INF_TIME:
                self.state = "R"
                NUM_R += 1
                NUM_INF -= 1
                NEW_CASES += 1

    def find_neighbors(self):
        global NEIGHBOR_LIST
        global NEIGHBOR_LIST_KEYS
        if self.pos in NEIGHBOR_LIST_KEYS:
            return NEIGHBOR_LIST[self.pos]
        else:
            n = [self.pos]
            # Add +1 and -1 to x and y separately
            for d in [-1, 1]:
                for idx in [0, 1]:
                    if idx == 0:
                        xy = (self.pos[0] + d, self.pos[1])
                    else:
                        xy = (self.pos[0], self.pos[1] + d)
                    x1, y1 = xy
                    # True if this neighbor should be excluded
                    exclude_neighbor = (self.pos in EXCLUDE_EDGES_KEYS) and ((x1, y1) in EXCLUDE_EDGES[self.pos])
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
                NODE_STATS[(x, y)] = {"numI": 0.0, "nonR": 0.0}
            if left_over_agents > 0:
                agents.append(Agent((x, y), "S"))
                left_over_agents -= 1

            for a in xrange(agents_per_node):
                state = "S"
                if x == 0 and y == 0 and a == 0:
                # if a == 0 or a == 1:              # Adds 2 infected per node
                    state = "I"
                agents.append(Agent((x, y), state))

    return agents


def main():
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
        if t % 7 == 0:
            new_cases.append(NEW_CASES)
            NEW_CASES = 0
        for a in agents:
            a.update_state()
            a.update_pos()
        print "t =", t, "infected =", NUM_INF + NUM_R
        infected.append(NUM_INF + NUM_R)
        infected_only.append(NUM_INF)
        removed_only.append(NUM_R)

    np.save(get_filename(start_time, "INFECTED_") + ".npy", infected)
    np.save(get_filename(start_time, "INFCONLY_") + ".npy", infected_only)
    plt.plot(xrange(MAX_TIME), infected, color='b', label='Infected + Removed')
    plt.plot(xrange(MAX_TIME), infected_only, color='r', label='Infected')
    plt.title("CONSTRAIN_MOVEMENT = " + str(CONSTRAIN_MOVEMENT))
    plt.ylabel('Number of cases')
    plt.xlabel('Day #')
    plt.legend(loc="upper left")
    plt.savefig(get_filename(start_time, "INFECTED_") + ".svg")
    # plt.show()
    plt.close()

    plt.plot(xrange(len(new_cases)), new_cases, label='New cases')
    plt.title("New cases, CONSTRAIN_MOVEMENT =" + str(CONSTRAIN_MOVEMENT))
    plt.ylabel('Number of cases')
    plt.xlabel('Week #')
    plt.legend(loc="upper left")
    plt.savefig(get_filename(start_time, "NEWCASE_") + ".svg")
    np.save(get_filename(start_time, "NEWCASE_") + ".npy", new_cases)
    # plt.show()


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
