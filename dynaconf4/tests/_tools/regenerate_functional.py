from tests._tools.build_testtree import build_testtree
from pathlib import Path
import shutil


def main():
    functional_fixture_dir = Path("tests/functional/fixtures")

    # clean fixtures
    testtree_dirs = [f for f in functional_fixture_dir.iterdir() if f.is_dir()]
    for testree_dir in testtree_dirs:
        shutil.rmtree(testree_dir)

    # re-generate fixtures
    testtree_files = [f for f in functional_fixture_dir.iterdir() if f.suffix == ".toml"]
    for testtree_file in testtree_files:
        fixture_dir = Path(functional_fixture_dir / testtree_file.stem)
        fixture_dir.mkdir()
        build_testtree(testtree_file, fixture_dir)

if __name__ == "__main__":
    exit(main())
