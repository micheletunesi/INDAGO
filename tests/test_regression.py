import math
import unittest
from indago.analysis import linear_regression, regression_points


class RegressionTests(unittest.TestCase):
    def test_known_fit_and_standard_errors(self):
        fit = linear_regression(list(zip([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])))
        for key, expected in dict(slope=.6, intercept=2.2, sse=2.4, r2=.6,
                                  adjusted_r2=1-.4*4/3, residual_sd=math.sqrt(.8),
                                  slope_se=math.sqrt(.08), intercept_se=math.sqrt(.88),
                                  r=math.sqrt(.6), rmse=math.sqrt(2.4/5)).items():
            self.assertAlmostEqual(fit[key], expected, msg=key)
        self.assertEqual(fit['df'], 3)

    def test_exact_line_constant_y_and_degenerate_x(self):
        fit = linear_regression([(1, 5), (2, 8), (3, 11)])
        self.assertEqual((fit['intercept'], fit['slope'], fit['intercept_se']), (2, 3, 0))
        self.assertEqual(fit['r'], 1)
        fit = linear_regression([(1, 4), (2, 4), (3, 4)])
        self.assertTrue(math.isnan(fit['r']))
        self.assertTrue(math.isnan(fit['r2']))
        for points in [[], [(1, 2), (2, 3)], [(1, 2), (1, 3), (1, 4)]]:
            with self.assertRaises(ValueError):
                linear_regression(points)

    def test_cycle_bounds_exclusion_and_averaging(self):
        def curve(offset, included=True):
            return dict(included=included, cycles=[dict(cycle=i, values=dict(hc=i, HIT=2*i+offset)) for i in range(1, 6)])
        curves = [curve(0), curve(2), curve(100, False)]
        points = regression_points(curves, 'HIT', 'hc', 2, 4)
        self.assertEqual(len(points), 6)
        self.assertEqual(linear_regression(points)['intercept'], 1)
        points = regression_points(curves, 'HIT', 'hc', 2, 4, averaged=True)
        self.assertEqual(points, [(2, 5), (3, 7), (4, 9)])
        self.assertEqual(linear_regression(points)['intercept_se'], 0)
        transformed = regression_points(curves, 'HIT', lambda p: p['values']['hc']/10, 2, 4, True)
        self.assertAlmostEqual(linear_regression(transformed)['slope'], 20)
        self.assertEqual(regression_points(curves, 'missing', 'hc', 2, 4), [])

    def test_excluded_values_never_reach_either_fit_mode(self):
        good = dict(cycles=[dict(cycle=i, values=dict(hc=i, HIT=3*i+2)) for i in range(1, 5)])
        excluded = dict(included=False, cycles=[dict(cycle=i, values=dict(hc=100*i, HIT=-1000*i)) for i in range(1, 5)])
        for averaged in (False, True):
            baseline = regression_points([good], 'HIT', 'hc', 1, 4, averaged)
            points = regression_points([good, excluded], 'HIT', 'hc', 1, 4, averaged)
            self.assertEqual(points, baseline)
            self.assertEqual(linear_regression(points)['intercept'], 2)
            self.assertEqual(regression_points([excluded], 'HIT', 'hc', 1, 4, averaged), [])


if __name__ == '__main__':
    unittest.main()
