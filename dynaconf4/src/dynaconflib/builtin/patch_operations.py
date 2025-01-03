from dynaconflib.datastructures import BasePatchOperation
from dynaconflib.registry import PatchOpRegistry
from dynaconflib.exceptions import MergeError


def setup_patch_operations(registry: PatchOpRegistry):
    registry.add("add", Add())
    registry.add("append", Append())
    registry.add("replace", Replace())
    registry.add("remove", Remove())


class Add(BasePatchOperation):
    def on_dict(self, data: dict, key, value):
        if key not in data:
            data[key] = value

    def on_list(self, data: list, key, value):
        data.insert(key, value)


class Replace(BasePatchOperation):
    def on_dict(self, data: dict, key, value):
        data[key] = value

    def on_list(self, data: list, key, value):
        try:
            data[key] = value
        except IndexError:
            raise MergeError(f"Index out for range: can't replace at index={key} on {data=}.")


class Append(BasePatchOperation):
    def on_dict(self, data: dict, key, value):
        raise NotImplementedError()

    def on_list(self, data: list, key, value):
        data.append(value)


class Remove(BasePatchOperation):
    def on_dict(self, data: dict, key, value):
        del data[key]

    def on_list(self, data: list, key, value):
        del data[key]
