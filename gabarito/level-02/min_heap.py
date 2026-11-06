class MinHeap:
    def __init__(self):
        self.values = []

    def push(self, val: int) -> None:
        self.values.append(val)
        position = len(self.values) - 1
        while position > 0:
            parent = (position - 1) // 2
            if self.values[parent] <= self.values[position]:
                break
            self.values[parent], self.values[position] = self.values[position], self.values[parent]
            position = parent

    def pop(self) -> int | None:
        if not self.values:
            return None
        minimum = self.values[0]
        last = self.values.pop()
        if self.values:
            self.values[0] = last
            position = 0
            while 2 * position + 1 < len(self.values):
                child = 2 * position + 1
                if child + 1 < len(self.values) and self.values[child + 1] < self.values[child]:
                    child += 1
                if self.values[position] <= self.values[child]:
                    break
                self.values[position], self.values[child] = self.values[child], self.values[position]
                position = child
        return minimum

    def peek(self) -> int | None:
        if not self.values:
            return None
        return self.values[0]

    def size(self) -> int:
        return len(self.values)
