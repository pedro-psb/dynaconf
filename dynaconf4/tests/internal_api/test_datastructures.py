from internal_api.registry import Add


def test_equallity():
    assert Add("foo", "bar") == Add("foo", "bar")
