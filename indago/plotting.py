"""Independent snapshots of cycle-result plots."""
from copy import deepcopy


def copy_cycle_figure(source):
    """Preserve all cycle artists and limits without altering the embedded figure."""
    figure = deepcopy(source)
    raw, cycle = figure.axes
    figure.delaxes(raw)
    cycle.set_subplotspec(figure.add_gridspec(1, 1)[0])
    figure.set_size_inches(11, 8)
    return figure
