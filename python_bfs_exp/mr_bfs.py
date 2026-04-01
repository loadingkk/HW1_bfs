def mr_bfs(graph, start):
    order, _ = mr_bfs_with_stats(graph, start)
    return order


def mr_bfs_with_stats(graph, start):
    visited = {start}
    frontier = [start]
    order = []
    total_mapped_pairs = 0
    levels = 0

    while frontier:
        levels += 1
        order.extend(frontier)

        grouped = {}
        for node in frontier:
            for neighbor in graph.get(node, []):
                total_mapped_pairs += 1
                grouped.setdefault(neighbor, node)

        next_frontier = []
        for neighbor, parent in grouped.items():
            if neighbor in visited:
                continue
            visited.add(neighbor)
            next_frontier.append(neighbor)

        frontier = next_frontier

    stats = {
        "levels": levels,
        "mapped_pairs": total_mapped_pairs,
        "visited_count": len(order),
    }
    return order, stats


if __name__ == "__main__":
    example_graph = {
        "A": ["B", "C"],
        "B": ["D", "E"],
        "C": ["F"],
        "D": [],
        "E": ["F"],
        "F": [],
    }

    print(mr_bfs(example_graph, "A"))
