import pytest


@pytest.fixture
def registries():
    from dynaconflib.registry import RegistrySet

    registry_set = RegistrySet()
    registry_set.setup_builtin()
    return registry_set
