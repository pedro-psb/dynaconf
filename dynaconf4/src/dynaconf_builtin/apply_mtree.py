from __future__ import annotations

from copy import deepcopy

from dynaconf_builtin.datastructures import BaseMergeTree, TreePath, ensure_path, ensure_rooted
from dynaconf_builtin.registry import Merge, JumpMerge


def apply_merge_tree(
    base: dict, merge_tree: BaseMergeTree, mutate_base: bool = False
) -> dict:
    """Apply @merge_tree operation into @base.

    The merge_tree operations define how the base data will change. Some specialized function
    should be responsible for generating a correct MergeTree that reflects dynaconf mini-language
    and respects builtin-defined and user-defined merge behavior.

    Args:
        base: The nested dict-data structure that the merge_tree should be applied on.
        merge_tree: A MergeTree instance which contain operation to be applied on specific nodes.
        mutate_base: If set to False, a deep copy of the data will be created.

    Returns the base or base deep copy after merge_tree ops were applied.
    """
    _data = base if mutate_base is True else deepcopy(base)
    _data = ensure_rooted(_data)

    def step_in(container: dict | list, path: TreePath):
        container_ops = merge_tree.get(path) or []
        # apply all operation on current container items
        for op in container_ops:
            new_path = path + ensure_path(op.key)
            if isinstance(op, JumpMerge):  # optimization
                container = jump_to(container, op.key)
                step_in(container, new_path)
            if isinstance(op, Merge):
                step_in(container[op.key], new_path)
                continue
            op.run(container)

    step_in(_data["root"], TreePath(["root"]))
    return _data


def jump_to(container, rel_path):
    # Split the path by dots to get the individual keys or indices
    keys = rel_path.split(".")

    # Traverse the tree using each key or index in the path
    current_obj = container
    for key in keys:
        if isinstance(current_obj, dict):
            # For dicts, use the key directly
            current_obj = current_obj[key]
        elif isinstance(current_obj, list):
            # For lists, convert the key to an integer index
            current_obj = current_obj[int(key)]
        else:
            raise ValueError(
                f"Unexpected type encountered: {
                    type(current_obj)} at key: {key}"
            )

    return current_obj
