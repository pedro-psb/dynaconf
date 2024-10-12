from _dynaconf.coreutils.token_registry import Add


def test_equallity():
    assert Add("foo", "bar") == Add("foo", "bar")
