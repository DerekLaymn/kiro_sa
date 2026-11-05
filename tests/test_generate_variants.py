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


# --- Day 5 1b: 'Variant k of N' line ---
def _prompts(tmp_path, n, ops=""):
    seeds = tmp_path / "seeds"
    seeds.mkdir(exist_ok=True)
    (seeds / "s.py").write_text("# area: gradual_any\n# hypothesis: x\nx: int = 1\n")
    inbox, out = tmp_path / f"inbox{n}", tmp_path / f"out{n}"
    argv = ["--python-version", "3.13", "--llm", f"file:{inbox}", "generate", "--from-seeds", str(seeds),
            "--out-dir", str(out), "--n", str(n)]
    if ops:
        argv += ["--ops", ops]
    assert main(argv) == 0
    return [p.read_text() for p in sorted(inbox.glob("*.prompt.md"))]


def test_variants_have_different_prompt_bodies(tmp_path):
    bodies = _prompts(tmp_path, 2, "feature_crossover")
    assert len(bodies) == 2 and len(set(bodies)) == 2
    assert sorted(l for b in bodies for l in b.splitlines() if l.startswith("Variant ")) == [
        "Variant 1 of 2: independent variants of this request are written separately; make this one differ from the others.",
        "Variant 2 of 2: independent variants of this request are written separately; make this one differ from the others.",
    ]


def test_variants_are_otherwise_identical(tmp_path):
    a, b = _prompts(tmp_path, 2)
    strip = lambda t: "\n".join(l for l in t.splitlines() if not l.startswith("Variant "))  # noqa: E731
    assert strip(a) == strip(b)


def test_single_variant_prompt_is_unchanged(tmp_path):
    (body,) = _prompts(tmp_path, 1)
    assert "Variant " not in body
    from typediff import prompts
    from typediff.generator import generate  # noqa: F401  (prompt text built from the same templates)

    user = prompts.GENERATOR_USER.format(area="gradual_any", brief="x", mutations="(none)", previous="# area: gradual_any\n# hypothesis: x\nx: int = 1\n")
    assert user in body
