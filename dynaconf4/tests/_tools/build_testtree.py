from pathlib import Path

import tomllib

def build_testtree(testtree_file: Path, target_dir: Path):
    """Create a test fs structure from @testtree_file on @target dir.

    The goal is to facilitate creating fixtures for testing common user cases.
    The overall structure is:

    ```pseudo-format
    {
        meta: {
            dynaconf_version: x.y.z
            python_version: x.y.z
            os: linux | windows
        }
        runner: [
            {
                name: ...
                description: ...
                workdir: ...
                run: python main.py
                expected: multinline expected stdout string output
            },
            ...
        ]
        data: {
            structure: multiline paths to be created (by mkdir or touch)
            environ: multiline with the environ key=value
            files: [
                {
                    path: the file relative path
                    content: multiline file content
                }
            ]
        }
    }
    ```

    See `test_doctree_writer` for samples.

    Params:
        doctree_file: The file with a supported extenstion format. E.g: `.toml` `.yml` and `.doctree`
        target: The directory where the project should be writter to.
    """

    # Open and parse doctree file
    if testtree_file.suffix in (".toml",):
        parsed= tomllib.loads(testtree_file.read_text())
    else:
        raise NotImplementedError(f"File type not supported: {testtree_file.name}")

    # guard: should have data.structure
    try:
        structure = parsed["data"]["structure"]
    except KeyError:
        raise ValueError("The testree file should have a data.structure definition.")

    # guard: data.files should have should have record in data.structure
    try:
        paths_in_files = [file["path"] for file in parsed["data"]["files"]]
        for path in paths_in_files:
            if path not in structure.split("\n"):
                raise ValueError("Files defined in data.structure should have a record in data.files")
    except KeyError:
        raise ValueError("Files defined in data.structure should have a record in data.files")
        
    # create structure and populate files
    for path in [s.strip("\n") for s in structure.split("\n")]:
        basedir, _, filename = path.strip("/").rpartition("/")
        basedir = target_dir / basedir
        if basedir:
            basedir.mkdir(parents=True, exist_ok=True)
        file_full_path = target_dir / basedir / filename
        file_full_path.touch()

        files = [f for f in parsed["data"]["files"] if f]
        if content := [f["content"].strip("\n") for f in files if f["path"] == path.strip("\n")]:
            Path(file_full_path).write_text(content[0])

