Empty = object()


def setup_limit(limit):
    """Use positive int or infinity limit."""
    n = limit or float("inf")
    if n <= 0:
        raise ValueError(f"Limit should be a positive int. Got {limit}.")
    return 0, n


def type_guard(obj, t: type | tuple[type]):
    if not isinstance(obj, t):
        raise TypeError(f"Expected {t}, got {type(obj)}")


def is_last(it, i):
    return i == len(it) - 1
