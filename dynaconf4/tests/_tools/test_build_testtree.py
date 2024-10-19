from pathlib import Path

from .build_testtree import build_testtree

happy_sample = """\
[meta]
scenario_name = "Some scenario title"
dynaconf_version = "x.y.z"
python_version = "3.9"
os = "linux"

[[runner]]
name = "basic"
description = "description"
workdir = ""
run = "python main.py"
expected = '''
foo = bar    
'''

[data]

structure = '''
main.py
settings/__init__.py
settings/settings.toml
settings/settings.yaml
'''

environ = '''
DYNACONF_FOO=bar    
'''

[[data.files]]
path = 'main.py'
content = '''
main.py-check
'''

[[data.files]]
path = 'settings/settings.toml'
content = '''
settings/settings.toml-check
'''

[[data.files]]
path = 'settings/settings.yaml'
content = '''
settings/settings.yaml-check
'''
"""


def test_happy_sample(tmp_path):
    sample_file = tmp_path / "happy_sample.toml"
    sample_file.write_text(happy_sample)
    build_testtree(sample_file, target_dir=tmp_path)

    files = ("main.py", "settings/settings.toml", "settings/settings.yaml")
    for file_path in files:
        file = Path(tmp_path / file_path)
        assert file.exists()
        assert f"{str(file_path)}-check" == file.read_text()

    print()
    print(f"To check manually cd to:\n{tmp_path}")
