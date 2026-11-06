from datetime import datetime
import json
import math
from pathlib import Path
import random
import select
import sys
import time
import uuid

from .grader import grade
from .terminal import clear_screen, paint, timer_text


ROOT = Path(__file__).resolve().parents[1]
DURATION = 4 * 60 * 60


class TimeExpired(Exception):
    pass


def clock_text(seconds):
    seconds = max(0, math.ceil(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def read_command(prompt, deadline=None):
    if deadline is None:
        return input(paint(prompt, "cyan")).strip().lower()
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    shown = None
    if interactive:
        remaining = deadline - time.time()
        print(timer_text(remaining, f"[{clock_text(remaining)}]") + " " + paint(prompt, "cyan"), end="", flush=True)
    else:
        print(prompt, end="", flush=True)
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            print()
            raise TimeExpired
        timer = clock_text(remaining)
        if interactive and timer != shown:
            print("\0337\r" + timer_text(remaining, f"[{timer}]") + "\0338", end="", flush=True)
            shown = timer
        ready, _, _ = select.select([sys.stdin], [], [], min(1, remaining))
        if ready:
            line = sys.stdin.readline()
            if not line:
                raise EOFError
            if time.time() >= deadline:
                raise TimeExpired
            return line.strip().lower()


def catalog(root):
    levels = {}
    statements = root / "gabarito" / "enunciados"
    for statement in sorted(statements.glob("level-*/*.txt")):
        level = int(statement.parent.name.removeprefix("level-"))
        levels.setdefault(level, []).append(str(statement.relative_to(statements)))
    if not levels:
        raise ValueError("Nenhuma questão encontrada em gabarito/enunciados/level-*.")
    return levels


def save_session(root, session):
    path = root / "src" / ".session.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def load_session(root):
    path = root / "src" / ".session.json"
    if not path.exists():
        return None
    try:
        session = json.loads(path.read_text(encoding="utf-8"))
        if session["mode"] not in ("exam", "practice"):
            raise ValueError("Modo inválido")
        if session["status"] not in ("active", "passed", "expired", "finished"):
            raise ValueError("Estado inválido")
        exercises = session["exercises"]
        if not isinstance(exercises, list) or not exercises:
            raise ValueError("Questões inválidas")
        available = set()
        for options in catalog(root).values():
            available.update(options)
        for exercise in exercises:
            if exercise not in available:
                raise ValueError("Questão não encontrada")
        if type(session["current"]) is not int or not 0 <= session["current"] <= len(exercises):
            raise ValueError("Nível inválido")
        if session["status"] == "active" and session["current"] == len(exercises):
            raise ValueError("Questão atual ausente")
        if not isinstance(session["attempts"], list):
            raise ValueError("Tentativas inválidas")
        if session["mode"] == "exam":
            if type(session["deadline"]) not in (int, float) or not math.isfinite(session["deadline"]):
                raise ValueError("Prazo inválido")
        elif session["deadline"] is not None:
            raise ValueError("Prática deve ter prazo ausente")
        return session
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("Estado da sessão inválido. Preserve rendu/ e consulte src/README.md para recuperação.") from error


def create_session(root, mode, exercises):
    workspace = root / "rendu"
    state = root / "src" / ".session.json"
    if workspace.exists() or state.exists():
        history = root / "historico"
        history.mkdir(exist_ok=True)
        name = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
        archive = history / name
        archive.mkdir()
        if workspace.exists():
            workspace.rename(archive / "rendu")
        if state.exists():
            state.rename(archive / ".session.json")
        print(f"Entrega anterior preservada em historico/{name}/")
    workspace.mkdir()
    now = time.time()
    session = {
        "mode": mode, "exercises": exercises, "current": 0,
        "started_at": now, "deadline": now + DURATION if mode == "exam" else None,
        "status": "active", "attempts": [],
    }
    save_session(root, session)
    return session


def statement_text(root, exercise):
    statement = root / "gabarito" / "enunciados" / exercise
    metadata = json.loads((root / "src" / "subjects.json").read_text(encoding="utf-8"))
    subject = next(item for item in metadata["subjects"] if item["file"] == statement.with_suffix(".py").name)
    signature = subject["signature"]
    if subject["name"] == "py_compress_decompress":
        signature += "\ndef decompress(s: str) -> str:"
    header = (
        f"Nível: {statement.parent.name.removeprefix('level-')}\n"
        f"Arquivo exigido: rendu/{statement.stem}.py\n"
        f"Interface exigida: {signature}\n"
        "Implemente todas as funções ou métodos exigidos e retorne os resultados solicitados.\n\n"
    )
    text = header + statement.read_text(encoding="utf-8").rstrip() + "\n"
    from .exam_cases import local_rules
    rules = local_rules(subject["name"])
    if rules:
        text += "\nCritérios deste simulado local:\n" + rules + "\n"
    return text


def publish_statement(root, session):
    exercise = session["exercises"][session["current"]]
    text = statement_text(root, exercise)
    print()
    for number, line in enumerate(text.splitlines()):
        if number < 3:
            print(paint(line, "cyan"))
        else:
            print(line)
    print()


def finish(root, session, status):
    session["status"] = status
    save_session(root, session)
    score = 0
    if session["mode"] == "exam":
        score = round(100 * session["current"] / len(session["exercises"]))
    color = "yellow"
    if status == "passed":
        color = "green"
    elif status == "expired":
        color = "red"
    message = f"\nSessão encerrada: {status}." + (f" Pontuação: {score}/100." if session["mode"] == "exam" else "")
    print(paint(message, color))
    print("Entregas e resultados preservados.")


def correct(root, session):
    deadline = session["deadline"]
    timeout = 5
    if deadline is not None:
        remaining = deadline - time.time()
        if remaining <= 0:
            raise TimeExpired
        timeout = min(timeout, remaining)
    exercise = session["exercises"][session["current"]]
    statement = root / "gabarito" / "enunciados" / exercise
    submission = root / "rendu" / statement.with_suffix(".py").name
    print(paint("Corrigindo...", "blue"), flush=True)
    result = grade(statement, submission, timeout=timeout)
    if deadline is not None and time.time() >= deadline:
        raise TimeExpired
    attempt = {"exercise": exercise, "time": time.time(), "ok": result["ok"]}
    session["attempts"].append(attempt)
    if result["ok"] and session["mode"] == "exam":
        session["current"] += 1
        if session["current"] == len(session["exercises"]):
            session["status"] = "passed"
    save_session(root, session)
    clear_screen()
    if result["ok"]:
        print(paint("✅ correto", "green"))
    else:
        print(paint("❌ incorreto", "yellow"))
    completed = session["current"]
    if session["mode"] == "practice":
        completed = int(any(attempt["ok"] for attempt in session["attempts"]))
    print(paint(f"Progresso: {completed}/{len(session['exercises'])}", "green"))
    if result["ok"] and session["mode"] == "exam" and session["status"] == "active":
        publish_statement(root, session)
    if not result["ok"] and session["mode"] == "practice":
        print(paint(result["detail"], "yellow"))
        if "passed" in result:
            print(f"Testes aprovados antes da primeira falha: {result['passed']}/{result['total']}.")


def run_session(root, session):
    deadline = session["deadline"]
    if deadline is not None and time.time() >= deadline:
        finish(root, session, "expired")
        return
    publish_statement(root, session)
    print("Edite sua solução em outro terminal ou no editor e salve antes de corrigir.")
    print("Comandos: corrigir (ou grademe), enunciado, status, sair, encerrar")
    print("Ao acertar, o próximo enunciado aparece automaticamente; use enunciado para reler.")
    print("Ao iniciar outra sessão, rendu será limpa e o relógio será reiniciado.")
    try:
        while session["status"] == "active":
            command = read_command("prova> ", deadline)
            if command in ("corrigir", "grademe"):
                correct(root, session)
            elif command == "enunciado":
                publish_statement(root, session)
            elif command == "status":
                print(paint(f"Etapa: {session['current'] + 1}/{len(session['exercises'])} | Tentativas: {len(session['attempts'])}", "green"))
                if deadline is None:
                    print("Sem limite de tempo.")
                else:
                    remaining = deadline - time.time()
                    print(timer_text(remaining, f"Restante: {clock_text(remaining)}"))
            elif command == "sair":
                print("Entregas salvas. Ao iniciar novamente, será criada uma sessão limpa.")
                return
            elif command == "encerrar":
                finish(root, session, "finished")
            else:
                print(paint("Use corrigir, enunciado, status, sair ou encerrar.", "yellow"))
    except TimeExpired:
        finish(root, session, "expired")


def start(root, mode):
    levels = catalog(root)
    if mode == "exam":
        exercises = []
        for level in sorted(levels):
            exercises.append(random.choice(levels[level]))
    else:
        options = []
        for level in sorted(levels):
            for exercise in levels[level]:
                options.append(exercise)
                print(f"{len(options)}) Nível {level}: {Path(exercise).stem}")
        selection = read_command("Questão (ou voltar): ")
        if selection == "voltar":
            return
        if not selection.isdecimal() or not 1 <= int(selection) <= len(options):
            print(paint("Questão inválida.", "yellow"))
            return
        exercises = [options[int(selection) - 1]]
    session = create_session(root, mode, exercises)
    run_session(root, session)


def main(root=ROOT):
    try:
        catalog(root)
        while True:
            print(paint("\nSIMULADO RANK 06 — treino local inspirado no formato da 42", "title"))
            print(paint("1) Praticar", "blue"))
            print(paint("2) Iniciar simulado (4 horas)", "blue"))
            print("3) Sair")
            command = read_command("> ")
            if command in ("1", "praticar"):
                start(root, "practice")
            elif command in ("2", "iniciar"):
                start(root, "exam")
            elif command in ("3", "sair"):
                return 0
            else:
                print(paint("Opção inválida.", "yellow"))
    except (EOFError, KeyboardInterrupt):
        print("\nSaída. Entregas preservadas; a próxima sessão começará com rendu limpa.")
        return 0
    except (OSError, ValueError) as error:
        print(paint(f"Erro: {error}", "red", stream=sys.stderr), file=sys.stderr)
        return 1
