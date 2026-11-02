from pathlib import Path
import ast
from queue import Queue
import tempfile
from types import SimpleNamespace
import unittest

from indago.parser import read_curve
from indago.sorting import natural_path_key


class NaturalOrderingTests(unittest.TestCase):
    def test_trailing_numbers_and_extensions(self):
        names = ['sample12.txt', 'sample1.txt', 'sample10.txt', 'sample2.txt']
        result = sorted(map(Path, names), key=natural_path_key)
        self.assertEqual([p.name for p in result],
                         ['sample1.txt', 'sample2.txt', 'sample10.txt', 'sample12.txt'])

    def test_subfolders_and_case(self):
        names = ['batch10/sample1.txt', 'batch2/Sample10.txt', 'batch2/sample2.txt']
        self.assertEqual(sorted(map(Path, names), key=natural_path_key),
                         list(map(Path, [names[2], names[1], names[0]])))

    def test_zero_padding_and_mixed_names_are_deterministic(self):
        names = list(map(Path, ['sample1.txt', 'sample01.txt', 'notes.txt', '2.txt']))
        result = sorted(names, key=natural_path_key)
        self.assertEqual(result, sorted(reversed(names), key=natural_path_key))
        self.assertLess(result.index(Path('sample01.txt')), result.index(Path('sample1.txt')))

    def test_folder_loader_uses_numeric_order_and_skips_hidden_paths(self):
        source = Path(__file__).resolve().parents[1] / 'indago' / 'ui.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        app_class = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in app_class.body if isinstance(n, ast.FunctionDef) and n.name == 'load')
        scope = dict(read_curve=read_curve, natural_path_key=natural_path_key)
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
        app = SimpleNamespace(events=Queue())
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ['batch10/sample1.txt', 'batch2/sample12.txt',
                         'batch2/sample2.txt', '.hidden/sample1.txt', '.ignored.txt']:
                path = folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Cycle # 1\nHIT=1 GPa\nTime (s)\tPd (nm)\tFn (mN)\n0\t1\t2',
                                encoding='utf-8')
            scope['load'](app, folder)
        events = list(app.events.queue)
        kind, (curves, notices, _folder) = events[-1]
        self.assertEqual(kind, 'done')
        self.assertEqual([Path(c['name']).as_posix() for c in curves],
                         ['batch2/sample2.txt', 'batch2/sample12.txt', 'batch10/sample1.txt'])
        self.assertEqual(notices, [])
