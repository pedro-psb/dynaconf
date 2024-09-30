from _dynaconf.datastructures import LoadRequest
from _dynaconf.abstract import BaseLoadRegistry

EnvName = str


def load(
    load_request: LoadRequest, load_registry: BaseLoadRegistry
) -> dict[EnvName, dict]:
    loader = load_registry.get_loader(load_request.loader_id)
    data = {}
    result = {"env": data}
    return result


def split_envs(
    self,
    parsed_data: dict,
    has_explicit_envs: bool,
    default_env: str,
):
    if has_explicit_envs is True:
        return {env: data for env, data in parsed_data.items()}
    return {default_env: parsed_data}
