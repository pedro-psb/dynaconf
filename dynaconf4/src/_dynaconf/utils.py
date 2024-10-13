from __future__ import annotations
import rich.pretty
import rich.panel

# _print = rich.print


class Empty:
    __slots__ = ()

    def __repr__(self):
        return "EMPTY"


empty = Empty()


def print_kwargs(**kwargs):
    for k, v in kwargs.items():
        section_print(k, v)


def section_print(name: str, data: dict | str):
    if not isinstance(data, str):
        rich.print(
            rich.panel.Panel(rich.pretty.Pretty(data, expand_all=True), title=name)
        )
    else:
        rich.print(rich.panel.Panel(data, title=name))


def pprint(obj: dict | list, indent=4):
    """Pretty print a container object with linebreak similar to json.dumps()."""
    rich.print(rich.pretty.Pretty(obj, expand_all=True))


if __name__ == "__main__":
    mydict = [
        {
            "name": "Alice",
            "age": 30,
            "children": [
                {"name": "Bob", "age": 5, "listy": [True, 2, 3, 4, 5, "foo"]},
                {"name": "Charlie", "age": 3},
            ],
            "married": True,
        },
        "foo",
        123,
        {"something": False, "otherthing": True},
    ]
    pprint(mydict)
