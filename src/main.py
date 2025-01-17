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


def calc_train_length(trains, maxx, FACTOR):
    short_trains = []
    for train in trains:
        train_part = []
        summ = 0
        for op in train:
            ress = 0
            if len(op.resources) >= 1:
                ress = max([res.release__time for res in op.resources])
            summ += max(op.minimal_duration, ress)
            train_part.append(op)
            if summ >= maxx/FACTOR:
                short_trains.append(train_part)
                break

    return short_trains


def calc_new_objective(trains: list[list[Operation]], timeslots):
    train_list = []
    for train in trains:
        old_threshold = train[len(train)-1].threshold
        old_coeff = train[len(train)-1].coeff
        old_increment = train[len(train)-1].increment
        summ = 0
        pos = 0
        for i, op in enumerate(reversed(train)):
            summ += op.minimal_duration
            if summ >= old_threshold-(old_threshold-timeslots):
                pos = i-1
                if old_threshold-timeslots <= 0:
                    pos = 0
                break
        op_list = []
        summ = 0
        for j, op in enumerate(train):
            summ += op.minimal_duration
            if (summ > timeslots) or (op.lower_bound+op.minimal_duration > timeslots):
                break
            op_list.append(op)
            if j > len(train)-pos:
                break
        if op_list != []:
            if old_threshold > timeslots:
                op_list[len(op_list)-1].threshold = timeslots
            op_list[len(op_list)-1].coeff = old_coeff
            op_list[len(op_list)-1].increment = old_increment
            op_list[len(op_list)-1].succesors = []

            train_list.append(op_list)

    return train_list


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
        important_operations: list[Operation] = []
        temp = []
        for op in train:
            temp.append(op)
            if op.threshold != -1:
                for ops in temp:
                    important_operations.append(ops)
                temp = []
        # important_operations[len(important_operations)-1].succesors = []
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

    sol = solver.Solver(trains, 1500, graphes, calc_new_objective(
        trains, 500), clac_maxtime2(important_trains))
    sol.start_time = start_time
    # sol.print()
    sol.solve()
    # sol.print(True)
