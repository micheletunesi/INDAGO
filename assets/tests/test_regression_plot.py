"""Exercise regression overlays without requiring a desktop or Matplotlib."""
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from indago.analysis import regression_points, linear_regression


class RegressionPlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[2] / 'indago' / 'ui.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        app = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        method = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == 'draw_regression')
        scope = dict(math=math, regression_points=regression_points, linear_regression=linear_regression)
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
        cls.draw_fit = staticmethod(scope['draw_regression'])

    def test_top_labels_no_point_highlighting_and_red_line(self):
        var = lambda value: SimpleNamespace(get=lambda: value)
        axis = Mock()
        app = SimpleNamespace(xaxis=var('Normalized depth'), regression_enabled=var(True),
                              first_cycle=var(1), last_cycle=var(3), average_mode=var(False),
                              curves=[dict(cycles=[dict(cycle=i, values=dict(hc=i, HIT=2*i+1))
                                                   for i in (1, 2, 3)])],
                              cycle_ax=axis, label=lambda key: key, set_regression_text=Mock())
        self.draw_fit(app, 'HIT', 'hc')
        calls = axis.annotate.call_args_list
        self.assertEqual([c.args[0] for c in calls], ['Fit-', 'Fit+'])
        self.assertTrue(all(c.kwargs['xy'][1] == 1 and c.kwargs['xytext'][1] > 0 for c in calls))
        self.assertEqual(axis.axvline.call_count, 2)
        self.assertEqual(axis.plot.call_count, 1)  # fit line only; no point overlay
        self.assertEqual(axis.plot.call_args.kwargs['color'], 'red')

    def test_other_axes_never_draw_regression(self):
        app = SimpleNamespace(xaxis=SimpleNamespace(get=lambda: 'Contact depth (hc)'))
        self.draw_fit(app, 'HIT', 'hc')  # no other state should be accessed
