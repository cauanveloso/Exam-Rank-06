def trie_autocomplete(words: list[str], prefix: str) -> list[str]:
    root = {}
    for word in words:
        node = root
        for character in word:
            node = node.setdefault(character, {})
        node[None] = word
    node = root
    for character in prefix:
        if character not in node:
            return []
        node = node[character]
    pending, matches = [node], []
    while pending:
        current = pending.pop()
        for character, value in current.items():
            if character is None:
                matches.append(value)
            else:
                pending.append(value)
    return sorted(matches)
