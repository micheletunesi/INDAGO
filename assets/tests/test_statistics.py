import math
import unittest
from indago.analysis import cycle_averages


def curve(rows, included=True):
    return dict(included=included, cycles=[dict(cycle=n, values=v) for n, v in rows])


class AverageTests(unittest.TestCase):
    def test_sample_standard_deviation_and_exclusion(self):
        curves = [curve([(1, dict(HIT=y, hmax=x))]) for y, x in [(2, 10), (4, 20), (6, 30)]]
        curves.append(curve([(1, dict(HIT=100, hmax=100))], included=False))
        row, = cycle_averages(curves, 'HIT', 'hmax')
        self.assertEqual((row['y'], row['x'], row['n']), (4, 20, 3))
        self.assertAlmostEqual(row['uncertainty'], 4 / math.sqrt(3))
        curves[-1]['included'] = True
        self.assertEqual(cycle_averages(curves, 'HIT')[0]['n'], 4)

    def test_missing_nonfinite_and_singletons(self):
        curves = [curve([(2, dict(HIT=3)), (1, dict(HIT=1))]),
                  curve([(1, {}), (2, dict(HIT=math.nan))])]
        rows = cycle_averages(curves, 'HIT')
        self.assertEqual([r['cycle'] for r in rows], [1, 2])
        self.assertTrue(all(r['n'] == 1 and math.isnan(r['uncertainty']) for r in rows))
        self.assertEqual(cycle_averages(curves, 'HIT', 'hmax'), [])
        self.assertEqual(cycle_averages([curve([(1, dict(HIT=2))], False)], 'HIT'), [])

    def test_duplicate_cycle_does_not_inflate_n(self):
        rows = cycle_averages([curve([(1, dict(HIT=4)), (1, dict(HIT=8))])], 'HIT')
        self.assertEqual(rows[0]['n'], 1)


if __name__ == '__main__':
    unittest.main()
