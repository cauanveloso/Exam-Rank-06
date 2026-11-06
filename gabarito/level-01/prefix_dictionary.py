class PrefixDictionary:
    def __init__(self):
        self.root = {}

    def insert(self, word: str) -> None:
        node = self.root
        for character in word:
            node = node.setdefault(character, {})
        node[None] = True

    def walk(self, text):
        node = self.root
        for character in text:
            if character not in node:
                return {}
            node = node[character]
        return node

    def search(self, word: str) -> bool:
        return None in self.walk(word)

    def starts_with(self, prefix: str) -> bool:
        return bool(self.walk(prefix))
