Empty = object()


def setup_limit(limit):
    """Use positive int or infinity limit."""
    limit = limit or 0
    n = float("inf") if limit is all else limit
    if n < 0:
        raise ValueError(f"Limit should be a positive int. Got {limit}.")
    return n

def raise_if(condition: bool, exception, e_args=None):
    if condition:
        raise exception()

def type_guard(obj, t: type | tuple[type]):
    if not isinstance(obj, t):
        raise TypeError(f"Expected {t}, got {type(obj)}")


def is_last(it, i):
    return i == len(it) - 1
