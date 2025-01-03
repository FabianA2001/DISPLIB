import json
from typing import Dict


class Resource:
    def __init__(self, name: str, release_time: int = 0) -> None:
        self.name: str = name
        self.release__time: int = release_time

    def __repr__(self) -> str:
        return self.name + " " + str(self.release__time)
        return self.name


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


def save_result(solver, vars, max_operatins: list):
    events = []

    for time_index, timeslot in enumerate(vars):
        for train_index, train in enumerate(timeslot):
            for operation_index, operation in enumerate(train):
                if solver.Value(operation):
                    if time_index == 0 or not solver.Value(vars[time_index-1][train_index][operation_index]):
                        if max_operatins[train_index] >= operation_index:
                            event = {"time": time_index, "train": train_index,
                                     "operation": operation_index}
                            events.append(event)
                        if max_operatins[train_index] == operation_index:
                            max_operatins[train_index] = 0
    data = {
        "objective_value": solver.ObjectiveValue(),
        "events": events
    }
    # JSON-Datei erstellen
    with open('solution.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
