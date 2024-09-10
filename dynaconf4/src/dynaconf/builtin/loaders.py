class TomlLoader(ResourceLoader):
    LOADER_ID = "builtin.yaml"
    ...


class EnvironLoader(ResourceLoader):
    LOADER_ID = "builtin.environ"
    ...


class SqliteLoader(ResourceLoader):
    LOADER_ID = "builtin.sqlite"
    ...
