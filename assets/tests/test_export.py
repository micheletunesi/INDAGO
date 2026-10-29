from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from indago.export import export_summary

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


class ExportTests(unittest.TestCase):
    def test_results_units_exclusions_and_literal_strings(self):
        curves = [dict(name='=sample & one.txt', included=True,
                       units={'HIT': 'GPa', 'hc': 'nm'},
                       cycles=[dict(cycle=1, values={'HIT': .5, 'hc': 42}),
                               dict(cycle=2, values={'hc': 80})]),
                  dict(name='two.txt', included=False, units={'HIT': 'MPa'},
                       cycles=[dict(cycle=1, values={'HIT': 500})])]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'summary.xlsx'
            self.assertEqual(export_summary(curves, path), 3)
            with ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                for name in archive.namelist():
                    ET.fromstring(archive.read(name))
                sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
                cells = {c.attrib['r']: c for c in sheet.findall('.//s:c', NS)}
                self.assertEqual(cells['B2'].find('s:is/s:t', NS).text, '=sample & one.txt')
                self.assertIsNone(cells['B2'].find('s:f', NS))
                self.assertEqual(cells['E1'].find('s:is/s:t', NS).text, 'HIT (GPa)')
                self.assertEqual(cells['G1'].find('s:is/s:t', NS).text, 'HIT (MPa)')
                self.assertEqual(cells['E2'].find('s:v', NS).text, '0.5')
                self.assertNotIn('E3', cells)
                self.assertNotIn('E4', cells)
                self.assertEqual(cells['G4'].find('s:v', NS).text, '500')
                self.assertEqual(cells['C4'].find('s:is/s:t', NS).text, 'No')
                self.assertEqual(cells['G4'].attrib['s'], '3')
                self.assertEqual(sheet.find('s:autoFilter', NS).attrib['ref'], 'A1:G4')

    def test_empty_results(self):
        with self.assertRaises(ValueError):
            export_summary([], 'unused.xlsx')


if __name__ == '__main__':
    unittest.main()
