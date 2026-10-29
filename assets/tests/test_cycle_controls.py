"""Validate typed and dragged cycle bounds without a desktop session."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class CycleControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[2] / 'indago' / 'ui.py'
        app = next(n for n in ast.parse(source.read_text(encoding='utf-8')).body if isinstance(n, ast.ClassDef))
        methods = [n for n in app.body if isinstance(n, ast.FunctionDef)
                   and n.name in ('commit_cycle', 'cycle_slider_changed')]
        scope = {}
        exec(compile(ast.Module(body=methods, type_ignores=[]), str(source), 'exec'), scope)
        cls.commit = staticmethod(scope['commit_cycle'])
        cls.slide = staticmethod(scope['cycle_slider_changed'])

    def app(self):
        return SimpleNamespace(first_cycle=Value(2), last_cycle=Value(12),
                               cycle_texts=[Value('2'), Value('12')], cycle_limits=(1, 26),
                               cycle_sliders=[Mock(), Mock()], status=Value(''),
                               canvas=True, schedule_depth_draw=Mock())

    def test_typed_cycle_updates_numeric_value_and_slider(self):
        app = self.app()
        app.cycle_texts[0].set('5')
        self.commit(app, 0)
        self.assertEqual(app.first_cycle.get(), 5)
        app.cycle_sliders[0].set.assert_called_once_with(5)
        app.schedule_depth_draw.assert_called_once()

    def test_invalid_or_blank_entry_preserves_last_valid_cycle(self):
        for text in ('', '0', '27', '2.5', 'abc'):
            app = self.app()
            app.cycle_texts[0].set(text)
            self.commit(app, 0)
            self.assertEqual(app.first_cycle.get(), 2)
            self.assertEqual(app.cycle_texts[0].get(), '2')
            app.schedule_depth_draw.assert_not_called()

    def test_slider_rounds_and_respects_loaded_bounds(self):
        app = self.app()
        self.slide(app, 1, '13.2')
        self.assertEqual(app.last_cycle.get(), 13)
        self.assertEqual(app.cycle_texts[1].get(), '13')
        self.slide(app, 0, '-10')
        self.assertEqual(app.first_cycle.get(), 1)
