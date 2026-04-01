import random


def generate_graph(num_nodes, avg_degree, seed):
    if num_nodes <= 0:
        return {}
    if num_nodes == 1:
        return {0: []}

    rng = random.Random(seed)
    half_degree = max(1, avg_degree // 2)
    adjacency = {node: set() for node in range(num_nodes)}

    for node in range(num_nodes):
        while len(adjacency[node]) < half_degree:
            neighbor = rng.randrange(num_nodes)
            if neighbor == node or neighbor in adjacency[node]:
                continue
            adjacency[node].add(neighbor)
            adjacency[neighbor].add(node)

    return {node: sorted(neighbors) for node, neighbors in adjacency.items()}


def choose_roots(graph, root_count, seed):
    rng = random.Random(seed)
    candidates = [node for node, neighbors in graph.items() if neighbors]
    if not candidates:
        return [0]
    if root_count >= len(candidates):
        return candidates
    return rng.sample(candidates, root_count)
