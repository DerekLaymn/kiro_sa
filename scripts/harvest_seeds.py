"""Harvest seed programs from upstream test suites (Phase 1 of FUZZING_PLAN.md).

    python scripts/harvest_seeds.py [--out seeds/harvested] [--sources conformance,ty,mypy]

Sources (shallow, sparse git clones into ~/.cache/typediff/upstream):
  conformance  python/typing  conformance/tests/*.py        spec-backed; errors marked with `# E`
  ty           astral-sh/ruff crates/ty_python_semantic/resources/mdtest/**/*.md  (```py blocks)
  mypy         python/mypy    test-data/unit/check-*.test    ([case ...] blocks)

Each output file gets a `# area:` header guessed from its name, so `typediff seeds` can bucket results.
Programs that cannot work standalone are skipped: multi-file tests, ty_extensions, non-stdlib imports,
mypy plugins/flags, syntax errors. Output is NOT committed (see .gitignore); re-run to refresh.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

CACHE = Path.home() / ".cache" / "typediff" / "upstream"
STD = set(sys.stdlib_module_names) | {"typing_extensions", "__future__"}
REPOS = {
    "conformance": ("https://github.com/python/typing.git", "conformance/tests"),
    "ty": ("https://github.com/astral-sh/ruff.git", "crates/ty_python_semantic/resources/mdtest"),
    "mypy": ("https://github.com/python/mypy.git", "test-data/unit"),
}
AREA_HINTS = [
    ("self", "self_classmethods"), ("paramspec", "paramspec_concatenate"), ("concatenate", "paramspec_concatenate"),
    ("typevartuple", "typevartuple_unpack"), ("variadic", "typevartuple_unpack"), ("unpack", "typevartuple_unpack"),
    ("protocol", "protocols"), ("typeddict", "typeddict"), ("typed_dict", "typeddict"), ("overload", "overloads"),
    ("typeis", "narrowing_user"), ("typeguard", "narrowing_user"), ("narrow", "narrowing_builtin"),
    ("match", "match_statement"), ("dataclass", "dataclasses"), ("enum", "enums_literals"),
    ("literal", "enums_literals"), ("descriptor", "descriptors_properties"), ("property", "descriptors_properties"),
    ("constructor", "constructors_metaclasses"), ("metaclass", "constructors_metaclasses"), ("callable", "callables"),
    ("recursive", "recursive_aliases"), ("alias", "recursive_aliases"), ("final", "final_classvar"),
    ("classvar", "final_classvar"), ("qualifier", "final_classvar"), ("abstract", "abstract_classes"),
    ("async", "async_generators"), ("generator", "async_generators"), ("override", "inheritance_mro"),
    ("inherit", "inheritance_mro"), ("mro", "inheritance_mro"), ("tuple", "tuples_unpacking"),
    ("namedtuple", "tuples_unpacking"), ("generic", "generics_variance"), ("variance", "generics_variance"),
    ("typevar", "generics_variance"), ("any", "gradual_any"),
]


def guess_area(name: str) -> str:
    low = name.lower()
    for key, area in AREA_HINTS:
        if key in low:
            return area
    return "gradual_any"


def clone(src: str) -> Path:
    url, sub = REPOS[src]
    dest = CACHE / src
    if not (dest / ".git").exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth=1", "--filter=blob:none", "--sparse", url, str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", sub], check=True)
    else:
        subprocess.run(["git", "-C", str(dest), "pull", "-q", "--depth=1"], check=False)
    return dest / sub


def usable(code: str, version: tuple[int, int]) -> bool:
    try:
        tree = ast.parse(code, feature_version=version)
    except SyntaxError:
        return False
    if not tree.body or "ty_extensions" in code or "reveal_type" not in code and "# E" not in code and "error" not in code:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] not in STD for a in n.names):
            return False
        if isinstance(n, ast.ImportFrom) and (n.level or (n.module and n.module.split(".")[0] not in STD)):
            return False
    return True


def harvest_conformance(root: Path):
    for f in sorted(root.glob("*.py")):
        if f.name.startswith("_"):
            continue
        yield f"conformance__{f.stem}", f.read_text(encoding="utf-8"), f"python/typing conformance/tests/{f.name}"


_MD_BLOCK = re.compile(r"(?P<head>[^\n]*)\n```(?:py|python)\n(?P<code>.*?)```", re.S)


def harvest_ty(root: Path):
    for md in sorted(root.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        if re.search(r"^`[\w/]+\.pyi?`:\s*$", text, re.M):
            continue  # multi-file test: blocks depend on each other
        for i, m in enumerate(_MD_BLOCK.finditer(text)):
            rel = md.relative_to(root).with_suffix("")
            yield f"ty__{str(rel).replace('/', '__')}__{i}", m.group("code"), f"ruff mdtest {rel}.md block {i}"


_CASE = re.compile(r"^\[case (?P<name>[^\]]+)\]\n(?P<body>.*?)(?=^\[case |\Z)", re.S | re.M)


def harvest_mypy(root: Path):
    for t in sorted(root.glob("check-*.test")):
        for m in _CASE.finditer(t.read_text(encoding="utf-8")):
            body = m.group("body")
            if re.search(r"^\[(file|builtins|typing|fixture|out\d|stale|rechecked)\b", body, re.M) or "# flags:" in body:
                continue  # needs fixtures, extra files or special flags
            code = re.split(r"^\[(out|builtins|typing)\]", body, flags=re.M)[0]
            code = re.sub(r"^\[[^\]]+\]\s*$", "", code, flags=re.M)
            yield f"mypy__{t.stem}__{m.group('name')}", code, f"python/mypy {t.name} [case {m.group('name')}]"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="seeds/harvested")
    ap.add_argument("--sources", default="conformance,ty,mypy")
    ap.add_argument("--python-version", default="3.13")
    ap.add_argument("--limit", type=int, default=0, help="max programs per source (0 = all)")
    args = ap.parse_args()
    version = tuple(int(x) for x in args.python_version.split("."))
    out = Path(args.out)
    funcs = {"conformance": harvest_conformance, "ty": harvest_ty, "mypy": harvest_mypy}
    for src in args.sources.split(","):
        root = clone(src)
        kept = seen = 0
        for name, code, origin in funcs[src](root):
            seen += 1
            if not usable(code, version):
                continue
            safe = re.sub(r"[^\w]+", "_", name)[:120]
            area = guess_area(name)
            dest = out / area / f"{safe}.py"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"# area: {area}\n# origin: {origin}\n{code}", encoding="utf-8")
            kept += 1
            if args.limit and kept >= args.limit:
                break
        print(f"{src}: kept {kept} of {seen} programs -> {out}")


if __name__ == "__main__":
    main()
