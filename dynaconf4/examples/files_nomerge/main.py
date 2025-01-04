from dynaconf import Dynaconf

settings = Dynaconf(setting_files="sample.json")
print(settings)
