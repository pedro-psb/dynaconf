Empty = object()


def type_guard(obj, t: type | tuple[type]):
    if not isinstance(obj, t):
        raise TypeError(f"Expected {t}, got {type(obj)}")


def is_last(it, i):
    return i == len(it) - 1
