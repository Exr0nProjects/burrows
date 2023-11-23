from graph_data import menu_graph

print(menu_graph)

out = ''

MOD = int(1e6)

def add_to_graph(adj_graph, parent=None):
    # assume k is already in the graph
    for k, v in adj_graph.items():
        out += f"{hash(k) % MOD}[{k}]\n"

    if parent is not None:
        for k, v in adj_graph.items():
            out += f"{hash(parent) % MOD} --> {hash(k) % MOD}"
            add_to_graph(v, k)


print(out)