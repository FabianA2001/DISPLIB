import read_file
import graphe

import networkx as nx
import matplotlib.pyplot as plt


def print_operations(operations):
    for i, train in enumerate(operations):
        print(f"Train {i}:")
        for y, op in enumerate(train):
            print(f"\tOperation {y}: {op}")


if __name__ == "__main__":

    # path = "displib_instances_testing/line1_critical_0.json"
    path = "displib_instances_testing/displib_testinstances_headway1.json"
    operations = read_file.get_operations(path)

    print_operations(operations)

    for i, train in enumerate(operations):
        plt.clf()
        g = graphe.create_graphe(train)
        nx.draw(g, with_labels=True, node_color='skyblue',
                node_size=300, font_size=9, font_weight='bold')
        plt.savefig(f"graphen/train{i}.png")
