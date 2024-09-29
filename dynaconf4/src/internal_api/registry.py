from internal_api.datastructures import TokenCallback, TokenName
from internal_api.abstract import BaseOperation


class TokenRegistry:
    def __init__(self):
        def Int(o, *args, **kwargs):
            return int(o)

        def Str(o, *args, **kwargs):
            return str(o)

        def Sum(o, *args, **kwargs):
            return sum(o)

        self._transformers = {
            "int": TokenCallback(Int),
            "str": TokenCallback(Str),
            "sum": TokenCallback(Sum),
            "add": TokenCallback(Add),
        }

    def get_callback(self, token_id: str) -> TokenCallback:
        callback = self._transformers.get(token_id)
        if not callback:
            raise RuntimeError(f"No TokenCallback registered for token: {token_id!r}")
        return callback


def get_builtin_token_operation_map() -> dict[TokenName, type[BaseOperation]]:
    token_op_map: dict[str, type[BaseOperation]] = {
        "merge": Merge,
        "add": Add,
        "replace": Replace,
        "append": Append,
        "append_unique": AppendUnique,
    }
    return token_op_map


class DefaultOperation(BaseOperation):
    """
    This represents a merge operation to be performed onto a container (dict or list).

    ALLOWED_MATCH_KEY_CASES declares the cases when the operation should be performed.
    They are:
    - "conflict": self.key in base.keys()
    - "income_alone": self.key not base.keys()

    The "base_alone" case cannot be treated normally, so we might add a special operation to handle those (or not).
    """

    ALLOWED_MATCH_KEY_CASES: list[str] = []

    def __init__(self, key, value, *args, **kwargs):
        self.key = key
        self.value = value

    def run(self, container: dict | list, **ctx):
        # validate
        if not self._validate(container, **ctx):
            return
        # run
        if isinstance(container, dict):
            self._dict_handler(container, **ctx)
        else:
            self._list_handler(container, **ctx)

    def _validate(self, container: dict | list):
        """Validate if that operation is allowed in the given context.

        By default, if requirements are not met the operation will no-op quietly.
        """
        match_case = self._get_match_case(container, self.key)
        if match_case not in self.ALLOWED_MATCH_KEY_CASES:
            return False
        return True

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
        # None key means its not important (e.g, in Append(None, value))
        if key is None:
            return "conflict"

        if isinstance(container, dict):
            return "conflict" if key in container else "income_alone"
        else:
            index = int(key)
            return "conflict" if index < len(container) else "income_alone"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.key!r}, {self.value!r})"

    def __eq__(self, o):
        return type(self) == type(o) and (self.key, self.value) == (o.key, o.value)


# merge controllers


class Merge(DefaultOperation):
    ALLOWED_MATCH_KEY_CASES = ["conflict"]


class JumpMerge(DefaultOperation):
    ALLOWED_MATCH_KEY_CASES = ["conflict"]


# primitive operation


class Add(DefaultOperation):
    ALLOWED_MATCH_KEY_CASES = ["income_alone"]

    def _dict_handler(self, container: dict, **kwargs):
        container[self.key] = self.value

    def _list_handler(self, container: list, **kwargs):
        container[self.key] = self.value


class Replace(DefaultOperation):
    ALLOWED_MATCH_KEY_CASES = ["conflict"]

    def _dict_handler(self, container: dict, **kwargs):
        container[self.key] = self.value

    def _list_handler(self, container: list, **kwargs):
        container[self.key] = self.value


class Append(DefaultOperation):
    ALLOWED_MATCH_KEY_CASES = ["conflict", "income_alone"]

    def _dict_handler(self, container: dict, **kwargs):
        raise NotImplementedError(
            "This operator is only compatible with list containers."
        )

    def _list_handler(self, container: list, **kwargs):
        container.append(self.value)


class AppendUnique(DefaultOperation):
    """Append unique by comparing value uniquiness."""

    ALLOWED_MATCH_KEY_CASES = ["conflict", "income_alone"]

    def _dict_handler(self, container: dict, **kwargs):
        raise NotImplementedError(
            "This operator is only compatible with list containers."
        )

    def _list_handler(self, container: list, **kwargs):
        if self.value not in container:
            container.append(self.value)
