# movement/constraints.py


def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def filter_exact_steps(start, reachable_cells, dice_value):
    """
    Only keep cells that are EXACTLY dice_value steps away
    """
    valid = []

    for cell in reachable_cells:
        if manhattan_distance(start, cell) == dice_value:
            valid.append(cell)

    return valid