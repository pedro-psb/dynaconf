from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable, Any, Sequence

if TYPE_CHECKING:
    from _dynaconf.datastructures import (
        DynaconfToken,
        TreePath,
        MergePolicyRuleAttrWeightMap,
        MergePolicyRuleAttr,
    )


class BaseOptions:
    def print(self):
        raise NotImplementedError()


class BaseSchemaTree:
    def get_key_type(self, key: str | int) -> None | type:
        """Get key type or None if not present."""
        raise NotImplementedError()


# TODO: generalize this structure.
# It should store all types of operations ("terminal" and "container") and lazy tokens.
# Maybe:
# mtree.add_operation(operation_type, path, value)
# mtree.get_operation(operation_type, path)
# mtree.add_lazy_tokens(path, lazy_token)
# mtree.get_lazy_token(path)
# or
# mtree.add(item_type: terminal_op|container_op|lazy_token, path, value)
# mtree.get(item_type: (...^) , path)
# mtree.iter(item_type: (...^))
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
    def get_loader(self, loader_id: str) -> Callable:
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


class BaseValidator:
    """Holds the conditions that should apply to @names and also the validation logic."""

    def __init__(
        self,
        *names: str,
        messages: dict[str, str] | None = None,
        items_validators: list[BaseValidator] | None = None,
        items_lookup: Callable[[Any], Any] | None = None,
        description: str | None = None,
        # conditions
        must_exist: bool | None = None,
        required: bool | None = None,
        condition: Callable[[Any], bool] | None = None,
        when: BaseValidator | None = None,
        env: str | Sequence[str] | None = None,
        **operations: Any,
    ) -> None:
        raise NotImplementedError()

    def validate(
        self,
        settings: dict,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:
        """Raise ValidationError if invalid"""
        raise NotImplementedError()

    def _validate_names(
        self,
        settings: dict,
        env: str | None = None,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        variable_path: tuple | None = None,
    ) -> None:
        raise NotImplementedError()

    def _validate_internal_items(
        self,
        value: Any,
        name: str,
        validators: list[BaseValidator],
        variable_path: tuple | None = None,
    ):
        """Validate internal items of a data structure."""
        raise NotImplementedError()

    @property
    def required(self) -> bool:
        raise NotImplementedError()

    @required.setter
    def required(self, value: bool):
        raise NotImplementedError()

    @property
    def is_type_of(self):
        raise NotImplementedError()

    @is_type_of.setter
    def is_type_of(self, value):
        raise NotImplementedError()

    def __repr__(self):
        raise NotImplementedError()

    def __or__(self, other: BaseValidator) -> BaseCombinedValidator:
        raise NotImplementedError()

    def __and__(self, other: BaseValidator) -> BaseCombinedValidator:
        raise NotImplementedError()

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError()


class BaseCombinedValidator(BaseValidator):
    def __init__(
        self,
        validator_a: BaseValidator,
        validator_b: BaseValidator,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Takes 2 validators and combines the validation"""
        raise NotImplementedError()

    def validate(
        self,
        settings: Any,
        only: str | Sequence | None = None,
        exclude: str | Sequence | None = None,
        only_current_env: bool = False,
        variable_path: tuple | None = None,
    ) -> None:
        raise NotImplementedError()


class BaseMergePolicyRegistry:
    def get_policy_factor_weight_map(self) -> MergePolicyRuleAttrWeightMap:
        raise NotImplementedError()

    def update_policy_factor_weight_map(
        self, policy_priority_definition: list[MergePolicyRuleAttr]
    ):
        raise NotImplementedError()
