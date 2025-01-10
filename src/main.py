import access_file as access_file
from access_file import Operation
import graphe
import solver

import networkx as nx
import matplotlib.pyplot as plt
import sys

import time
# Record the start time
start_time = time.time()


def print_operations(trains):
    for i, train in enumerate(trains):
        print(f"Train {i}:")
        for y, op in enumerate(train):
            print(f"\tOperation {y}: {op}")


def clac_maxtime(trains):
    maxx = 0
    for train in trains:
        summ = 0
        for op in train:
            ress = 0
            if len(op.resources) >= 1:
                ress = max([res.release__time for res in op.resources])
            summ += max(op.minimal_duration, ress)
        maxx = max(summ, maxx)
    return maxx


if __name__ == "__main__":
    path = sys.argv[1]
    print(path)
    trains: list[list[Operation]] = access_file.get_operations(path)
    # print_operations(trains)

    graphes = [graphe.create_graphe(train) for train in trains]
    # list[graph]
    # der index gibt den Zug an
    # für jeden Zug einen Graphen

    for i, train in enumerate(trains):
        plt.clf()
        g = graphes[i]
        nx.draw(g, with_labels=True, node_color='skyblue',
                node_size=300, font_size=9, font_weight='bold')
        plt.savefig(f"graphen/train{i}.png")

    sol = solver.Solver(trains, int(clac_maxtime(trains)*2), graphes)
    sol.start_time = start_time
    # sol.print()
    sol.solve()
    # sol.print(True)
