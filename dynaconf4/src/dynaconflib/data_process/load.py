from __future__ import annotations

from _dynaconf.abstract import BaseLoadRegistry
from _dynaconf.datastructures import LoadRequest, LoadContext

EnvName = str


def load(
    load_request: LoadRequest,
    load_registry: BaseLoadRegistry,
    load_context: LoadContext,
) -> dict[EnvName, dict]:
    default_env = "default"  # TODO: move this to a better place and pass it over
    # TODO: where default comes from?
    namespace_in_root = load_request.namespace_in_root or False
    loader = load_registry.get_loader(load_request.loader_id)
    parsed = loader(load_request, load_context)
    return split_envs(
        parsed, namespace_in_root=namespace_in_root, default_env=default_env
    )


def split_envs(
    parsed_data: dict,
    namespace_in_root: bool,
    default_env: str,
):
    if namespace_in_root is True:
        return {env: data for env, data in parsed_data.items()}
    return {default_env: parsed_data}
