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


def get_resources(train):
    resources = []
    for op in train:
        for res in op.resources:
            if res not in resources:
                resources.append(res)
    return resources


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


    print("number of timeslots: ", clac_maxtime(trains))
    print("number of trains: ", len(trains))
    op_num = 0
    resources = []
    path_lengths = 0
    highest_length = (0, [-1])
    most_resources = (0, [-1])
    most_operations = (0, [-1])
    for trainnr, graph in enumerate(graphes):
        train = trains[trainnr]
        op_num += len(train)
        if len(train) > most_operations[0]:
            most_operations = (len(train), [trainnr])
        elif len(train) == most_operations[0]:
            most_operations[1].append(trainnr)
        train_res = get_resources(train)
        resources += train_res
        if len(train_res) > most_resources[0]:
            most_resources = (len(train_res), [trainnr])
        elif len(train_res) == most_resources[0]:
            most_resources[1].append(trainnr)
        length = nx.shortest_path_length(graph, 0, len(train)-1)
        if length > highest_length[0]:
            highest_length = (length, [trainnr])
        elif length == highest_length[0]:
            highest_length[1].append(trainnr)
        path_lengths += length
    op_num = op_num/len(trains)
    print("average number of operations per train: ", op_num)
    print("average number of resources per train: ", len(resources)/len(trains))
    resources = set(resources)
    print("number of resouces: ", len(resources))
    print("average shortest path needs ", path_lengths/len(trains), " operations")
    print("-----------------")
    print("train(s) with most operations have ", most_operations[0], ":")
    for i in most_operations[1]:
        print(i)
    print("train(s) with most resources need ", most_resources[0], ":")
    for i in most_resources[1]:
        print(i)
    print("train(s) with longest shortest paths need at least", highest_length[0], " operations:")
    for i in highest_length[1]:
        print(i)
