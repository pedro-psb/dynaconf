from dynaconf import Dynaconf
from dynaconflib.utils import data_debug

settings = Dynaconf(data={"a": [{"name": "direct1"}, {"name": "direct2"}]})
print(settings)
