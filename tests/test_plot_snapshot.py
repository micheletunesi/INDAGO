"""Verify that snapshots preserve overlays and remain independent."""
import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec('matplotlib'), 'Matplotlib is not installed')
class PlotSnapshotTests(unittest.TestCase):
    def test_cycle_only_snapshot_keeps_artists_limits_and_is_independent(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from indago.plotting import copy_cycle_figure

        source = Figure(constrained_layout=True)
        raw, cycle = source.subplots(2, 1)
        raw.plot([0, 1], [10, 20])
        cycle.errorbar([1, 2], [3, 4], yerr=[.1, .2], capsize=4)
        cycle.plot([0, 2], [2, 4], color='red')
        cycle.axvline(1.5)
        cycle.annotate('Fit+', (2, 1), xycoords=cycle.get_xaxis_transform())
        cycle.set(xlabel='Normalized depth', ylabel='EIT', xlim=(-.2, 3))
        snapshot = copy_cycle_figure(source)
        axis, = snapshot.axes
        self.assertEqual(axis.get_ylabel(), 'EIT')
        self.assertEqual(axis.get_xlim(), cycle.get_xlim())
        self.assertEqual(len(axis.lines), len(cycle.lines))
        self.assertEqual(len(axis.collections), len(cycle.collections))
        self.assertEqual(axis.texts[0].get_text(), 'Fit+')
        FigureCanvasAgg(snapshot).draw()
        cycle.clear()
        self.assertTrue(axis.lines)
        self.assertEqual(len(source.axes), 2)
