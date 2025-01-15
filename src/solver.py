from access_file import Operation
from ortools.sat.python import cp_model
from access_file import save_result
import networkx as nx
import time
import math


class Solver:
    def __init__(self, trains, timeslots, graphes) -> None:
        self.trains: list[list[Operation]] = trains
        self.graphes = graphes
        self.model = cp_model.CpModel()
        self.SCALE_FACTOR: int = 4  # int
        self.MAX_FACTOR: float = 2  # float
        self.timeslots = int((timeslots/self.SCALE_FACTOR)*self.MAX_FACTOR)
        print(f"time slots: {self.timeslots}")
        self.start_time = 0.0

        # vars sind : list[list[list[bool]]]
        #             time  train operation
        #             immer der Index
        self.vars = []

        for time in range(self.timeslots):
            slot = []
            for i, train in enumerate(trains):
                train_slot = []
                for op in range(len(train)):
                    train_slot.append(self.model.new_bool_var(
                        f"train{i}:op{op} ({time})"))
                slot.append(train_slot)
            self.vars.append(slot)

    def print_time(self, name):
        if self.start_time != 0.0:
            elapsed_time = int(time.time() - self.start_time)
            # Print the elapsed time
            print(f"{name} start: {int(elapsed_time/60)}m {elapsed_time % 60}s")

    def big_H(self, a, b):
        if (a <= b):
            return 0
        else:
            return 1

    def setObjective(self):
        # opdelay = 0
        # for t, timeslot in enumerate(self.vars):
        #     for train, time in zip(self.trains, timeslot):
        #         for op, var in zip(train, time):
        #             opdelay += (op.coeff*max(0, t-op.threshold) +
        #                         op.increment*self.big_H(t, op.threshold))*var
        # self.model.minimize(opdelay)

        # eine int varibale erstellen welche nach allen bool variabeln aus der vorigen op waren

        #################################
        # WRONG
        ################################
        opdelay = 0
        for t, timeslot in enumerate(self.vars):
            for train, time in zip(self.trains, timeslot):
                for op, var in zip(train, time):
                    opdelay += t*self.SCALE_FACTOR*var
        self.model.minimize(opdelay)

    def resources(self):
        resources = []
        for train in self.trains:
            for op in train:
                for res in op.resources:
                    if res not in resources:
                        resources.append(res)
        return resources

    def find_resource_cycles(self, solver):
        graph = nx.DiGraph()
        resource_names = []
        for resource in self.resources():
            resource_names.append(resource.name)
        graph.add_nodes_from(resource_names)
        slot_cycles = []
        for slot in range(self.timeslots-1):
            graph.clear_edges()
            for train in range(len(self.trains)):
                resources_now = []
                resources_next = []
                op_now = 0
                op_next = 0
                for operation in range(len(self.trains[train])):
                    if solver.value(self.vars[slot][train][operation]) == 1:
                        resources_now += self.trains[train][operation].resources
                        op_now = operation
                    if solver.value(self.vars[slot+1][train][operation]) == 1:
                        resources_next += self.trains[train][operation].resources
                        op_next = operation
                for now in resources_now:
                    for next in resources_next:
                        if now != next:
                            graph.add_edge(now.name, next.name, x=(
                                train, op_now, op_next))
            cycles = nx.simple_cycles(graph)
            for cycle in cycles:
                critical_operations = []
                for node in range(len(cycle) - 1):
                    critical_operations.append(
                        graph[cycle[node]][cycle[node+1]]["x"])
                critical_operations.append(
                    graph[cycle[len(cycle)-1]][cycle[0]]["x"])
                slot_cycles.append((slot, critical_operations))
        return slot_cycles

    def constraint_always_there(self):
        # At every timeslot, every train has to be in exactly one operation
        for train in range(len(self.trains)):
            for slot in range(0, self.timeslots):
                self.model.add(sum(self.vars[slot][train][op]
                               for op, _ in enumerate(self.trains[train])) <= 1)

        # in 0 slot there can be the start and an other operation
        # messes up the solution
        # bei slot aus der 0 eine 1 machen

        # for train in range(len(self.trains)):
        #     self.model.add(sum(self.vars[0][train][op]
        #                        for op in range(1, len(self.trains[train]))) <= 1)

    def constraint_start_at_start(self):
        # The start operation has to be the first operation
        for train in range(len(self.trains)):
            self.model.add(self.vars[0][train][0] == 1)

    def constraint_operation_length(self):
        # The train can spend 0 timeslots at an operation or at least as many as the operations minimum length
        for train in range(len(self.trains)):
            for op in range(len(self.trains[train])):
                con1 = sum(self.vars[slot][train][op]
                           for slot in range(math.ceil(self.timeslots/self.SCALE_FACTOR))) == 0
                con2 = sum(self.vars[slot][train][op] for slot in range(
                    self.timeslots)) >= math.ceil(self.trains[train][op].minimal_duration/self.SCALE_FACTOR)

                # Define boolean variables
                condition1 = self.model.NewBoolVar('condition1')
                condition2 = self.model.NewBoolVar('condition2')
                # Enforce that exactly one of the conditions must be true
                self.model.Add(condition1 + condition2 == 1)
                self.model.add(con1).only_enforce_if(condition1)
                self.model.add(con2).only_enforce_if(condition2)

    def constraint_end_at_last_op(self):
        # The end has to be the last operation
        for train in range(len(self.trains)):
            last_op = len(self.trains[train]) - 1
            self.model.add(sum(self.vars[slot][train][last_op]
                           for slot in range(self.timeslots)) >= 1)

    def constraint_resource_release(self):
        # Resources can only be used after their release time.
        resources = self.resources()
        ops_per_resource = {res: [] for res in resources}

        for train_idx, train in enumerate(self.trains):
            for op_idx, operation in enumerate(train):
                for resource in operation.resources:
                    ops_per_resource[resource].append(
                        (train_idx, op_idx, operation))

        for time_id in range(self.timeslots):
            for resource, operations in ops_per_resource.items():
                for train_idx, op_idx, operation in operations:
                    release_time = resource.release__time
                    if release_time > 0:
                        is_active = self.vars[time_id][train_idx][op_idx]

                        for t in range(1, (math.ceil(release_time/self.SCALE_FACTOR) + 1)):
                            if time_id + t < self.timeslots:
                                for other_train_idx, other_op_idx, _ in operations:
                                    if (other_train_idx, other_op_idx) != (train_idx, op_idx):
                                        self.model.Add(
                                            self.vars[time_id + t][other_train_idx][other_op_idx] == 0).OnlyEnforceIf(
                                            is_active)

    def constraint_consecutive(self):
        # An operaton has to take place in consecutive timeslots
        # checks for timeslot 1 and up
        for slot in range(1, self.timeslots):
            for train in range(len(self.trains)):
                for op in range(len(self.trains[train])):
                    outcoming_edges = list(self.graphes[train].in_edges(op))
                    target_nodes = [edge[0] for edge in outcoming_edges]
                    # stay in op or come from previous node in graphe
                    summ = sum(self.vars[slot-1][train][i]
                               for i in target_nodes)
                    self.model.add(
                        self.vars[slot-1][train][op] + summ >= self.vars[slot][train][op])

        # checks slot 0
        # assumes op 0 is the start operation in every train

        # müsste inzwischen Egal sein weil wir wieder nur 1 op in jedem Zeitslot erlauben

        # for train in range(len(self.trains)):
        #     outcoming_edges = list(self.graphes[train].out_edges(0))
        #     target_nodes = [edge[1] for edge in outcoming_edges]
        #     target_nodes.append(0)
        #     summ = 0
        #     for op in range(len(self.trains[train])):
        #         if op in target_nodes:
        #             continue
        #         summ += self.vars[0][train][op]
        #     self.model.add(summ == 0)

    def constraint_resource(self):
        # A resource can only be used by one train at a time
        resources = self.resources()
        for slot in range(self.timeslots):
            for res in resources:
                summ = 0
                for index_train, train in enumerate(self.vars[slot]):
                    for index_op, _ in enumerate(train):
                        for res_train in self.trains[index_train][index_op].resources:
                            if res == res_train:
                                summ += self.vars[slot][index_train][index_op]
                self.model.add(summ <= 1)

    def constraint_destroy_cycle(self, cycle):
        self.model.add(sum(self.vars[cycle[0]][cycle[1][t][0]][cycle[1][t][1]] +
                       self.vars[cycle[0]][cycle[1][t][0]][cycle[1][t][1]] for t in range(len(cycle[1])))
                       < 2*len(cycle[1]))

    def constraint_start_upper_bound(self):
        for index_train, train in enumerate(self.trains):
            for index_operation, operatin in enumerate(train):
                if operatin.upper_bound != -1:
                    summ = self.vars[0][index_train][index_operation]
                    for i in range(0, math.ceil(operatin.upper_bound/self.SCALE_FACTOR)):
                        summ += self.vars[i][index_train][index_operation]
                    self.model.add(
                        summ >= 1)

    def constraint_start_lower_bound(self):
        for index_train, train in enumerate(self.trains):
            for index_operation, operatin in enumerate(train):
                if operatin.lower_bound != -1:
                    summ = 0
                    for i in range(0, math.ceil(operatin.lower_bound/self.SCALE_FACTOR)):
                        summ += self.vars[i][index_train][index_operation]
                    self.model.add(
                        summ == 0)

    def print(self, value=False):
        # value erst True setzen wenn gesolvt wurde
        for i, trains in enumerate(self.vars):
            print(f"timeslot {i}")
            for y, train in enumerate(trains):
                print(f"\ttrain {y}:")
                if not value:
                    print("\t\t" + str(train))
                else:
                    print("\t\t", end="")
                    for index_var, var in enumerate(train):
                        print(
                            f"op{index_var}: {self.solver.value(var)}\t", end="")
                    print()

    def max_operations(self):
        max_op = []
        for train in self.trains:
            max_op.append(len(train)-1)
        return max_op

    def solve(self):
        self.print_time("begin model")
        self.solver = cp_model.CpSolver()
        # ohne dieses Zeile ist es nicht Determinstisch
        # self.solver.parameters.num_search_workers = 1
        self.solver.parameters.log_search_progress = True
        self.print_time("objective")
        self.setObjective()
        self.print_time("start")
        self.constraint_start_at_start()
        self.print_time("length")
        self.constraint_operation_length()
        self.print_time("end")
        self.constraint_end_at_last_op()
        self.print_time("consecutive")
        self.constraint_consecutive()
        self.print_time("resource")
        self.constraint_resource()
        self.print_time("upper")
        self.constraint_start_upper_bound()
        self.print_time("lower")
        self.constraint_start_lower_bound()

        self.print_time("always there")
        self.constraint_always_there()

        self.print_time("release")
        self.constraint_resource_release()
        self.print_time("end constraints")

        # 3 ist unmöglich, 4 ist optimal
        status = self.solver.solve(self.model)
        print("Status:", status)
        assert (status == 4)
        print("Orginal objective_value", self.solver.ObjectiveValue())

        # vorläufig deaktiviert da cycles aktuell keine Probleme darstellen
        cycles = self.find_resource_cycles(self.solver)
        while (len(cycles) > 0):
            for cycle in cycles:
                self.constraint_destroy_cycle(cycle)
            status = self.solver.solve(self.model)
            print("Status:", status)
            assert (status == 4)

            cycles = self.find_resource_cycles(self.solver)
        self.print_time("save")
        save_result(self.solver, self.vars, self.trains,
                    self.resources(), self.SCALE_FACTOR)
