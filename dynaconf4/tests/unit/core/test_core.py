from dynaconflib.datastructures import LoadRequest, SchemaTree, DataDict
from dynaconflib.core import DynaconfCore
from dynaconflib.utils import container_items, data_print


def create_load_request(data) -> LoadRequest:
    return LoadRequest(
        "builtin.direct", uri="test_core", direct_data=data, namespace_in_root=False
    )


def assert_data_nodes_are_initialized(data):
    def walk(data):
        if isinstance(data, (dict, list)):
            assert data.__get_dynaconf__()
            for k, v in container_items(data):
                walk(v)

    walk(data)


def test_core_workflow():
    schema = SchemaTree()
    schema.add(["a"], dict)
    schema.add(["a", "x"], int)
    schema.add(["a", "y"], bool)
    core = DynaconfCore("dynaconf_test", schema)
    default_namespace = core.namespaces.get_current()
    frontend_namespace = core.namespaces.get("_frontend")

    # ensure initial data has dynaconf initialized
    for name, ns in core.namespaces.items():
        assert ns.data.__get_dynaconf__()

    # load/merge 1
    data_input = {"a": {"x": 1, "y": True}}

    load_request = create_load_request(data_input)
    core.enqueue(load_request=load_request)
    assert load_request in core.load_request_q
    core.debug()

    core.process_api(load=all)
    assert load_request not in core.load_request_q
    # core.debug()

    assert default_namespace.data == DataDict()
    core.process_api(merge=all)
    assert default_namespace.data == data_input

    assert_data_nodes_are_initialized(frontend_namespace.data)
    data_print(default_namespace.data, debug=True)
    data_print(frontend_namespace.data, debug=True)

    # load/merge 2
    data_input = {"a": {"y": False}}
    load_request = create_load_request(data_input)
    core.enqueue(load_request=load_request)
    assert load_request in core.load_request_q

    core.process_api(load=all)
    assert load_request not in core.load_request_q

    core.process_api(merge=all)
    assert default_namespace.data == {"a": {"x": 1, "y": False}}

    core.debug()

    # TODO: evalute
    core.process_api(merge_lazy=all)

    # TODO: validate
