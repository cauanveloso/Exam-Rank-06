import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

from .exam_cases import subject_for, test_cases


WORKER = Path(__file__).with_name("grader_worker.py")


def grade(statement, submission, timeout=5):
    if not submission.is_file() or submission.is_symlink():
        return {"ok": False, "detail": f"Crie o arquivo {submission.name} em rendu/."}
    cases = test_cases(statement)
    payload = {
        "path": str(submission.resolve()),
        "forbidden": subject_for(statement).get("forbidden", []),
        "subject": subject_for(statement)["name"],
        "cases": cases,
    }
    with tempfile.TemporaryDirectory(prefix="rank06-grade-") as directory:
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", str(WORKER)],
                stdin=subprocess.PIPE, stdout=output, stderr=output,
                cwd=directory, start_new_session=True,
            )
            try:
                process.communicate(json.dumps(payload).encode(), timeout=max(0.01, timeout))
            except subprocess.TimeoutExpired:
                return {"ok": False, "detail": "Tempo limite de execução excedido."}
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            if process.returncode:
                return {"ok": False, "detail": "Execução interrompida: erro ou limite de recursos."}
            output.seek(0)
            try:
                result = json.loads(output.read(1024 * 1024).decode())
            except (ValueError, UnicodeDecodeError):
                return {"ok": False, "detail": "A entrega não concluiu a correção corretamente."}
    result["ok"] = result["passed"] == result["total"] and not result["detail"]
    return result
