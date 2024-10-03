import functools
from typing import Any

from _dynaconf.datastructures import (
    DynaconfToken,
    TreePath,
    ensure_rooted,
    MergeTree,
)
from _dynaconf.abstract import BaseOperation, BaseMergeTree
from _dynaconf.token_registry import Replace

from _dynaconf.tokenize import TokenRegistry, tokenize


def create_merge_tree(
    data: dict,
    mtree_cls: type[BaseMergeTree] = MergeTree,
    token_registry: TokenRegistry = TokenRegistry(),
    # merge_policy: BaseMergePolicy = MergePolicy(),
):
    """Create a MergeTree instance from a @data tree.

    The @data may contain special dynaconf tokens, such as container-level and
    terminal-level tokens.

    container-level token example: `"listy": [1,2,3, "@merge_unique"]`
    terminal-level token example: `"leafy": "@int 123"`

    Args:
        data: The data that will be used to create the merge tree from.
        mtree_cls: The MergeTree class implementation that will be used. This should
            be a subclass of BaseMergeTree.
        token_registry: The object containing the token_id:token_callback relationship.
    """
    mtree = mtree_cls()
    default_terminal_operation = Replace

    def traverse_container(
        container_path: TreePath,
        key: str | int,
        value: Any,
    ):
        # Recursive case: value is container
        if isinstance(value, dict | list):
            for k, v in items(value):
                traverse_container(container_path + key, k, v)
            return

        # Base case: value is terminal
        token_operation = None
        if token := tokenize(value, token_registry):
            if token.is_container_level is True or token.is_lazy:
                mtree.add_meta_token(container_path, token)
                return
            token_operation, evaluated = evaluate(token, key)
            value = evaluated or value

        # priority merge resolution
        container_level_operation = first(mtree.get_meta_token(container_path))
        merge_operation = (
            token_operation or container_level_operation or default_terminal_operation
        )
        mtree.add(container_path, merge_operation(key, value))

    data = ensure_rooted(data)
    traverse_container(TreePath(), "root", data["root"])
    return mtree


def first(sequence):
    """Returns the first element of a sequence or None."""
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
