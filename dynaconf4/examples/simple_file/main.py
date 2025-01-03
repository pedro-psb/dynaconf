from dynaconf import Dynaconf

settings = Dynaconf(setting_files=["sample.json", "sample.toml"])
print(settings)
