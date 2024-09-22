import pluggy

from .data_structs import DataDict, LoadRequest, SchemaTree, Stack, DynaconfTree
from .dynaconf_options import Options
from .environment import EnvManager
from .loading import LoadingManager
from .merging import MergingManager
from .evaluation import EvaluationManager

from typing import Optional

from collections import defaultdict


DataDicStack = Stack[DataDict]


class DynaconfCore:
    def __init__(self, schema_tree: SchemaTree, options: Options):
        # core data
        self.options = options
        self.schema_tree = schema_tree
        shared_options = options.shared

        # modules
        self.loading_manager = LoadingManager(shared_options)
        self.merging_manager = MergingManager(shared_options)
        self.env_manager = EnvManager(shared_options)
        self.evaluation_manager = EvaluationManager(shared_options)
        self.plugin_manager = pluggy.PluginManager("dynaconf4")

        # state
        self._load_request_stack: Stack[LoadRequest] = Stack[LoadRequest]()
        self._loaded_data_stack: dict[str, Stack[DynaconfTree]] = defaultdict(
            default_factory=Stack[DynaconfTree]  # type: ignore
        )

    def setup_plugins(self) -> None:
        """Load module plugins (e.g, loading.loaders, merging.strategies)."""
        raise NotImplementedError()

    def add_loader_request(self, loader_request: LoadRequest):
        self._load_request_stack.push(loader_request)

    def run_loaders(self):
        """Load data from load_request_stack, parse to DynaconfTree and push do loaded_data_stack."""
        while not self._load_request_stack.is_empty():
            load_request = self._load_request_stack.pop()
            env_data_map = self.loading_manager.load_resource(load_request)
            for env, data in env_data_map.items():
                dynaconf_tree = self.evaluation_manager.parse_tree(
                    data, self.schema_tree
                )
                self._loaded_data_stack[env].push(dynaconf_tree)

    def merge_loaded_data(self, env: Optional[str] = None):
        """Merge data from the loaded_data_stack for all or selected envs.

        No lazy values should be evaluated in this step.
        """
        env_names_list = [env] if env else self.env_manager.env_names
        for env_name in env_names_list:
            base_data = self.env_manager.get(env_name)
            income_data_stack = self._loaded_data_stack[env_name]
            while not income_data_stack.is_empty():
                income_data = income_data_stack.pop()
                self.merging_manager.merge_data(base_data, income_data)

    def evaluate_lazy_values(self, env: Optional[str] = None):
        """Evaluate lazy values from current env."""
        env_names_list = [env] if env else self.env_manager.env_names
        for env_name in env_names_list:
            dynaconf_tree = self.env_manager.get(env_name)
            self.evaluation_manager.evalute_lazy_values(dynaconf_tree)

    def get_settings_data(self, env: Optional[str] = None) -> DataDict:
        """Get the settings data for the active env, or optionally for an explicit provided env."""
        return self.env_manager.get(env).root
