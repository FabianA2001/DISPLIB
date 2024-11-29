import networkx as nx
from typing import Dict
from read_file import Operation


def create_graphe(train: list[Operation]):
    g = nx.DiGraph()
    for index, op in enumerate(train):
        g.add_node(index)
        for suc in op.succesors:
            g.add_edge(index, suc)
    return g
