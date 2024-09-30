from _dynaconf import apply_merge_tree, create_merge_tree
from _dynaconf.utils import print_kwargs


def example_1():
    base = {"key_a": 111, "key_b": 222, "key_c": 111}
    income = {
        "key_a": "@add @int 999",
        "key_b": 999,
    }
    mtree = create_merge_tree(income)
    result = apply_merge_tree(base, mtree)
    docs = """\
    * 'income.key_a' is a no-op, because '@add' token's callback only applies in 'income_only' case.
    * 'income.key_b' replaces 'base.key_b', because replace is the default behavior for Terminal values 'conflict' case.

    See test_merge.py for more in-depth reference.
    """

    print_kwargs(base=base, income=income, result=result["root"], mtree=mtree, docs=docs)


if __name__ == "__main__":
    exit(example_1())
