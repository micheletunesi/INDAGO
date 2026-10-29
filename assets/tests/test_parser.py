from pathlib import Path
import tempfile
import unittest
from indago.parser import parse_cmc, read_curve


class ParserTests(unittest.TestCase):
    def test_cycles_results_and_invalid_measurements(self):
        text = ('\ufeffIndentation\nCycle # 1\nHIT=0,5 GPa\nhc=42 nm\n'
                'Cycle # 2\nEIT=1.2e1 GPa\nMeasured values\n'
                'Time (s)\tPd (nm)\tFn (mN)\n0\t-1\t0\n1\t2\t3\nbad\n2\tnan\t4\n')
        curve = parse_cmc(text, 'sample')
        self.assertEqual(curve['cycles'][0]['values'], {'HIT': .5, 'hc': 42})
        self.assertEqual(curve['cycles'][1]['values']['EIT'], 12)
        self.assertEqual(curve['raw'], [(0., -1., 0.), (1., 2., 3.)])
        self.assertEqual(curve['warnings'], ['2 invalid measurement rows skipped.'])

    def test_reordered_columns_and_no_summaries(self):
        c = parse_cmc('Fn (mN)\tTime (s)\tPd (nm)\n3\t1\t2', 'sample')
        self.assertEqual(c['raw'], [(1., 2., 3.)])
        self.assertEqual(c['warnings'], ['No cycle summaries found.'])
        with self.assertRaises(ValueError):
            parse_cmc('not an export', 'sample')

    def test_windows_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'sample.txt'
            p.write_bytes('Indentation é\nTime (s)\tPd (nm)\tFn (mN)\n0\t1\t2'.encode('cp1252'))
            self.assertEqual(read_curve(p)['raw'], [(0., 1., 2.)])
