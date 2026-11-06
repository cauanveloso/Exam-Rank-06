import ast
from collections import Counter
import contextlib
import importlib.util
import json
import os
import resource
import sys


def forbidden_usage(tree, forbidden):
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split('.')[0]] = item.name
                if any(item.name == rule or item.name.startswith(rule + '.') for rule in forbidden):
                    return item.name
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                full = (node.module or '') + '.' + item.name
                aliases[item.asname or item.name] = full
                if any(full == rule or full.startswith(rule + '.') for rule in forbidden):
                    return full
                if item.name == '*' and any(rule.startswith((node.module or '') + '.') for rule in forbidden):
                    return full
    for node in ast.walk(tree):
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.insert(0, current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.insert(0, aliases.get(current.id, current.id))
            name = '.'.join(parts).removeprefix('builtins.')
            if name in forbidden:
                return name
    return None


def same_result(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(same_result(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(same_result(actual[key], value) for key, value in expected.items())
    return actual == expected


def valid_schedule(actual, expected, code):
    if not isinstance(actual, dict) or set(actual) != {'total_rooms', 'schedule'}:
        return False
    count = actual['total_rooms']
    rooms = actual['schedule']
    if type(count) is not int or count != expected['total_rooms'] or not isinstance(rooms, list) or len(rooms) != count:
        return False
    meetings = ast.literal_eval(ast.parse(code, mode='eval').body.args[0])
    delivered = []
    for room in rooms:
        if not isinstance(room, list) or not room:
            return False
        end = None
        for meeting in room:
            if not isinstance(meeting, list) or len(meeting) != 2 or any(type(t) is not int for t in meeting):
                return False
            if end is not None and meeting[0] < end:
                return False
            end = meeting[1]
            delivered.append(tuple(meeting))
    return Counter(delivered) == Counter(map(tuple, meetings))


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    payload = json.loads(sys.stdin.read())
    passed = 0
    detail = ''
    try:
        with open(os.devnull, 'w') as silent:
            with contextlib.redirect_stdout(silent), contextlib.redirect_stderr(silent):
                with open(payload['path'], encoding='utf-8') as source:
                    tree = ast.parse(source.read())
                prohibited = forbidden_usage(tree, payload['forbidden'])
                if prohibited:
                    raise ValueError(f'Recurso proibido pelo enunciado: {prohibited}')
                spec = importlib.util.spec_from_file_location('submission', payload['path'])
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for number, case in enumerate(payload['cases'], 1):
                    namespace = vars(module).copy()
                    program = ast.parse(case['input'])
                    prefix = ast.Module(body=program.body[:-1], type_ignores=[])
                    expression = ast.Expression(body=program.body[-1].value)
                    exec(compile(prefix, '<test>', 'exec'), namespace)
                    actual = eval(compile(expression, '<test>', 'eval'), namespace)
                    expected = ast.literal_eval(case['output'])
                    ok = same_result(actual, expected)
                    if payload['subject'] == 'py_room_scheduler':
                        ok = valid_schedule(actual, expected, case['input'])
                    elif payload['subject'] == 'py_prism_detector':
                        ok = isinstance(actual, list) and all(type(item) is tuple for item in actual) and sorted(actual) == sorted(expected)
                    if not ok:
                        detail = f'Teste {number}: esperado {expected!r}; recebido {actual!r}.'[:1500]
                        break
                    passed += 1
    except BaseException as error:
        detail = f'{type(error).__name__}: {error}'[:1500]
    print(json.dumps({'passed': passed, 'total': len(payload['cases']), 'detail': detail}))


if __name__ == '__main__':
    main()
