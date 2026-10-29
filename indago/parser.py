"""Parser for CMC nanoindentation text exports."""
from pathlib import Path
import math
import re

NUMBER = r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?"
RESULT = re.compile(rf"^\s*(.+?)\s*=\s*({NUMBER})\s*(.*?)\s*$")
CYCLE = re.compile(r"\s*Cycle\s*#\s*(\d+)", re.I)
HEADERS = tuple(re.compile(p, re.I) for p in
                (r"Time\s*\(s\)", r"Pd\s*\(nm\)", r"Fn\s*\(mN\)"))


def parse_cmc(text, name):
    curve = dict(name=name, raw=[], cycles=[], units={}, warnings=[])
    current = None
    columns = None
    invalid = 0
    for line in text.lstrip("\ufeff").splitlines():
        if columns is not None:
            if not line.strip():
                continue
            try:
                fields = line.split()
                point = tuple(float(fields[i].replace(',', '.')) for i in columns)
                if not all(math.isfinite(v) for v in point):
                    raise ValueError('Nonfinite measurement')
                curve['raw'].append(point)
            except (IndexError, ValueError):
                invalid += 1
            continue
        match = CYCLE.match(line)
        if match:
            current = dict(cycle=int(match[1]), values={})
            curve['cycles'].append(current)
            continue
        if all(pattern.search(line) for pattern in HEADERS):
            headers = re.split(r"\t+|\s{2,}", line.strip())
            columns = [next((i for i, h in enumerate(headers) if pattern.match(h)), default)
                       for default, pattern in enumerate(HEADERS)]
            current = None
            continue
        if current is not None:
            match = RESULT.match(line)
            if match:
                key, value, unit = match.groups()
                current['values'][key.strip()] = float(value.replace(',', '.'))
                if unit.strip():
                    curve['units'][key.strip()] = ' '.join(unit.split())
    if not curve['raw']:
        raise ValueError('No measured data: expected Time (s), Pd (nm), Fn (mN).')
    if not curve['cycles']:
        curve['warnings'].append('No cycle summaries found.')
    if invalid:
        curve['warnings'].append(f'{invalid} invalid measurement rows skipped.')
    return curve


def read_curve(path, name=None):
    path = Path(path)
    data = path.read_bytes()
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = data.decode('cp1252', errors='replace')
    return parse_cmc(text, name or path.name)
