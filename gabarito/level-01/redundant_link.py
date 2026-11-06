def redundant_link(edges: list[list[int]]) -> list[int]:
    parents = {}

    def find(node):
        parents.setdefault(node, node)
        while node != parents[node]:
            parents[node] = parents[parents[node]]
            node = parents[node]
        return node

    redundant = []
    for first, second in edges:
        root_first = find(first)
        root_second = find(second)
        if root_first == root_second:
            redundant = [first, second]
        else:
            parents[root_second] = root_first
    return redundant
