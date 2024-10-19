from dynaconf import Dynaconf

settings = Dynaconf(settings_files=["settings/*"])
print(settings.foo)
