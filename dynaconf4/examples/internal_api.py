from _dynaconf import apply_merge_tree, create_merge_tree
from _dynaconf.utils import section_print


def example_1():
    base = {"key_a": 111, "key_b": 222, "key_c": 111}
    income = {
        "key_a": "@add @int 999",
        "key_b": 999,
    }
    mtree = create_merge_tree(income)
    result = apply_merge_tree(base, mtree)
    docs = """See test_merge.py for more in-depth reference."""

    section_print(base=base)
    section_print(income=income)
    section_print(result=result["root"])
    section_print(docs=docs)


if __name__ == "__main__":
    exit(example_1())
