from access_file import Operation
from ortools.sat.python import cp_model
from access_file import save_result
import networkx as nx


class Solver:
    def __init__(self, trains, timeslots, graphes) -> None:
        self.trains: list[list[Operation]] = trains
        self.graphes = graphes
        self.model = cp_model.CpModel()
        self.timeslots = timeslots

        # vars sind : list[list[list[bool]]]
        #             time  train operation
        #             immer der Index
        self.vars = []
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
        # opdelay = 0
        # for t, timeslot in enumerate(self.vars):
        #     for train, time in zip(self.trains, timeslot):
        #         for op, var in zip(train, time):
        #             opdelay += (op.coeff*max(0, t-op.threshold) +
        #                         op.increment*self.big_H(t, op.threshold))*var
        # self.model.minimize(opdelay)

        #################################
        # WRONG
        ################################
        opdelay = 0
        for t, timeslot in enumerate(self.vars):
            for train, time in zip(self.trains, timeslot):
                for op, var in zip(train, time):
                    opdelay += t*var
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
            for slot in range(1, self.timeslots):
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
            self.model.add(sum(self.vars[slot][train][last_op]
                           for slot in range(self.timeslots)) >= 1)

    def constraint_resource_release(self):
        # Resources can only be used after their release time.
        resources = self.resources()
        ops_per_resource = {res.name: [] for res in resources}

        for train_idx, train in enumerate(self.trains):
            for op_idx, operation in enumerate(train):
                for resource in operation.resources:
                    ops_per_resource[resource.name].append(
                        (train_idx, op_idx, operation))

        for time_id in range(self.timeslots):
            for resource_name, operations in ops_per_resource.items():
                for train_idx, op_idx, operation in operations:
                    release_time = max(
                        res.release__time for res in operation.resources if res.name == resource_name)
                    if release_time > 0:
                        is_active = self.vars[time_id][train_idx][op_idx]

                        for t in range(1, release_time + 1):
                            if time_id + t < self.timeslots:
                                for other_train_idx, other_op_idx, _ in operations:
                                    if (other_train_idx, other_op_idx) != (train_idx, op_idx):
                                        self.model.Add(
                                            self.vars[time_id + t][other_train_idx][other_op_idx] == 0).OnlyEnforceIf(
                                            is_active)

    def constraint_resource_release2(self):
        ops_per_res = []
        for i, ressource in enumerate(self.resources()):
            ops_per_res_i = []
            for trainid, train in enumerate(self.trains):
                for opid, operation in enumerate(train):

                    for res in operation.resources:
                        if res.name == ressource:
                            ops_per_res_i.append((trainid, opid))
            ops_per_res.append(ops_per_res_i)
        print(ops_per_res)

        for timeid, slot in enumerate(self.vars):
            for trainid, train in enumerate(self.trains):
                for opid, op in enumerate(train):

                    is_equal = self.model.NewBoolVar(
                        f'is_equal_{timeid}_{trainid}_{opid}')
                    self.model.Add(
                        self.vars[timeid][trainid][opid] == 1).OnlyEnforceIf(is_equal)
                    is_equal2 = self.model.NewBoolVar(
                        f'is_equal2_{timeid}_{trainid}_{opid}')
                    if timeid > 0:

                        self.model.Add(
                            self.vars[timeid-1][trainid][opid] == 0).OnlyEnforceIf(is_equal2)

                    for res in op.resources:
                        res_id = self.resources().index(res.name)

                        for tuple in ops_per_res[res_id]:
                            if tuple[1] != op:
                                summ = sum(self.vars[i][trainid][opid]
                                           for i in range(0, timeid))
                                for t in range(res.release__time):
                                    if timeid+t < len(self.vars):
                                        print("hi")
                                        is_equal3 = self.model.NewBoolVar(
                                            f'is_equal3_{timeid+t}_{tuple[0]}_{tuple[1]}')
                                        self.model.Add(
                                            self.vars[timeid+t][tuple[0]][tuple[1]] == 0).OnlyEnforceIf(is_equal3)
                                        self.model.add(is_equal3 <= is_equal)
                                        self.model.add(is_equal3 <= is_equal2)

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
        for train in range(len(self.trains)):
            outcoming_edges = list(self.graphes[train].out_edges(0))
            target_nodes = [edge[1] for edge in outcoming_edges]
            target_nodes.append(0)
            summ = 0
            for op in range(len(self.trains[train])):
                if op in target_nodes:
                    continue
                summ += self.vars[0][train][op]
            self.model.add(summ == 0)

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
                    for i in range(0, operatin.upper_bound,):
                        summ += self.vars[i][index_train][index_operation]
                    self.model.add(
                        summ >= 1)

    def constraint_start_lower_bound(self):
        for index_train, train in enumerate(self.trains):
            for index_operation, operatin in enumerate(train):
                if operatin.lower_bound != -1:
                    summ = 0
                    for i in range(0, operatin.lower_bound,):
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
        self.solver = cp_model.CpSolver()
        # ohne dieses Zeile ist es nicht Determinstisch
        self.solver.parameters.num_search_workers = 1
        self.setObjective()

        self.constraint_start_at_start()
        self.constraint_operation_length()
        self.constraint_end_at_last_op()
        self.constraint_consecutive()
        self.constraint_resource()
        self.constraint_start_upper_bound()
        self.constraint_start_lower_bound()

        # in deren der Lösung (displib_solution_testinstances_headway1) ist
        # Zug 0 im 0 zeitslot in operation 0 und 1
        # aber ohne geht es garnicht mehr
        self.constraint_always_there()

        # warscheinlich unnötig
        # self.constraint_successor()

        # compiliert jetzt, tut aber nicht, was es soll
        self.constraint_resource_release()

        # # compiliert jetzt, tut aber nicht, was es soll, solllte aber richtiger sein als vorher
        # self.constraint_resource_release2()

        # 3 ist unmöglich, 4 ist optimal
        status = self.solver.solve(self.model)
        print("Status:", status)
        assert (status == 4)
        print("Orginal objective_value", self.solver.ObjectiveValue())

        # vorläufig deaktiviert da cycles aktuell keine Probleme darstellen
        # cycles = self.find_resource_cycles(self.solver)
        # while (len(cycles) > 0):
        #     for cycle in cycles:
        #         self.constraint_destroy_cycle(cycle)
        #     status = self.solver.solve(self.model)
        #     print("Status:", status)
        #     assert (status == 4)

        #     cycles = self.find_resource_cycles(self.solver)

        save_result(self.solver, self.vars, self.max_operations(), self.trains)
