from dynaconflib.datastructures import PriorityField, PriorityQueue
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    priority_field: PriorityField


def test_priority_field():
    priority_field = PriorityField()
    assert isinstance(priority_field.priority, int)
    assert isinstance(priority_field.group, int)


def test_priority_q():
    GREEN = PriorityQueue.PRIORITY_GROUP_SET.GREEN
    ORANGE = PriorityQueue.PRIORITY_GROUP_SET.ORANGE
    RED = PriorityQueue.PRIORITY_GROUP_SET.RED

    priority_q = PriorityQueue[Item]()
    items = [
        Item("last", PriorityField(-1, GREEN)),
        Item("same-prio-0", PriorityField()),
        Item("in-group-precedence-0", PriorityField(10, ORANGE)),
        Item("same-prio-1", PriorityField()),
        Item("in-group-precedence-1", PriorityField(9, ORANGE)),
        Item("same-prio-2", PriorityField()),
        Item("red-group-precedence", PriorityField(0, RED)),
        Item("in-group-precedence-2", PriorityField(8, ORANGE)),
    ]
    expected = [
        "red-group-precedence",
        # groups first
        "in-group-precedence-0",
        "in-group-precedence-1",
        "in-group-precedence-2",
        # insertion order should be preserved
        "same-prio-0",
        "same-prio-1",
        "same-prio-2",
        # green with low prio
        "last",
    ]
    for item in items:
        priority_q.push(item)

    pop_sequence = [priority_q.pop().name for _ in range(len(priority_q))]
    assert pop_sequence == expected
