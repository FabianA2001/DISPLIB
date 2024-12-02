from access_file import Operation
from ortools.sat.python import cp_model
from access_file import save_result


class Solver:
    def __init__(self, trains, timeslots, graphes) -> None:
        # vars sind : list[list[list[bool]]]
        #             time  train operation
        #             immer der Index
        self.vars = []
        self.trains: list[list[Operation]] = trains
        self.graphes = graphes
        self.model = cp_model.CpModel()
        for time in range(timeslots):
            slot = []
            for i, train in enumerate(trains):
                train_slot = []
                for op in range(len(train)):
                    train_slot.append(self.model.new_bool_var(
                        f"train{i}:op{op} ({time})"))
                slot.append(train_slot)
            self.vars.append(slot)
    
    def big_H(self,a, b):
        if (a<=b):
            return 0
        else:
            return 1

    def setObjective(self):
        opdelay=0
        for t,timeslot in enumerate(self.vars):
            for train,time in zip(self.trains,timeslot):
                for op,var in zip(train,time):
                    opdelay+= (op.coeff*max(0,t-op.threshold)+ op.increment*self.big_H(t,op.threshold))*var
        self.model.minimize(opdelay)

    def print(self):
        for i, trains in enumerate(self.vars):
            print(f"timeslot {i}")
            for y, train in enumerate(trains):
                print(f"\ttrain {y}:")
                print("\t\t" + str(train))

    def solve(self):
        solver = cp_model.CpSolver()
        self.setObjective()
        solver.solve(self.model)

        save_result(solver,self.vars)

