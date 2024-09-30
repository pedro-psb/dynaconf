import functools
from typing import Any, Callable, NamedTuple, Optional

from _dynaconf.datastructures import (
    DynaconfToken,
    Stack,
    TreePath,
    is_token,
    ensure_rooted,
    MergeTree,
)
from _dynaconf.abstract import BaseOperation, BaseMergeTree
from _dynaconf.token_registry import Replace, get_builtin_token_operation_map

from _dynaconf.tokenize import TokenRegistry, create_token, tokenize


class Item(NamedTuple):
    container_path: TreePath
    key: str | int
    value: Any


class ContextChange(NamedTuple):
    new_container_path: TreePath
    new_container_type: dict | list


def create_merge_tree(
    data: dict,
    mtree_cls: type[BaseMergeTree] = MergeTree,
    token_registry: TokenRegistry = TokenRegistry(),
):
    """Create a MergeTree instance from a @data tree.

    The @data may contain special dynaconf tokens, such as container-level and
    terminal-level tokens.

    container-level token example: `"listy": [1,2,3, "@merge_unique"]`
    terminal-level token example: `"leafy": "@int 123"`
    """
    mtree = mtree_cls()

    # handler functions
    create_token_fn = functools.partial(create_token, token_registry=token_registry)
    tokenize_fn = functools.partial(tokenize, create_token=create_token_fn)

    def get_operation(token_id: str) -> type[BaseOperation]:
        token_op_map = get_builtin_token_operation_map()
        try:
            return token_op_map[token_id]
        except KeyError:
            raise KeyError(f"The token_id doesnt exist: {token_id}")

    def mtree_add_fn(path, item):
        mtree.add(path, item)  # noqa

    def mtree_add_meta_token_fn(path, token):
        if token:
            mtree.add_meta_token(path, token)  # noqa

    def mtree_get_meta_token_fn(path, token_id: Optional[str] = None):
        return mtree.get_meta_token(path, token_id)  # noqa

    # state

    # default_container_merge_policy = True
    # default_container_merge_operation = (
    #     Merge if default_container_merge_policy else None

    # merge_token_list = mtree_get_token_fn(item_path, "merge")
    # container_level_merge_operation = merge_token_list[0] if merge_token_list else None
    # merge_operation = container_level_merge_operation or default_container_merge_operation

    default_terminal_operation = Replace

    # TODO: implement this properly
    def is_token_merge_operation(op):
        return True

    def traverse_container(
        container_path: TreePath,
        key: str | int,
        value: Any,
    ):
        # case: value is container
        if isinstance(value, dict | list):
            for k, v in items(value):
                traverse_container(container_path + key, k, v)
            return

        # case: value is terminal value
        token_operation = None
        if token := tokenize_fn(value):
            if token.meta is True:
                mtree_add_meta_token_fn(container_path, token)
                return
            token_operation, evaluated = evaluate(token, key)
            value = evaluated or value

        # priority merge resolution
        container_level_operation = first(mtree_get_meta_token_fn(container_path))
        merge_operation = (
            token_operation or container_level_operation or default_terminal_operation
        )
        mtree_add_fn(container_path, merge_operation(key, value))

    data = ensure_rooted(data)
    traverse_container(TreePath(), "root", data["root"])
    return mtree


def first(sequence):
    if sequence:
        return sequence[0]
    return None


def evaluate(
    token: DynaconfToken, key: str | int
) -> tuple[type[BaseOperation] | None, Any]:
    """Evaluate DynaconfToken.

    Returns a tuple of (merge_operation, value)
    """
    next_token: DynaconfToken | None = token
    value = None
    merge_operation = None
    while next_token:
        if isinstance(next_token.fn, type) and issubclass(next_token.fn, BaseOperation):
            if next_token.next:
                raise ValueError(
                    f"BaseOperation should be the left-most token: {next_token.fn!r}"
                )
            merge_operation = next_token.fn
            break
        value = next_token.fn(
            next_token.args, cumulative=value
        )  # TODO: add proper types to those callables
        next_token = next_token.next
    return merge_operation, value


def items(container):
    if isinstance(container, dict):
        return container.items()
    elif isinstance(container, list):
        return enumerate(container)
    else:
        raise RuntimeError(f"Must be a dict or list: {container}")
