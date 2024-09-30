from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from _dynaconf.datastructures import TreePath, DynaconfToken, Loader


class BaseMergeTree:
    def get(self, path: TreePath):
        raise NotImplementedError()

    def add(self, path: TreePath, value):
        raise NotImplementedError()

    def add_meta_token(self, path: TreePath, token: DynaconfToken):
        raise NotImplementedError()

    def get_meta_token(
        self, path: TreePath, token_id: Optional[str] = None
    ) -> tuple[DynaconfToken, ...] | DynaconfToken:
        raise NotImplementedError()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._merge_operation_data!r}, {self._meta_token_data!r})"

    def __str__(self):
        return f"{self.__class__.__name__}(\n    {self._merge_operation_data=},\n    {self._meta_token_data=}\n)"

    def __eq__(self, o):
        raise NotImplementedError()


class BaseLoadRegistry:
    def get_loader(self, loader_id: str) -> Loader:
        raise NotImplementedError()


class BaseOperation:
    """
    This represents a merge operation to be performed onto a container (dict or list).

    ALLOWED_MATCH_KEY_CASES declares the cases when the operation should be performed.
    """

    ALLOWED_MATCH_KEY_CASES: list[str] = []

    def __init__(self, key: int | str, value):
        raise NotImplementedError()

    def run(self, container: dict | list, **ctx):
        raise NotImplementedError()

    def _dict_handler(self, container: dict, **kwargs):
        raise NotImplementedError()

    def _list_handler(self, container: list, **kwargs):
        raise NotImplementedError()

    def _validate(self, container: dict | list):
        """Validate if that operation is allowed in the given context.

        By default, if requirements are not met the operation will no-op quietly.
        """
        raise NotImplementedError()

    def _get_match_case(self, container: dict | list, key: str | int):
        """Get a match case for @key in @container.

        Match case refers to how keys from base match with the keys from incoming.
        For dicts, that is the 'key' attr. For list, that is the 'index'.

        There can be 3 key-matching cases:
        * (base=True, income=True): That's a "conflict", as the two have the same key.
        * (base=False, income=True): That's a "income_only", as only the income has the key.
        * (base=True, income=False): That's a "base_only", as only the base has the key. We cant
            get this match-case by only comparing the income key (we would need the income container),
            but we probably don't need to handle this (maybe for income-mask feature, but let it come).
        """
        raise NotImplementedError()

    def __eq__(selef, o):
        raise NotImplementedError()
