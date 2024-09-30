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
    stack = Stack[Item]()
    mtree = mtree_cls()

    # handler functions
    create_token_fn = functools.partial(create_token, token_registry=token_registry)
    dynaconf_parse_fn = functools.partial(tokenize, create_token=create_token_fn)

    def get_operation(token_id: str) -> type[BaseOperation]:
        token_op_map = get_builtin_token_operation_map()
        try:
            return token_op_map[token_id]
        except KeyError:
            raise KeyError(f"The token_id doesnt exist: {token_id}")

    def mtree_add_fn(path, item):
        mtree.add(path, item)  # noqa

    def mtree_add_token_fn(path, token):
        if token:
            mtree.add_meta_token(path, token)  # noqa

    def mtree_get_token_fn(path, token_id: Optional[str] = None):
        return mtree.get_meta_token(path, token_id)  # noqa

    def push_item_fn(item: Item):
        stack.push(item)

    def push_container_fn(container_item: Item):
        for item in items(container_item.value):
            if item.contains_token():
                mtree_add_token_fn(item.path, dynaconf_parse_fn(item))
                continue
            stack.push(item)  # noqa

    # state
    container_type = dict
    container_path = TreePath(("root",))  # absolute path

    # initial setup
    root_item = Item(container_path=container_path, key="", value=ensure_rooted(data))
    stack.push(root_item)

    # traverse
    # TODO: I've reinvted recursion calls here.
    #       Its probably not more efficient than normal recursion and way confusing.
    #       Make a more generalized Travereser object or something and use normal recursion
    count = 0
    COUNT_LIMIT = 1000
    while not stack.is_empty():
        if count > COUNT_LIMIT:
            raise RuntimeError("Recursion detected.")

        count += 1
        item = stack.pop()
        if isinstance(item, ContextChange):
            container_type = item.new_container_type
            container_path = item.new_container_path
            continue

        # process item
        # TODO: make this explicit if blocks
        # TODO: pass merge tree instead of enclosing its methods
        container_handler = dict_handler if container_type is dict else list_handler
        container_handler(
            item,
            container_path,
            push_container_fn,
            push_item_fn,
            mtree_add_fn,
            mtree_add_token_fn,
            mtree_get_token_fn,
            dynaconf_parse_fn,
        )
    return mtree


def evaluate(token: DynaconfToken, key: str | int):
    next_token: DynaconfToken | None = token
    value = None
    while next_token:
        if isinstance(next_token.fn, type) and issubclass(next_token.fn, BaseOperation):
            return next_token.fn(key, value)
        value = next_token.fn(
            next_token.args, cumulative=value
        )  # TODO: add proper types to those callables
        next_token = next_token.next
    return value


def dict_handler(
    item: Item,
    container_path: TreePath,
    push_container_fn: Callable,
    push_item_fn: Callable,
    mtree_add_fn: Callable,
    mtree_add_token_fn: Callable,
    mtree_get_token_fn: Callable,
    dynaconf_parse_fn: Callable,
):
    # default_container_merge_policy = True
    # default_container_merge_operation = (
    #     Merge if default_container_merge_policy else None
    # )

    # case: value is container
    if isinstance(item.value, dict | list):
        for k, v in items(item.value):
            child_item = Item(item.container_path, k, v)
            if is_token(child_item.value):
                if token := dynaconf_parse_fn(child_item.value):
                    if token.meta is True:
                        mtree_add_token_fn(child_item.container_path, token)
                    else:
                        item_operation = evaluate(token, child_item.key)
                        mtree_add_fn(child_item.container_path, item_operation)
            else:
                push_item_fn(child_item)  # noqa

    # case: value is terminal value
    else:
        default_terminal_operation = Replace
        # merge_token_list = mtree_get_token_fn(item_path, "merge")
        # container_level_merge_operation = merge_token_list[0] if merge_token_list else None
        # merge_operation = container_level_merge_operation or default_container_merge_operation

        merge_operation = default_terminal_operation
        mtree_add_fn(item.container_path, merge_operation(item.key, item.value))


def list_handler(
    item: Item,
    container_path: TreePath,
    push_container_fn: Callable,
    mtree_add_fn: Callable,
    push_item_fn: Callable,
    mtree_add_token_fn: Callable,
    mtree_get_token_fn: Callable,
    dynaconf_parse_fn: Callable,
): ...


def items(container):
    if isinstance(container, dict):
        return container.items()
    elif isinstance(container, list):
        return enumerate(container)
    else:
        raise RuntimeError(f"Must be a dict or list: {container}")
