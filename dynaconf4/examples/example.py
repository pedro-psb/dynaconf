from dynaconf.typed import DataDict, Options


class Database(DataDict):
    user: str
    port: int
    password: str = "secret123"


class Settings(DataDict):
    foo: int
    bar: str = "abc"
    db: Database


def init_explicitly():
    settings = Settings()
    dynaconf = settings.get_dynaconf()


def init_shorthand():
    options = Options()
    dynaconf, settings = Settings.init_dynaconf(options=options)
    dynaconf.load.add()
    dynaconf.load
