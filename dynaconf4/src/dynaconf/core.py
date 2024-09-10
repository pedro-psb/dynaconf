from .data_structs import LoaderSpec, MergeTree, SchemaTree, DataDict
from .dynaconf_options import Options
from .environment import EnvManager
from .loading import LoadingManager
from .merging import MergingManager


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

    def load_plugins(self) -> None:
        """Load module plugins (e.g, loading.loaders, merging.strategies)."""

    def execute_loaders(self):
        # load data
        for spec in self.loading_manager.dequeue_load_spec():
            self.loading_manager.load_resource(spec.loader_id, spec.uri)

        # merge data (for all envs)
        for env_name, data_queue in self.loading_manager.loaded_data.items():
            base_data = self.env_manager.get(env_name)
            for raw_income_data in data_queue:
                income_data = MergeTree.from_raw_data(raw_income_data, self.schema_tree)
                lazy_values = self.merging_manager.merge_data(base_data, income_data)
                self.env_manager.update_lazy(env_name, lazy_values)

    def get_settings(self) -> DataDict:
        """Get the settings for the active env."""
        return self.env_manager.get()
