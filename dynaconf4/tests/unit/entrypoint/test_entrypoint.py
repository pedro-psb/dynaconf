from dynaconflib.entrypoint import Dynaconf


def test_entrypoint_noschema():
    settings = Dynaconf(data={"a": 1, "b": 2})
    settings["c"] = 3
    core = settings.__get_dynaconf__()
    assert settings == {"a": 1, "b": 2, "c": 3}

    # set operation on the frontend object should reflect on the
    # internal active namespace.
    core = settings.__get_dynaconf__()
    current_ns = core.namespaces.get()
    assert current_ns.data == settings
    # core.debug()
    # print(settings)
