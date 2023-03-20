from pathlib import Path

import dynaconf

PROJECT_ROOT = Path(__file__).parent.parent.resolve(strict=True).as_posix()

settings = dynaconf.DjangoDynaconf(
    __name__,
    root_path=PROJECT_ROOT,
    core_loaders=["TOML", "PY"],
    settings_files=["settings.toml"],
    secrets=".secrets.toml",
    lowercase_read=False,
)