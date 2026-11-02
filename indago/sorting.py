"""Deterministic natural ordering for measurement paths."""
import re


def natural_path_key(path):
    """Compare digit runs numerically, with a stable tie-break for zero padding."""
    parts = tuple(tuple((1, int(token)) if token.isdigit() else (0, token.casefold())
                        for token in re.split(r'([0-9]+)', part))
                  for part in path.parts)
    return parts, str(path).casefold(), str(path)
