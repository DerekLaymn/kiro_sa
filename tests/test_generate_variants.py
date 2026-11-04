"""`typediff generate --n N` must produce N distinct prompts (seed=k) and stable output filenames."""
import json

from typediff.cli import main


def _run(tmp_path, n=3):
    seeds = tmp_path / "seeds"
    seeds.mkdir(exist_ok=True)
    (seeds / "s.py").write_text("# area: gradual_any\n# hypothesis: x\nx: int = 1\n")
    inbox, out = tmp_path / "inbox", tmp_path / "out"
    rc = main(["--python-version", "3.13", "--llm", f"file:{inbox}", "generate",
               "--from-seeds", str(seeds), "--out-dir", str(out), "--n", str(n)])
    assert rc == 0
    return inbox, out


def test_n3_gives_three_distinct_prompts(tmp_path):
    inbox, _ = _run(tmp_path, 3)
    assert len(list(inbox.glob("*.prompt.md"))) == 3


def test_output_filenames_stable_across_runs(tmp_path):
    inbox, out = _run(tmp_path, 3)
    for p in inbox.glob("*.prompt.md"):
        key = p.name.split(".")[0]
        (inbox / f"{key}.answer.json").write_text(json.dumps({"source": "y: int = 1\n", "hypothesis": "h"}))
    _run(tmp_path, 3)
    first = sorted(p.name for p in out.rglob("*.py"))
    assert len(first) == 3
    _run(tmp_path, 3)
    assert sorted(p.name for p in out.rglob("*.py")) == first
