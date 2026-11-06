import ast
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from src import simulator
from src.exam_cases import subject_for, test_cases
from src.grader import grade


ROOT = Path(__file__).resolve().parents[2]


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / 'gabarito', self.root / 'gabarito')
        (self.root / 'src').mkdir()
        shutil.copy2(ROOT / 'src/subjects.json', self.root / 'src/subjects.json')
        self.output = io.StringIO()
        redirect = contextlib.redirect_stdout(self.output)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)
        self.statements = sorted((self.root / 'gabarito/enunciados').glob('level-*/*.txt'))

    def reference(self, statement):
        return (self.root / 'gabarito' / statement.relative_to(self.root / 'gabarito/enunciados')).with_suffix('.py')

    def session(self, mode='exam'):
        exercises = [options[0] for _, options in sorted(simulator.catalog(self.root).items())]
        if mode == 'practice':
            exercises = exercises[:1]
        return simulator.create_session(self.root, mode, exercises)

    def submit(self, text):
        path = self.root / 'answer.py'
        path.write_text(text)
        return path

    def deliver(self, exercise):
        statement = self.root / 'gabarito/enunciados' / exercise
        shutil.copy2(self.reference(statement), self.root / 'rendu' / statement.with_suffix('.py').name)

    def test_all_references_pass_examples_and_additional_cases(self):
        count = 0
        for statement in self.statements:
            with self.subTest(statement=statement.name):
                result = grade(statement, self.reference(statement))
                self.assertTrue(result['ok'], result)
                count += result['total']
        self.assertGreater(count, 500)

    def test_stubs_are_rejected_for_every_exercise(self):
        for statement in self.statements:
            with self.subTest(statement=statement.name):
                tree = ast.parse(self.reference(statement).read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        node.body = [ast.Return(value=ast.Constant(value=None))]
                ast.fix_missing_locations(tree)
                self.assertFalse(grade(statement, self.submit(ast.unparse(tree)))['ok'])

    def test_missing_file_missing_interface_syntax_exception_and_exit(self):
        self.assertFalse(grade(self.statements[0], self.root / 'missing.py')['ok'])
        for text in ('', 'def broken(:', 'raise RuntimeError("error")', 'raise SystemExit(0)'):
            with self.subTest(text=text):
                self.assertFalse(grade(self.statements[0], self.submit(text))['ok'])

    def test_loop_times_out(self):
        started = time.monotonic()
        result = grade(self.statements[0], self.submit('while True:\n    pass\n'), timeout=0.15)
        self.assertFalse(result['ok'])
        self.assertIn('Tempo limite', result['detail'])
        self.assertLess(time.monotonic() - started, 2)

    def test_prints_do_not_break_grading(self):
        statement = self.statements[0]
        answer = self.submit('print("noise")\n' + self.reference(statement).read_text())
        self.assertTrue(grade(statement, answer)['ok'])

    def test_saved_changes_are_reloaded(self):
        statement = self.statements[0]
        answer = self.submit('')
        self.assertFalse(grade(statement, answer)['ok'])
        answer.write_text(self.reference(statement).read_text())
        self.assertTrue(grade(statement, answer)['ok'])

    def test_symlinks_are_rejected(self):
        answer = self.root / 'link.py'
        answer.symlink_to(self.reference(self.statements[0]))
        self.assertFalse(grade(self.statements[0], answer)['ok'])

    def test_forbidden_imports_aliases_and_calls_are_rejected(self):
        for statement in self.statements:
            for forbidden in subject_for(statement).get('forbidden', []):
                module, separator, member = forbidden.rpartition('.')
                if separator:
                    prefixes = [f'from {module} import {member} as prohibited\n', f'import {module} as alias\nprohibited = alias.{member}\n']
                elif forbidden == 'eval':
                    prefixes = ['prohibited = eval\n', 'import builtins as b\nprohibited = b.eval\n']
                else:
                    prefixes = [f'import {forbidden} as prohibited\n']
                for prefix in prefixes:
                    with self.subTest(statement=statement.name, forbidden=forbidden, prefix=prefix):
                        answer = self.submit(prefix + self.reference(statement).read_text())
                        result = grade(statement, answer)
                        self.assertFalse(result['ok'])
                        self.assertIn('proibido', result['detail'])

    def test_session_deadline_catalog_and_round_trip(self):
        session = self.session()
        metadata = json.loads((self.root / 'src/subjects.json').read_text())
        expected_levels = 3 if metadata['rank'] == '05' else 2
        self.assertEqual(len(session['exercises']), expected_levels)
        self.assertEqual(session['deadline'] - session['started_at'], 14400)
        self.assertEqual(simulator.load_session(self.root), session)

    def test_complete_exam_and_progress(self):
        session = self.session()
        total = len(session['exercises'])
        for step, exercise in enumerate(session['exercises'], 1):
            self.deliver(exercise)
            self.output.seek(0)
            self.output.truncate(0)
            with patch('src.simulator.clear_screen') as clear:
                simulator.correct(self.root, session)
                clear.assert_called_once()
            output = self.output.getvalue()
            self.assertIn(f'✅ correto\nProgresso: {step}/{total}', output)
            self.assertNotIn(f'Arquivo exigido: rendu/{Path(exercise).stem}.py', output)
            if step < total:
                next_name = Path(session['exercises'][step]).stem
                self.assertIn(f'Arquivo exigido: rendu/{next_name}.py', output)
            else:
                self.assertNotIn('Arquivo exigido:', output)
            self.assertEqual(session['current'], step)
        self.assertEqual(session['status'], 'passed')
        self.assertEqual(simulator.load_session(self.root)['status'], 'passed')

    def test_rejection_does_not_advance_and_hides_details(self):
        session = self.session()
        with patch('src.simulator.grade', return_value={'ok': False, 'detail': 'private test'}):
            simulator.correct(self.root, session)
        self.assertEqual(session['current'], 0)
        self.assertNotIn('private test', self.output.getvalue())
        self.assertIn('❌ incorreto', self.output.getvalue())

    def test_practice_has_no_deadline_and_shows_failure(self):
        session = self.session('practice')
        self.assertIsNone(session['deadline'])
        with patch('src.simulator.grade', return_value={'ok': False, 'detail': 'diagnóstico'}):
            simulator.correct(self.root, session)
        self.assertIn('diagnóstico', self.output.getvalue())
        self.deliver(session['exercises'][0])
        simulator.correct(self.root, session)
        self.assertEqual(session['current'], 0)
        self.assertIn('Progresso: 1/1', self.output.getvalue())

    def test_restart_archives_hidden_files_and_state(self):
        first = self.session()
        (self.root / 'rendu/.hidden').write_text('saved')
        nested = self.root / 'rendu/nested'
        nested.mkdir()
        (nested / 'work.py').write_text('my answer')
        first['current'] = 1
        simulator.save_session(self.root, first)
        second = self.session()
        self.assertEqual(second['current'], 0)
        self.assertEqual(second['attempts'], [])
        self.assertEqual(list((self.root / 'rendu').iterdir()), [])
        archive = next((self.root / 'historico').iterdir())
        self.assertEqual((archive / 'rendu/.hidden').read_text(), 'saved')
        self.assertEqual((archive / 'rendu/nested/work.py').read_text(), 'my answer')
        self.assertEqual(json.loads((archive / '.session.json').read_text()), first)

    def test_corrupt_state_is_preserved_on_restart(self):
        self.session()
        (self.root / 'src/.session.json').write_text('invalid json')
        with patch('src.simulator.run_session'):
            simulator.start(self.root, 'exam')
        archive = next((self.root / 'historico').iterdir())
        self.assertEqual((archive / '.session.json').read_text(), 'invalid json')
        self.assertEqual(simulator.load_session(self.root)['status'], 'active')

    def test_practice_cancel_leaves_existing_delivery_untouched(self):
        self.session()
        (self.root / 'rendu/work.py').write_text('saved')
        with patch('src.simulator.read_command', return_value='voltar'):
            simulator.start(self.root, 'practice')
        self.assertEqual((self.root / 'rendu/work.py').read_text(), 'saved')
        self.assertFalse((self.root / 'historico').exists())

    def test_practice_after_exam_starts_empty(self):
        self.session()
        (self.root / 'rendu/work.py').write_text('saved')
        with patch('src.simulator.read_command', return_value='1'), patch('src.simulator.run_session'):
            simulator.start(self.root, 'practice')
        self.assertEqual(list((self.root / 'rendu').iterdir()), [])
        self.assertIsNone(simulator.load_session(self.root)['deadline'])

    def test_statements_include_exact_interfaces_and_no_auxiliary_delivery_files(self):
        self.session()
        for statement in self.statements:
            relative = statement.relative_to(self.root / 'gabarito/enunciados')
            text = simulator.statement_text(self.root, str(relative))
            self.assertIn(subject_for(statement)['signature'], text)
            self.assertIn('rendu/' + statement.with_suffix('.py').name, text)
        self.assertEqual(list((self.root / 'rendu').iterdir()), [])
        self.assertTrue((self.root / 'src/.session.json').exists())

    def test_expiry_prevents_grading(self):
        session = self.session()
        session['deadline'] = time.time() - 1
        with self.assertRaises(simulator.TimeExpired):
            simulator.correct(self.root, session)
        simulator.run_session(self.root, session)
        self.assertEqual(session['status'], 'expired')
        self.assertEqual(session['attempts'], [])

    def test_expiry_during_grading_does_not_award_progress(self):
        session = self.session()
        deadline = session['deadline']
        with patch('src.simulator.grade', return_value={'ok': True}), patch('src.simulator.time.time', side_effect=[deadline - 1, deadline + 1]):
            with self.assertRaises(simulator.TimeExpired):
                simulator.correct(self.root, session)
        self.assertEqual(session['current'], 0)

    def test_inconsistent_state_is_rejected(self):
        session = self.session()
        session['exercises'] = ['../../other.txt']
        simulator.save_session(self.root, session)
        with self.assertRaises(ValueError):
            simulator.load_session(self.root)

    def test_real_cli_start_status_and_exit_in_temporary_project(self):
        for file in ('main.py', 'src/simulator.py', 'src/terminal.py', 'src/grader.py', 'src/grader_worker.py', 'src/exam_cases.py'):
            shutil.copy2(ROOT / file, self.root / file)
        result = subprocess.run([sys.executable, '-B', 'main.py'], cwd=self.root, input='2\nstatus\nsair\n3\n', text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SIMULADO RANK', result.stdout)
        self.assertIn('Restante:', result.stdout)
        self.assertEqual(list((self.root / 'rendu').iterdir()), [])

    def test_equivalent_schedules_and_match_order_are_accepted(self):
        for statement in self.statements:
            name = subject_for(statement)['name']
            if name not in ('py_room_scheduler', 'py_prism_detector'):
                continue
            source = self.reference(statement).read_text()
            if name == 'py_room_scheduler':
                source += '\noriginal = py_room_scheduler\ndef py_room_scheduler(meetings):\n    result = original(meetings)\n    result["schedule"].reverse()\n    return result\n'
            else:
                source += '\noriginal = prism_detector\ndef prism_detector(grid, pattern):\n    return list(reversed(original(grid, pattern)))\n'
            self.assertTrue(grade(statement, self.submit(source))['ok'])

    def test_serialization_format_is_free(self):
        for statement in self.statements:
            if subject_for(statement)['name'] != 'pack_strings':
                continue
            source = 'import base64\ndef pack(strs):\n    return ";".join("x" + base64.b64encode(s.encode()).decode() for s in strs)\ndef unpack(s):\n    return [base64.b64decode(part[1:]).decode() for part in s.split(";")] if s else []\n'
            self.assertTrue(grade(statement, self.submit(source))['ok'])

    def test_timer_colors_and_redirected_output(self):
        from src.terminal import paint, timer_text
        self.assertEqual(paint('text', 'green'), 'text')
        self.assertEqual(simulator.clock_text(3661), '01:01:01')
        self.assertEqual(simulator.clock_text(-1), '00:00:00')
        with patch('src.terminal.paint', side_effect=lambda text, color: color):
            self.assertEqual(timer_text(3600, 'time'), 'cyan')
            self.assertEqual(timer_text(1000, 'time'), 'yellow')
            self.assertEqual(timer_text(200, 'time'), 'red')


if __name__ == '__main__':
    unittest.main()
