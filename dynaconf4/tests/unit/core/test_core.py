from dynaconflib.datastructures import LoadRequest, SchemaTree, DataDict
from dynaconflib.core import DynaconfCore


def create_load_request(data) -> LoadRequest:
    return LoadRequest(
        "builtin.direct", uri="test_core", direct_data=data, namespace_in_root=False
    )


def test_core():
    schema = SchemaTree()
    schema.add(["a"], dict)
    schema.add(["a", "x"], int)
    schema.add(["a", "y"], bool)
    core = DynaconfCore("dynaconf_test", schema)
    default_namespace = core.namespaces.get_current()

    # load/merge 1
    data_input = {"a": {"x": 1, "y": True}}

    load_request = create_load_request(data_input)
    core.enqueue(load_request=load_request)
    assert load_request in core.load_request_q
    core.debug()

    core.process_api(load=all)
    assert load_request not in core.load_request_q
    core.debug()

    assert default_namespace.data == DataDict()
    core.process_api(merge=all)
    assert default_namespace.data == data_input

    # load/merge 2
    data_input = {"a": {"y": False}}
    load_request = create_load_request(data_input)
    core.enqueue(load_request=load_request)
    assert load_request in core.load_request_q

    core.process_api(load=all)
    assert load_request not in core.load_request_q

    core.process_api(merge=all)
    assert default_namespace.data == {"a": {"x": 1, "y": False}}

    # TODO: evalute
    core.process_api(merge_lazy=all)

    # TODO: validate
