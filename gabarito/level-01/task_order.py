import heapq


def task_order(n: int, prereqs: list[list[int]]) -> list[int]:
    followers = [set() for _ in range(n)]
    incoming = [0] * n
    for task, prerequisite in prereqs:
        if task not in followers[prerequisite]:
            followers[prerequisite].add(task)
            incoming[task] += 1
    ready = [task for task in range(n) if incoming[task] == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        task = heapq.heappop(ready)
        result.append(task)
        for follower in followers[task]:
            incoming[follower] -= 1
            if incoming[follower] == 0:
                heapq.heappush(ready, follower)
    return result if len(result) == n else []
