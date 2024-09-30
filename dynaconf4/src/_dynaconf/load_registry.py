from typing import Callable
from _dynaconf.abstract import BaseLoadRegistry
from _dynaconf.datastructures import Loader
from _dynaconf.load import split_envs


class LoaderRegistry(BaseLoadRegistry):
    def __init__(self):

        self._loaders = {
            "direct": Loader(noop, noop, split_envs),
        }

    def get_loader(self, loader_id: str) -> Loader:
        loader = self._loaders.get(loader_id)
        if not loader:
            raise RuntimeError(f"No TokenCallback registered for token: {loader_id!r}")
        return loader


def noop(input, *args, **kwargs):
    return input
