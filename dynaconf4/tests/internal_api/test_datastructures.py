from dynaconf_builtin.registry import Add


def test_equallity():
    assert Add("foo", "bar") == Add("foo", "bar")
