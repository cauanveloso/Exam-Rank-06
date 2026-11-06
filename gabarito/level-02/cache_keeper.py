class CacheKeeper:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.values = {}
        self.links = {}
        self.first = None
        self.last = None

    def remove(self, key):
        previous, following = self.links.pop(key)
        if previous is None:
            self.first = following
        else:
            self.links[previous][1] = following
        if following is None:
            self.last = previous
        else:
            self.links[following][0] = previous

    def touch(self, key):
        if key in self.links:
            self.remove(key)
        self.links[key] = [self.last, None]
        if self.last is None:
            self.first = key
        else:
            self.links[self.last][1] = key
        self.last = key

    def get(self, key: int) -> int:
        if key not in self.values:
            return -1
        self.touch(key)
        return self.values[key]

    def put(self, key: int, value: int) -> None:
        self.values[key] = value
        self.touch(key)
        if len(self.values) > self.capacity:
            oldest = self.first
            self.remove(oldest)
            del self.values[oldest]
