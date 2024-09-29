from __future__ import annotations
from rich import print as _print
from typing import Optional

def section_print(name: str, data: dict):
    _print(name)
    pprint(data)

def pprint(obj: dict | list, indent=4):
    """Pretty print a container object with linebreak similar to json.dumps()."""

    def _pprint(_data, indent=4, level=0):
        spacing = " " * (level * indent)

        if isinstance(_data, dict):
            _print("{")
            for i, (key, value) in enumerate(_data.items()):
                _print(f'{spacing}{indent * " "}"{key}": ', end="")
                if isinstance(value, (dict, list)):
                    _pprint(value, indent, level + 1)
                else:
                    _print(f'{repr(value)}{"," if i < len(_data) - 1 else ""}')
            closing_bracket = "%s}" if level == 0 else "%s},"
            _print(closing_bracket % spacing)

        elif isinstance(_data, list):
            _print("[")
            for i, item in enumerate(_data):
                _print(f'{spacing}{indent * " "}', end="")
                if isinstance(item, (dict, list)):
                    _pprint(item, indent, level + 1)
                else:
                    _print(f'{repr(item)}{"," if i < len(_data) - 1 else ""}')
            closing_bracket = "%s]" if level == 0 else "%s],"
            _print(closing_bracket % spacing)

    _pprint(obj)
    print()


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
