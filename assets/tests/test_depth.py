import math
import unittest
from indago.analysis import normalized_depth, read_parameters
from indago.analysis import cycle_averages


class DepthTests(unittest.TestCase):
    def test_blank_coefficients_and_validation(self):
        self.assertEqual(read_parameters(['', ' ', '', '', ''], '10'), ((0.,)*5, 10.))
        self.assertEqual(read_parameters(['1,5', '', '', '', ''], '20')[0][0], 1.5)
        for thickness in ['', '0', '-1', 'nan', 'inf', 'abc']:
            with self.assertRaises(ValueError):
                read_parameters(['']*5, thickness)
        for coefficient in ['abc', 'inf', 'nan']:
            with self.assertRaises(ValueError):
                read_parameters([coefficient, '', '', '', ''], '10')

    def test_formula_and_invalid_areas(self):
        self.assertAlmostEqual(normalized_depth(100, (math.pi, 0, 0, 0, 0), 10), 10)
        h = 256
        expected = 2*h**2 + 3*h + 4*h**.5 + 5*h**.25 + 6*h**.125
        self.assertAlmostEqual(normalized_depth(h, (2, 3, 4, 5, 6), 20), math.sqrt(expected/math.pi)/20)
        self.assertEqual(normalized_depth(100, (0,)*5, 10), 0)
        for h, coefficients in [(-1, (1,)*5), (math.nan, (1,)*5), (1, (-1,)*5), (1e308, (1,)*5)]:
            self.assertTrue(math.isnan(normalized_depth(h, coefficients, 10)))

    def test_average_transforms_each_depth_before_averaging(self):
        curves = [dict(cycles=[dict(cycle=1, values=dict(hc=h, HIT=y))]) for h, y in [(1, 2), (9, 4)]]
        transform = lambda p: normalized_depth(p['values']['hc'], (0, math.pi, 0, 0, 0), 1)
        row, = cycle_averages(curves, 'HIT', transform)
        self.assertEqual(row['x'], 2)  # mean(sqrt(1), sqrt(9)), not sqrt(mean(1, 9))
        self.assertEqual(row['y'], 3)
        self.assertEqual(row['n'], 2)
        self.assertAlmostEqual(row['uncertainty'], 2)


if __name__ == '__main__':
    unittest.main()
