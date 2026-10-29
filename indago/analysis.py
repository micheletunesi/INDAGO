"""Normalization, cycle averaging and linear regression; no GUI dependencies."""
import math
from statistics import mean, stdev

POWERS = (2, 1, .5, .25, .125)


def read_parameters(coefficient_texts, thickness_text):
    """Blank coefficients are zero; thickness must be finite and positive."""
    try:
        coefficients = tuple(float(s.strip().replace(',', '.')) if s.strip() else 0.
                             for s in coefficient_texts)
    except ValueError as exc:
        raise ValueError('Enter numeric area coefficients (blank = 0).') from exc
    if len(coefficients) != 5 or not all(math.isfinite(c) for c in coefficients):
        raise ValueError('Enter five finite area coefficients (blank = 0).')
    try:
        thickness = float(thickness_text.strip().replace(',', '.'))
    except ValueError as exc:
        raise ValueError('Enter film thickness in nm, greater than zero.') from exc
    if not math.isfinite(thickness) or thickness <= 0:
        raise ValueError('Film thickness must be finite and greater than zero.')
    return coefficients, thickness


def normalized_depth(hc, coefficients, thickness):
    """Return sqrt(A(hc)/pi)/t; invalid depths/areas are omitted as NaN."""
    if not math.isfinite(hc) or hc < 0 or not math.isfinite(thickness) or thickness <= 0:
        return math.nan
    try:
        area = sum(c * hc ** p for c, p in zip(coefficients, POWERS) if c != 0)
        if not math.isfinite(area) or area < 0:
            return math.nan
        return math.sqrt(area / math.pi) / thickness
    except (OverflowError, ValueError):
        return math.nan


def cycle_x(cycle, xkey):
    if callable(xkey):
        return xkey(cycle)
    return cycle['cycle'] if xkey is None else cycle['values'].get(xkey, math.nan)


def cycle_averages(curves, property_key, xkey=None):
    """Return cycle, mean x, mean y, n and 2*sample-stdev/sqrt(n).

    Group matching cycle numbers. Each curve contributes at most once per cycle.
    A missing x or y omits that contribution. Singleton uncertainty is undefined.
    """
    groups = {}
    for curve in curves:
        if not curve.get('included', True):
            continue
        seen = set()
        for cycle in curve['cycles']:
            number = cycle['cycle']
            x = cycle_x(cycle, xkey)
            y = cycle['values'].get(property_key, math.nan)
            if number not in seen and math.isfinite(x) and math.isfinite(y):
                groups.setdefault(number, []).append((x, y))
                seen.add(number)
    rows = []
    for number, points in sorted(groups.items()):
        ys = [p[1] for p in points]
        n = len(ys)
        rows.append(dict(cycle=number, x=mean(p[0] for p in points),
                         y=mean(ys), n=n,
                         uncertainty=2 * stdev(ys) / math.sqrt(n) if n > 1 else math.nan))
    return rows


def regression_points(curves, property_key, xkey, first, last, averaged=False):
    # Apply the same exclusion gate before either aggregation or point collection.
    curves = [c for c in curves if c.get('included', True)]
    if averaged:
        return [(r['x'], r['y']) for r in cycle_averages(curves, property_key, xkey)
                if first <= r['cycle'] <= last]
    return [(x, y) for c in curves
            for p in c['cycles'] if first <= p['cycle'] <= last
            for x, y in [(cycle_x(p, xkey), p['values'].get(property_key, math.nan))]
            if math.isfinite(x) and math.isfinite(y)]


def linear_regression(points):
    points = [(x, y) for x, y in points if math.isfinite(x) and math.isfinite(y)]
    n = len(points)
    if n < 3:
        raise ValueError('Select at least 3 valid points to estimate fit uncertainty.')
    mx, my = mean(x for x, y in points), mean(y for x, y in points)
    sxx = sum((x-mx)**2 for x, y in points)
    syy = sum((y-my)**2 for x, y in points)
    sxy = sum((x-mx)*(y-my) for x, y in points)
    if sxx <= 0:
        raise ValueError('Regression needs at least two distinct x values.')
    slope = sxy / sxx
    intercept = my - slope*mx
    sse = sum(((y-my)-slope*(x-mx))**2 for x, y in points)
    variance = sse/(n-2)
    r = max(-1., min(1., sxy/math.sqrt(sxx)/math.sqrt(syy))) if syy > 0 else math.nan
    r2 = max(0., min(1., 1-sse/syy)) if syy > 0 else math.nan
    result = dict(n=n, df=n-2, slope=slope, intercept=intercept,
                  slope_se=math.sqrt(variance/sxx),
                  intercept_se=math.sqrt(variance*(1/n+mx*mx/sxx)),
                  r=r, r2=r2, adjusted_r2=1-(1-r2)*(n-1)/(n-2),
                  sse=sse, residual_sd=math.sqrt(variance), rmse=math.sqrt(sse/n),
                  xmin=min(x for x, y in points), xmax=max(x for x, y in points))
    if not all(math.isfinite(result[k]) for k in ('slope', 'intercept', 'slope_se', 'intercept_se')):
        raise ValueError('Numerical range too large for a reliable regression.')
    return result
