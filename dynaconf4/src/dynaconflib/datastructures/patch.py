from .data import DataDict, DataList


class BasePatch:
    def apply(self, data: DataDict | DataList): ...

    @classmethod
    def create(cls):
        patch = cls()
        return patch
