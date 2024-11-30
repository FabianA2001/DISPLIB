from read_file import Operation
from ortools.sat.python import cp_model


class Solver:
    def __init__(self, trains, timeslots, graphes) -> None:
        self.vars = []
        self.trains: list[list[Operation]] = trains
        self.graphes = graphes
        for time in range(timeslots):
            slot = []
            for train in trains:
                train_slot = []
                for op in train:
                    train_slot.append(self.model.new_bool_var(
                        f"train {train}:op {op} ({time})"))
                slot.append(train_slot)
            self.vars.append(slot)

        self.model = cp_model.CpModel()

    def print(self):
        for i, trains in enumerate(self.vars):
            print(f"timeslot {i}")
            for y, train in enumerate(trains):
                print(f"\ttrain {y}:")
                print("\t\t" + str(train))

    def solve(self):
        solver = cp_model.CpSolver()
        solver.solve(self.model)
