from dynaconf import Dynaconf
from dynaconflib.utils import data_debug
from dynaconflib.public import inspect_api

settings = Dynaconf(a=[{"name": "direct1"}, {"name": "direct2"}])

result = inspect_api(settings)
result.print()
# data_debug(settings)
# print(settings)
