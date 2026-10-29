"""Export cycle summaries to XLSX using only Python's standard library."""
import math
import os
from pathlib import Path
import re
import tempfile
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile, ZIP_DEFLATED

NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def column_name(index):
    result = ''
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xml(element):
    return tostring(element, encoding='utf-8', xml_declaration=True)


def export_summary(curves, filename):
    # Keep distinct units in separate columns rather than silently mixing them.
    properties = list(dict.fromkeys((key, c['units'].get(key, ''))
                      for c in curves for cycle in c['cycles'] for key in cycle['values']))
    headers = ['Indentation', 'Source file', 'Included', 'Cycle'] + [
        f'{key} ({unit})' if unit else key for key, unit in properties]
    rows = []
    for index, curve in enumerate(curves, 1):
        for cycle in curve['cycles']:
            rows.append(([index, curve['name'], 'Yes' if curve.get('included', True) else 'No',
                          cycle['cycle']] + [cycle['values'].get(key) if curve['units'].get(key, '') == unit
                                             else None for key, unit in properties],
                         curve.get('included', True)))
    if not rows:
        raise ValueError('No cycle results to export.')
    if len(rows) + 1 > 1048576 or len(headers) > 16384:
        raise ValueError('Summary exceeds Excel worksheet limits.')
    sheet = Element('worksheet', xmlns=NS)
    end = f'{column_name(len(headers))}{len(rows)+1}'
    SubElement(sheet, 'dimension', ref=f'A1:{end}')
    views = SubElement(sheet, 'sheetViews')
    view = SubElement(views, 'sheetView', workbookViewId='0')
    SubElement(view, 'pane', ySplit='1', topLeftCell='A2', activePane='bottomLeft', state='frozen')
    cols = SubElement(sheet, 'cols')
    for i, header in enumerate(headers, 1):
        SubElement(cols, 'col', min=str(i), max=str(i),
                   width=str(48 if i == 2 else min(38, max(16, len(header)+2))), customWidth='1')
    data = SubElement(sheet, 'sheetData')
    for r, (values, included) in enumerate([(headers, True)] + rows, 1):
        row = SubElement(data, 'row', r=str(r))
        for c, value in enumerate(values, 1):
            if value is None or (isinstance(value, float) and not math.isfinite(value)):
                continue
            style = '1' if r == 1 else '2' if included else '3'
            cell = SubElement(row, 'c', r=f'{column_name(c)}{r}', s=style)
            if isinstance(value, (int, float)):
                SubElement(cell, 'v').text = str(value)
            else:
                # Inline strings preserve filenames literally, including leading '='.
                cell.set('t', 'inlineStr')
                text = SubElement(SubElement(cell, 'is'), 't')
                text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                text.text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(value))[:32767]
    SubElement(sheet, 'autoFilter', ref=f'A1:{end}')
    styles = f'''<styleSheet xmlns="{NS}">
    <fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font><font><color rgb="FF888888"/><sz val="11"/><name val="Calibri"/></font></fonts>
    <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF173B52"/><bgColor indexed="64"/></patternFill></fill></fills>
    <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
    <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
    <cellXfs count="4"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>
    <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''
    parts = {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>',
        '_rels/.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        'xl/workbook.xml': f'<workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Cycle results" sheetId="1" r:id="rId1"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels': '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>',
        'xl/styles.xml': styles, 'xl/worksheets/sheet1.xml': xml(sheet)}
    destination = Path(filename)
    handle, temporary = tempfile.mkstemp(suffix='.xlsx', dir=destination.parent)
    os.close(handle)
    try:
        with ZipFile(temporary, 'w', ZIP_DEFLATED) as archive:
            for name, content in parts.items():
                archive.writestr(name, content)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return len(rows)
