import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from harvest_seeds import parse_mdtest  # noqa: E402

PY = "```py\nreveal_type(1)\n```\n"


def tom(body):
    return f"```toml\n[environment]\n{body}\n```\n"


def reasons(md):
    return [r[3] for r in parse_mdtest(md)]


def test_old_version_skipped_even_before_toml():
    assert reasons(f"# A\n{PY}{tom('python-version = \"3.12\"')}") == ["python-version=3.12"]


def test_nested_override_back_to_313():
    md = f"# A\n{tom('python-version = \"3.12\"')}{PY}## B\n{tom('python-version = \"3.13\"')}{PY}"
    assert reasons(md) == ["python-version=3.12", None]


def test_no_toml_kept():
    assert reasons(f"# A\n{PY}") == [None]


def test_313_kept():
    assert reasons(f"# A\n{tom('python-version = \"3.13\"')}{PY}") == [None]


def test_platform_and_extra_paths_skipped():
    assert reasons(f"# A\n{tom('python-platform = \"linux\"')}{PY}# B\n{tom('extra-paths = [\"/x\"]')}{PY}") == [
        "python-platform",
        "extra-paths",
    ]
