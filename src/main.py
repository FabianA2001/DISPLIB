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


def clac_maxtime2(trains):
    maxx = 0
    time_per_train = []
    for train in trains:
        summ = 0
        for op in train:
            ress = 0
            if len(op.resources) >= 1:
                ress = max([res.release__time for res in op.resources])
            summ += max(op.minimal_duration, ress)
        time_per_train.append(summ*2)
        maxx = max(summ, maxx)
    return time_per_train


def get_important_trains(trains: list[list[Operation]]):
    important_trains = []
    for train in trains:
        important_operations = []
        temp = []
        for op in train:
            temp.append(op)
            if op.threshold != -1:
                for ops in temp:
                    important_operations.append(ops)
                temp = []
        important_trains.append(important_operations)

    return important_trains


if __name__ == "__main__":
    path = sys.argv[1]
    print(path)
    trains: list[list[Operation]] = access_file.get_operations(path)
    important_trains = get_important_trains(trains=trains)
    # for i in range(len(important_trains)):
    # print(important_trains[i])

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

    sol = solver.Solver(trains, int(clac_maxtime(
        trains)*3), graphes, important_trains, clac_maxtime2(important_trains))
    sol.start_time = start_time
    # sol.print()
    sol.solve()
    # sol.print(True)
