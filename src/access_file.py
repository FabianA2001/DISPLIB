import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict


class Resource:
    def __init__(self, name: str, release_time: int = 0) -> None:
        self.name: str = name
        self.release__time: int = release_time

    def __repr__(self) -> str:
        return self.name + " " + str(self.release__time)
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Resource):
            return NotImplemented
        return (self.name == other.name)


class Operation:
    def __init__(self, min_dur: int = -1, low_bound: int = -1, upper_bound: int = -1, res: list[Resource] = [], successors: list[int] = [], threshold: int = 0, coeff: int = 0, increment: int = 0) -> None:
        # -1 -> not set
        self.minimal_duration: int = min_dur
        self.lower_bound: int = low_bound
        self.upper_bound: int = upper_bound
        self.resources: list[Resource] = res
        self.succesors: list[int] = successors
        self.threshold: int = threshold
        self.coeff: int = coeff
        self.increment: int = increment

    def __repr__(self) -> str:
        return f"\"dur: {self.minimal_duration}, suc: {self.succesors}, res: {self.resources}, start: {self.lower_bound},end: {self.upper_bound}, coeff: {self.coeff}, thres: {self.threshold}, incre: {self.increment}\""

# Die erste Zahl in Key gibt den Train an, die Zweite zahl die Operation


# TODO lower bound


def get_operations(path: str) -> list[list[Operation]]:
    result: list[list[Operation]] = []
    with open(path, "r") as file:
        data = json.load(file)
        trains = data["trains"]
        for train_index in trains:
            trains_list = []
            for operation in train_index:
                op = Operation()
                key = "start_ub"
                if key in operation:
                    op.upper_bound = operation[key]
                key = "min_duration"
                if key in operation:
                    op.minimal_duration = operation[key]
                key = "successors"
                if key in operation:
                    op.succesors = operation[key]
                op.resources = []
                key = "resources"
                if key in operation:
                    for res in operation[key]:
                        resurce = Resource(res["resource"])
                        key = "release_time"
                        if key in res:
                            resurce.release__time = res[key]
                        op.resources.append(resurce)
                trains_list.append(op)
            result.append(trains_list)

        objektives = data["objective"]
        for obj in objektives:
            train_index = obj["train"]
            ob_index = obj["operation"]
            op: Operation = result[train_index][ob_index]
            op.threshold = obj["threshold"]
            op.coeff = obj["coeff"]

    return result


def big_H(a, b):
    if (a <= b):
        return 0
    else:
        return 1


def save_result(solver, vars, max_operatins: list, trainss, resources: list):
    events = []
    opdelay = 0
    resource_graphes = timeslot_resource_graphes(
        solver, vars, trainss, resources)
    used_timeslots = []
    for time_index, timeslot in enumerate(vars):
        for train_index, train in enumerate(timeslot):
            for operation_index, operation in enumerate(train):
                if solver.Value(operation):

                    op = trainss[train_index][operation_index]
                    if time_index == 0:
                        opdelay += (op.coeff*max(0, time_index-op.threshold) +
                                    op.increment*big_H(time_index, op.threshold))
                        event = {"time": time_index, "train": train_index,
                                 "operation": operation_index}
                        events.append(event)

                    elif not solver.Value(vars[time_index-1][train_index][operation_index]):
                        if max_operatins[train_index] >= operation_index:
                            opdelay += (op.coeff*max(0, time_index-1-op.threshold) +
                                        op.increment*big_H(time_index-1, op.threshold))
                            event = {"time": time_index-1, "train": train_index,
                                     "operation": operation_index}
                            if time_index != 0 and time_index not in used_timeslots:
                                used_timeslots.append(time_index)

                            events.append(event)
                        if max_operatins[train_index] == operation_index:
                            max_operatins[train_index] = 0
    for time in used_timeslots:
        graph = resource_graphes[time-1]
        time_events = [event for event in events if event["time"] == time-1]
        print(time)
        for event in time_events:
            print(event)
        if len(time_events) > 1 and time>1:
            events = sort_events(events, time_events, graph)
            print("-")
            for event in time_events:
                print(event)
    data = {
        "objective_value": opdelay,
        "events": events
    }
    # JSON-Datei erstellen
    with open('solution.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)


def timeslot_resource_graphes(solver, vars, trains, resources: list):
    slot_graphes = []
    resource_names = []
    nothing = Resource("nothing")
    for resource in resources:
        resource_names.append(resource.name)
    for slot in range(len(vars)-1):
        slot_graphes.append(nx.DiGraph())
        slot_graphes[slot].add_nodes_from(resource_names)
        slot_graphes[slot].add_node("nothing")
        for train in range(len(trains)):
            resources_now = []
            resources_next = []
            op_now = 0
            op_next = 0
            for operation in range(len(trains[train])):
                if solver.value(vars[slot][train][operation]) == 1:
                    resources_now += trains[train][operation].resources
                    op_now = operation
                if solver.value(vars[slot+1][train][operation]) == 1:
                    resources_next += trains[train][operation].resources
                    op_next = operation
            if resources_now == []:
                nothing = Resource("nothing" + str(train))
                resources_now = [nothing]
            for now in resources_now:
                if resources_next == []:
                    nothing = Resource("nothing" + str(train))
                    resources_next = [nothing]
                for next in resources_next:
                    if now != next:
                        slot_graphes[slot].add_edge(next.name, now.name, x=(
                            train, op_now, op_next))
        if len(list(nx.simple_cycles(slot_graphes[slot]))) > 0:
            raise Exception("Please activate cycle constraints")
    return slot_graphes


def sort_events(events, time_events, graph):
    plt.clf()
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, with_labels=True, node_color='skyblue',
            node_size=300, font_size=9, font_weight='bold')
    edge_labels = nx.get_edge_attributes(graph, "x")
    nx.draw_networkx_edge_labels(graph, pos, edge_labels = edge_labels)
    plt.savefig("graphen/resourcen.png")
    before = []
    after = []
    flag_after = False
    sorted_time_events = []
    for event in events:
        if (event not in time_events and flag_after == False) or event["operation"] == 0:
            before.append(event)
        elif event not in time_events and flag_after == True:
            after.append(event)
        else:
            flag_after = True

    while graph.edges:
        path = nx.dag_longest_path(graph)
        for start in range(len(path)-1):
            edge_x = graph[path[start]][path[start+1]]
            sorted_time_events += [event for event in time_events if event["train"] == edge_x["x"][0]
                                   and event["operation"] == edge_x["x"][2]]
            graph.remove_edge(path[start], path[start+1])
    for event in time_events:
        if event not in sorted_time_events:
            sorted_time_events.append(event)

    return before + sorted_time_events + after
