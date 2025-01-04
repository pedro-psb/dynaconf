from dynaconf import Dynaconf
from dynaconflib.public import inspect_api
from dynaconflib.public.inspect import DataNode
from dynaconflib.utils import data_debug, DynaconfJSONEncoder, container_items
from functools import partial
import rich
import json




def get_history_ids(data):
    return [
        {
            k: [
                f"{p.operation}@{p.load_request.id_string()}:{id(p)%10000}"
                for p in patches
            ]
        }
        for k, patches in data.items()
    ]


def json_print(o):
    rich.print_json(json.dumps(o, cls=DynaconfJSONEncoder))


def rich_print(o):
    rich.print(o)


def test_inspect(monkeypatch):
    monkeypatch.setenv("DYNACONF_A__B", "999")
    settings = Dynaconf(data={"a": {"b": 123}, "c": True})
    result = inspect_api(settings)
    result.print()

