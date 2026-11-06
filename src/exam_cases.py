import ast
from collections import OrderedDict, deque
import itertools
import json
from pathlib import Path
import random


def subject_for(statement):
    statement = statement.resolve()
    path = statement.parents[3] / 'src' / 'subjects.json'
    subjects = json.loads(path.read_text(encoding='utf-8'))['subjects']
    return next(subject for subject in subjects if subject['file'] == statement.with_suffix('.py').name)


def local_rules(name):
    rules = {
        'py_compress_decompress': 'Compressão testada com caracteres não numéricos; descompressão recebe formatos válidos, com contagens positivas.',
        'py_spiral_matrix': 'Para n = 0, este treino espera uma matriz vazia. Valores negativos não são testados.',
        'py_graph_cycle_detector': 'Vizinhos ausentes das chaves são considerados vértices sem saídas.',
        'py_room_scheduler': 'Intervalos têm início menor que fim. Uma sala pode ser reutilizada quando fim <= próximo início. Qualquer distribuição válida com o número mínimo de salas é aceita.',
        'py_prism_detector': 'Valem os deslocamentos numéricos da tabela: D2 = (-1, 1) e D2- = (1, -1), apesar dos nomes textuais trocados no site. A ordem dos resultados é livre; repetições extras são rejeitadas. Uma letra isolada conta nas oito direções.',
        'py_word_ladder': 'Se start == end, o resultado é 1. Caso contrário, end precisa estar em sentence, como nos exemplos do site.',
        'cache_keeper': 'O segundo exemplo do site contém uma inconsistência: após put(1, 1), put(2, 2), put(3, 3), get(2) deve retornar 2. O corretor segue a regra LRU escrita. Capacidade sempre positiva.',
        'prefix_dictionary': 'Prefixo vazio corresponde a qualquer palavra já inserida; antes da primeira inserção, starts_with("") retorna False.',
        'pack_strings': 'O formato de serialização é livre: são verificados retorno str e round-trip, sem exigir um delimitador específico.',
        'union_find_system': 'A escolha da raiz em empates é livre. Testes verificam representantes válidos e conectividade; compressão de caminho e união por rank exigem revisão do código.',
        'bridge_finder': 'Casos usam grafos simples, não dirigidos e simétricos, sem arestas paralelas.',
    }
    return rules.get(name, '')


def component_count(graph, removed=None):
    visited = set()
    count = 0
    for node in graph:
        if node in visited:
            continue
        count += 1
        pending = [node]
        visited.add(node)
        while pending:
            current = pending.pop()
            for neighbor in graph[current]:
                if removed is not None and {current, neighbor} == set(removed):
                    continue
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
    return count


def test_cases(statement):
    subject = subject_for(statement)
    name = subject['name']
    cases = []
    for example in subject['examples']:
        cases.append(dict(example))
    if name == 'cache_keeper':
        cases[1]['output'] = '2'
    rng = random.Random(42)

    def add(code, result):
        cases.append({'input': code, 'output': repr(result)})

    def call(function, args, result):
        arguments = ', '.join(repr(arg) for arg in args)
        add(f'{function}({arguments})', result)

    if name == 'py_compress_decompress':
        texts = ['', 'a', 'a' * 120, 'abababab', 'AAaa!!   ', '\nééé']
        for _ in range(60):
            texts.append(''.join(rng.choices('abc !', k=rng.randrange(80))))
        for text in texts:
            compressed = ''
            for character, group in itertools.groupby(text):
                count = len(list(group))
                compressed += character + (str(count) if count > 1 else '')
            call('compress', [text], compressed)
            call('decompress', [compressed], text)
        call('decompress', ['a1b12c2'], 'a' + 'b' * 12 + 'cc')
    elif name == 'py_spiral_matrix':
        for size in range(13):
            matrix = []
            for _ in range(size):
                matrix.append([0] * size)
            row, column, direction = 0, 0, 0
            steps = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for number in range(1, size * size + 1):
                matrix[row][column] = number
                step_row, step_column = steps[direction]
                next_row, next_column = row + step_row, column + step_column
                if not (0 <= next_row < size and 0 <= next_column < size) or matrix[next_row][next_column]:
                    direction = (direction + 1) % 4
                    step_row, step_column = steps[direction]
                row += step_row
                column += step_column
            call('generate_spiral', [size], matrix)
    elif name == 'py_graph_cycle_detector':
        graphs = [{0: [0]}, {0: [1, 2], 1: [3], 2: [3], 3: []}, {0: [], 1: [2], 2: [1]}, {4: [5]}]
        for _ in range(70):
            size = rng.randrange(8)
            graph = {}
            for node in range(size):
                graph[node] = rng.sample(range(size), rng.randrange(size + 1))
            graphs.append(graph)
        for graph in graphs:
            cycle = False
            for start in graph:
                visited = set()
                pending = list(graph[start])
                while pending:
                    node = pending.pop()
                    if node == start:
                        cycle = True
                        break
                    if node not in visited:
                        visited.add(node)
                        pending.extend(graph.get(node, []))
            call('py_graph_cycle_detector', [graph], cycle)
    elif name == 'py_room_scheduler':
        all_meetings = [[], [[0, 2], [2, 4]], [[1, 4], [1, 4], [1, 4]], [[5, 6], [0, 5], [1, 3]]]
        for _ in range(80):
            meetings = []
            for _ in range(rng.randrange(20)):
                start = rng.randrange(-10, 20)
                meetings.append([start, start + rng.randrange(1, 12)])
            all_meetings.append(meetings)
        for meetings in all_meetings:
            maximum = 0
            for start, _ in meetings:
                active = sum(first <= start < last for first, last in meetings)
                maximum = max(maximum, active)
            call('py_room_scheduler', [meetings], {'total_rooms': maximum, 'schedule': []})
    elif name == 'py_island_matrix_counter':
        matrices = [[], [[]], [['1']], [['0']], [['1', '0'], ['0', '1']]]
        for _ in range(80):
            rows, columns = rng.randrange(8), rng.randrange(8)
            matrix = []
            for _ in range(rows):
                matrix.append(rng.choices(['0', '1'], k=columns))
            matrices.append(matrix)
        for matrix in matrices:
            land = set()
            for row, line in enumerate(matrix):
                for column, cell in enumerate(line):
                    if cell == '1':
                        land.add((row, column))
            islands = 0
            while land:
                islands += 1
                pending = [land.pop()]
                while pending:
                    row, column = pending.pop()
                    for point in ((row + 1, column), (row - 1, column), (row, column + 1), (row, column - 1)):
                        if point in land:
                            land.remove(point)
                            pending.append(point)
            call('island_matrix_counter', [matrix], islands)
    elif name == 'py_prism_detector':
        directions = [(1, 0, 'H'), (-1, 0, 'H-'), (0, 1, 'V'), (0, -1, 'V-'), (1, 1, 'D1'), (-1, -1, 'D1-'), (-1, 1, 'D2'), (1, -1, 'D2-')]
        inputs = [(['A'], 'A'), (['AA', 'AA'], 'AA'), (['AB', 'BA'], ''), (['..C', '.A.', 'T..'], 'CAT'), (['T..', '.A.', '..C'], 'CAT')]
        for _ in range(70):
            size = rng.randrange(6)
            grid = []
            for _ in range(size):
                grid.append(''.join(rng.choices('ABC', k=size)))
            inputs.append((grid, ''.join(rng.choices('ABC', k=rng.randrange(1, 5)))))
        for grid, pattern in inputs:
            matches = []
            if pattern:
                for y, row in enumerate(grid):
                    for x in range(len(row)):
                        for dx, dy, code in directions:
                            letters = ''
                            for offset in range(len(pattern)):
                                row_index, column_index = y + dy * offset, x + dx * offset
                                if 0 <= row_index < len(grid) and 0 <= column_index < len(grid[row_index]):
                                    letters += grid[row_index][column_index]
                            if letters == pattern:
                                matches.append((x, y, code))
            call('prism_detector', [grid, pattern], matches)
    elif name == 'py_word_ladder':
        words = list(map(''.join, itertools.product('abc', repeat=3)))
        inputs = [('a', 'a', []), ('a', 'b', ['b']), ('a', 'b', []), ('a', 'bb', ['bb'])]
        for _ in range(70):
            inputs.append((rng.choice(words), rng.choice(words), rng.sample(words, rng.randrange(len(words) + 1))))
        for start, end, sentence in inputs:
            distance = {start: 1}
            pending = deque([start])
            while pending:
                word = pending.popleft()
                for candidate in sentence:
                    if candidate in distance or len(candidate) != len(word):
                        continue
                    if sum(a != b for a, b in zip(word, candidate)) == 1:
                        distance[candidate] = distance[word] + 1
                        pending.append(candidate)
            call('word_ladder', [start, end, sentence], distance.get(end, 0))
    elif name == 'prefix_dictionary':
        for _ in range(30):
            words = set()
            lines = ['d = PrefixDictionary()', 'results = []']
            expected = []
            for _ in range(60):
                word = ''.join(rng.choices('abc', k=rng.randrange(1, 7)))
                operation = rng.choice(['insert', 'search', 'starts_with'])
                if operation == 'insert':
                    words.add(word)
                    lines.append(f'results.append(d.insert({word!r}))')
                    expected.append(None)
                else:
                    if operation == 'starts_with' and rng.randrange(4) == 0:
                        word = ''
                    lines.append(f'results.append(d.{operation}({word!r}))')
                    expected.append(word in words if operation == 'search' else any(item.startswith(word) for item in words))
            add('; '.join(lines + ['results']), expected)
    elif name == 'pack_strings':
        lists = [[], [''], ['', ''], ['#', ':', '12#:', '\n', 'á🌎'], ['a' * 1000], ['a', 'bc'], ['ab', 'c']]
        for _ in range(60):
            texts = []
            for _ in range(rng.randrange(12)):
                texts.append(''.join(rng.choices('abc01:# \n🌎', k=rng.randrange(25))))
            lists.append(texts)
        for texts in lists:
            add(f'isinstance(pack({texts!r}), str)', True)
            add(f'unpack(pack({texts!r}))', texts)
    elif name == 'task_order':
        for _ in range(85):
            size = rng.randrange(7)
            dependencies = []
            for first in range(size):
                for second in range(size):
                    if rng.randrange(7) == 0:
                        dependencies.append([first, second])
            if dependencies and rng.choice([True, False]):
                dependencies.append(dependencies[0][:])
            result = []
            for permutation in itertools.permutations(range(size)):
                position = {}
                for index, task in enumerate(permutation):
                    position[task] = index
                if all(position[before] < position[after] for after, before in dependencies):
                    result = list(permutation)
                    break
            call('task_order', [size, dependencies], result)
        call('task_order', [4, [[0, 2]]], [1, 2, 0, 3])
    elif name == 'redundant_link':
        for _ in range(70):
            size = rng.randrange(3, 10)
            edges = []
            for node in range(2, size + 1):
                edges.append([node, rng.randrange(1, node)])
            present = {tuple(sorted(pair)) for pair in edges}
            choices = []
            for first in range(1, size + 1):
                for second in range(first + 1, size + 1):
                    if (first, second) not in present:
                        choices.append([first, second])
            edges.append(rng.choice(choices))
            rng.shuffle(edges)
            expected = []
            for index in range(len(edges) - 1, -1, -1):
                graph = {}
                for node in range(1, size + 1):
                    graph[node] = []
                for edge_index, (first, second) in enumerate(edges):
                    if index != edge_index:
                        graph[first].append(second)
                        graph[second].append(first)
                if component_count(graph) == 1:
                    expected = edges[index]
                    break
            call('redundant_link', [edges], expected)
    elif name == 'union_find_system':
        for _ in range(30):
            size = rng.randrange(1, 20)
            labels = list(range(size))
            lines = [f'uf = UnionFind({size})', 'results = []']
            expected = []
            for _ in range(60):
                first, second = rng.randrange(size), rng.randrange(size)
                operation = rng.choice(['union', 'connected', 'find'])
                if operation == 'union':
                    expected.append(labels[first] != labels[second])
                    old, new = labels[second], labels[first]
                    for index in range(size):
                        if labels[index] == old:
                            labels[index] = new
                    lines.append(f'results.append(uf.union({first}, {second}))')
                elif operation == 'connected':
                    lines.append(f'results.append(uf.connected({first}, {second}))')
                    expected.append(labels[first] == labels[second])
                else:
                    members = []
                    for node in range(size):
                        if labels[node] == labels[first]:
                            members.append(node)
                    lines.append(f'root = uf.find({first})')
                    lines.append(f'results.append(type(root) is int and root in {members!r} and uf.find(root) == root and (root == uf.find({second})) == {labels[first] == labels[second]!r})')
                    expected.append(True)
            add('; '.join(lines + ['results']), expected)
    elif name == 'cache_keeper':
        for _ in range(35):
            capacity = rng.randrange(1, 6)
            cache = OrderedDict()
            lines = [f'c = CacheKeeper({capacity})', 'results = []']
            expected = []
            for _ in range(100):
                key = rng.randrange(10)
                if rng.choice([True, False]):
                    value = rng.randrange(-20, 21)
                    cache[key] = value
                    cache.move_to_end(key)
                    if len(cache) > capacity:
                        cache.popitem(last=False)
                    lines.append(f'results.append(c.put({key}, {value}))')
                    expected.append(None)
                else:
                    value = cache.get(key, -1)
                    if key in cache:
                        cache.move_to_end(key)
                    lines.append(f'results.append(c.get({key}))')
                    expected.append(value)
            add('; '.join(lines + ['results']), expected)
    elif name == 'min_heap':
        for _ in range(35):
            values = []
            lines = ['h = MinHeap()', 'results = []']
            expected = []
            for _ in range(100):
                operation = rng.choice(['push', 'pop', 'peek', 'size'])
                if operation == 'push':
                    value = rng.randrange(-30, 31)
                    values.append(value)
                    values.sort()
                    lines.append(f'results.append(h.push({value}))')
                    expected.append(None)
                elif operation == 'pop':
                    lines.append('results.append(h.pop())')
                    expected.append(values.pop(0) if values else None)
                elif operation == 'peek':
                    lines.append('results.append(h.peek())')
                    expected.append(values[0] if values else None)
                else:
                    lines.append('results.append(h.size())')
                    expected.append(len(values))
            add('; '.join(lines + ['results']), expected)
    elif name == 'trie_autocomplete':
        for _ in range(85):
            words = []
            for _ in range(rng.randrange(30)):
                words.append(''.join(rng.choices('aAbBc', k=rng.randrange(6))))
            prefix = ''.join(rng.choices('aAbBc', k=rng.randrange(4)))
            expected = []
            for word in sorted(set(words)):
                if word.startswith(prefix):
                    expected.append(word)
            call('trie_autocomplete', [words, prefix], expected)
    elif name == 'bridge_finder':
        for _ in range(85):
            size = rng.randrange(9)
            graph = {}
            for node in range(size):
                graph[node] = []
            edges = []
            for first in range(size):
                for second in range(first + 1, size):
                    if rng.randrange(4) == 0:
                        graph[first].append(second)
                        graph[second].append(first)
                        edges.append((first, second))
            original = component_count(graph)
            bridges = []
            for edge in edges:
                if component_count(graph, edge) > original:
                    bridges.append(edge)
            call('bridge_finder', [graph], bridges)
    else:
        raise ValueError(f'Questão sem corretor: {name}')
    return cases
