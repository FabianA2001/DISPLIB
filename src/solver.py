class Solver:
    def __init__(self, trains, timeslots) -> None:
        self.vars = []
        for _ in range(timeslots):
            slot = []
            for train in trains:
                train_slot = []
                for _ in train:
                    train_slot.append(None)
                slot.append(train_slot)
            self.vars.append(slot)

    def print(self):
        for i, trains in enumerate(self.vars):
            print(f"timeslot {i}")
            for y, train in enumerate(trains):
                print(f"\ttrain {y}:")
                print("\t\t" + str(train))
