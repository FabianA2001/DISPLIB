import json
from typing import Dict


class Resource:
    def __init__(self, name: str, release_time: int = -1) -> None:
        self.name: str = name
        self.release__time: int = release_time

    def __repr__(self) -> str:
        return self.name


class Operation:
    def __init__(self, min_dur: int = -1, low_bound: int = -1, upper_bound: int = -1, res: list[Resource] = [], successors: list[int] = []) -> None:
        # -1 -> not set
        self.minimal_duration: int = min_dur
        self.lower_bound: int = low_bound
        self.upper_bound: int = upper_bound
        self.resources: list[Resource] = res
        self.succesors: list[int] = successors

    def __repr__(self) -> str:
        return f"\"dur: {self.minimal_duration}, suc: {self.succesors}, res: {self.resources}\""

# Die erste Zahl in Key gibt den Train an, die Zweite zahl die Operation


def get_operations(path: str) -> Dict[tuple[int, int], Operation]:
    result: Dict[tuple[int, int], Operation] = {}
    with open(path, "r") as file:
        data = json.load(file)
        trains = data["trains"]
        for i, train in enumerate(trains):
            for y, operation in enumerate(train):
                op = Operation()
                key = "start_up"
                if key in operation:
                    op.upper_bound = operation[key]
                key = "min_duration"
                if key in operation:
                    op.minimal_duration = operation[key]
                key = "successors"
                if key in operation:
                    op.succesors = operation[key]
                key = "resources"
                if key in operation:
                    for res in operation[key]:
                        resurce = Resource(res["resource"])
                        key = "release_time"
                        if key in res:
                            resurce.release__time = res[key]
                        op.resources.append(resurce)
                result[(i, y)] = op

    return result
