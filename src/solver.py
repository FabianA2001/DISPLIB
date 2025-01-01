from access_file import Operation
from ortools.sat.python import cp_model
from access_file import save_result
import networkx as nx


class Solver:
    def __init__(self, trains, timeslots, graphes) -> None:
        # vars sind : list[list[list[bool]]]
        #             time  train operation
        #             immer der Index
        self.vars = []
        self.trains: list[list[Operation]] = trains
        self.graphes = graphes
        self.model = cp_model.CpModel()
        self.timeslots = timeslots
        for time in range(timeslots):
            slot = []
            for i, train in enumerate(trains):
                train_slot = []
                for op in range(len(train)):
                    train_slot.append(self.model.new_bool_var(
                        f"train{i}:op{op} ({time})"))
                slot.append(train_slot)
            self.vars.append(slot)

    def big_H(self, a, b):
        if (a <= b):
            return 0
        else:
            return 1

    def setObjective(self):
        opdelay = 0
        for t, timeslot in enumerate(self.vars):
            for train, time in zip(self.trains, timeslot):
                for op, var in zip(train, time):
                    opdelay += (op.coeff*max(0, t-op.threshold) +
                                op.increment*self.big_H(t, op.threshold))*var
        self.model.minimize(opdelay)

    def resources(self):
        resources = []
        for train in self.trains:
            for op in train:
                for res in op.resources:
                    if res.name not in resources:
                        resources.append(res.name)
        return resources

    def find_resource_cycles(self, solver):
        graph = nx.DiGraph()
        graph.add_nodes_from(self.resources())
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
                            graph.add_edge(now, next, x=(
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
            for slot in range(self.timeslots):
                self.model.add(sum(self.vars[slot][train][op]
                               for op, _ in enumerate(self.trains[train])) == 1)

    def constraint_start_at_start(self):
        # The start operation has to be the first operation
        for train in range(len(self.trains)):
            self.model.add(self.vars[0][train][0] == 1)

    def constraint_operation_length(self):
        # The train can spend 0 timeslots at an operation or at least as many as the operations minimum length
        for train in range(len(self.trains)):
            for op in range(len(self.trains[train])):
                con1 = sum(self.vars[slot][train][op]
                           for slot in range(self.timeslots)) == 0
                con2 = sum(self.vars[slot][train][op] for slot in range(
                    self.timeslots)) >= self.trains[train][op].minimal_duration

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
            self.model.add(self.vars[self.timeslots - 1][train][last_op] == 1)

    def constraint_resource_release(self):
        # Resources can only be used after their release time.
        for train_idx, train in enumerate(self.trains):
            for op_idx, operation in enumerate(train):
                if "resources" in operation:
                    for resource in operation.resources:
                        release_time = resource.get("release_time", 0)
                        for slot in range(release_time):
                            self.model.add(
                                self.vars[slot][train_idx][op_idx] == 0)

    def constraint_consecutive(self):
        # An operaton has to take place in consecutive timeslots
        for slot in range(1, self.timeslots):
            for train in range(len(self.trains)):
                for op in range(len(self.trains[train])):
                    incoming_edges = list(self.graphes[train].in_edges(op))
                    source_nodes = [edge[0] for edge in incoming_edges]
                    # stay in op or come from previous node in graphe
                    summ = sum(self.vars[slot-1][train][i]
                               for i in source_nodes)
                    self.model.add(
                        self.vars[slot-1][train][op] + summ >= self.vars[slot][train][op])
                    self.model.add(self.vars[slot-1][train][op] + summ <= 1)

    def constraint_successor(self):
        # The order of the operations for one train has to be a path in the graph
        for train in range(len(self.trains)):
            for op, operation in enumerate(self.trains[train]):
                for successor in operation.succesors:
                    for slot in range(self.timeslots - 1):
                        self.model.add(self.vars[slot][train][op] == 1).OnlyEnforceIf(
                            self.vars[slot + 1][train][successor]
                        )

    def constraint_resource(self):
        # A resource can only be used by one train at a time
        resources = self.resources()
        for slot in range(self.timeslots):
            for res in resources:
                # self.model.add(sum(sum(self.vars[slot][train][op] for op in range(len(
                #     self.trains[train])) if res in self.trains[train][op].resources) for train in range(len(self.trains))))
                summ = 0
                for index_train, train in enumerate(self.vars[slot]):
                    for index_op, _ in enumerate(train):
                        for res_train in self.trains[index_train][index_op].resources:
                            if res == res_train.name:
                                summ += self.vars[slot][index_train][index_op]
                self.model.add(summ <= 1)

    def constraint_destroy_cycle(self, cycle):
        self.model.add(sum(self.vars[cycle[0]][cycle[1][t][0]][cycle[1][t][1]] +
                       self.vars[cycle[0]][cycle[1][t][0]][cycle[1][t][1]] for t in range(len(cycle[1]))))

    def constraint_start_upper_bound(self):
        for index_train, train in enumerate(self.trains):
            for index_operation, operatin in enumerate(train):
                if operatin.upper_bound != -1:
                    sum=0
                    for i in range(0,operatin.upper_bound,):
                        sum=sum+self.vars[i][index_train][index_operation]
                    self.model.add(
                            sum>=1)

    def print(self):
        for i, trains in enumerate(self.vars):
            print(f"timeslot {i}")
            for y, train in enumerate(trains):
                print(f"\ttrain {y}:")
                print("\t\t" + str(train))

    def max_operations(self):
        max_op = []
        for train in self.trains:
            max_op.append(len(train)-1)
        return max_op

    def solve(self):
        solver = cp_model.CpSolver()
        self.setObjective()
        self.constraint_always_there()
        self.constraint_start_at_start()
        self.constraint_operation_length()
        self.constraint_end_at_last_op()
        self.constraint_consecutive()
        self.constraint_resource()
        #self.constraint_start_upper_bound()

        # warscheinlich unnötig
        # self.constraint_successor()

        # compiliert nicht
        # self.constraint_resource_release()

        # 3 ist unmöglich, 4 ist optimal
        status = solver.solve(self.model)
        print("Status:", status)
        assert (status == 4)

        # cycles = self.find_resource_cycles(solver)
        # while (len(cycles) > 0):
        #     for cycle in cycles:
        #         self.constraint_destroy_cycle(cycle)
        #     status = solver.solve(self.model)
        #     print("Status:", status)
        #     assert (status == 4)

        #     cycles = self.find_resource_cycles(solver)

        save_result(solver, self.vars, self.max_operations())
