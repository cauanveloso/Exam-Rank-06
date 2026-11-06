def bridge_finder(graph: dict[int, list[int]]) -> list[tuple[int, int]]:
    discovery = {}
    low = {}
    bridges = []
    clock = 0
    nodes = set(graph)
    for neighbors in graph.values():
        nodes.update(neighbors)
    for start in sorted(nodes):
        if start in discovery:
            continue
        discovery[start] = low[start] = clock
        clock += 1
        pending = [(start, None, iter(graph.get(start, [])))]
        while pending:
            node, parent, neighbors = pending[-1]
            neighbor = next(neighbors, None)
            if neighbor is None:
                pending.pop()
                if parent is not None:
                    low[parent] = min(low[parent], low[node])
                    if low[node] > discovery[parent]:
                        bridges.append((min(parent, node), max(parent, node)))
                continue
            if neighbor == parent:
                continue
            if neighbor in discovery:
                low[node] = min(low[node], discovery[neighbor])
            else:
                discovery[neighbor] = low[neighbor] = clock
                clock += 1
                pending.append((neighbor, node, iter(graph.get(neighbor, []))))
    return sorted(bridges)
