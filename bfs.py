from collections import deque


def bfs(graph, start):

	visited = set([start])
	order = []
	queue = deque([start])

	while queue:
		node = queue.popleft()
		order.append(node)
		for neighbor in graph.get(node, []):
			if neighbor not in visited:
				visited.add(neighbor)
				queue.append(neighbor)

	return order


if __name__ == "__main__":
	example_graph = {
		"A": ["B", "C"],
		"B": ["D", "E"],
		"C": ["F"],
		"D": [],
		"E": ["F"],
		"F": [],
	}

	print(bfs(example_graph, "A"))
