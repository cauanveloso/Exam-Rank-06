def pack(strs: list[str]) -> str:
    return "".join(str(len(text)) + ":" + text for text in strs)


def unpack(s: str) -> list[str]:
    result, position = [], 0
    while position < len(s):
        separator = s.index(":", position)
        end = separator + 1 + int(s[position:separator])
        result.append(s[separator + 1:end])
        position = end
    return result
