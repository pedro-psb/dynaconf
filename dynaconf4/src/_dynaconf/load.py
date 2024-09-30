from __future__ import annotations

from _dynaconf.abstract import BaseLoadRegistry
from _dynaconf.datastructures import LoadRequest

EnvName = str


def load(
    load_request: LoadRequest, load_registry: BaseLoadRegistry
) -> dict[EnvName, dict]:
    default_env = "default"  # TODO: move this to a better place and pass it over
    # TODO: where default comes from?
    has_explicit_envs = load_request.has_explicit_envs or False
    loader = load_registry.get_loader(load_request.loader_id)
    parsed = loader.parse(
        loader.read(load_request.uri, direct_data=load_request.direct_data)
    )
    return split_envs(
        parsed, has_explicit_envs=has_explicit_envs, default_env=default_env
    )


def split_envs(
    parsed_data: dict,
    has_explicit_envs: bool,
    default_env: str,
):
    if has_explicit_envs is True:
        return {env: data for env, data in parsed_data.items()}
    return {default_env: parsed_data}
