"""Local document corpus (typing spec, mypy docs, ty docs/rules, pyright's mypy comparison)
with BM25 retrieval and verbatim-quote verification.

Why: the adjudicator may only DISMISS with a citation, and citations are machine-checked here.
An LLM quoting the spec "from memory" is the #1 way a pipeline like this silently throws away
real bugs (or files bogus ones), so unverifiable quotes are discarded and the verdict downgraded.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DIR = Path(os.environ.get("TYPEDIFF_DOCS", Path.home() / ".cache" / "typediff" / "docs"))

SPEC_PAGES = [
    "concepts", "annotations", "special-types", "generics", "qualifiers", "class-compat", "aliases", "literal",
    "protocol", "callables", "constructors", "overload", "exceptions", "dataclasses", "enums", "namedtuples",
    "tuples", "typeddict", "narrowing", "directives", "type-forms", "type-system", "glossary",
]
MYPY_PAGES = [
    "type_inference_and_annotations", "type_narrowing", "error_code_list", "error_code_list2", "command_line",
    "common_issues", "kinds_of_types", "generics", "protocols", "literal_types", "final_attrs", "more_types",
    "dynamic_typing", "class_basics", "typed_dict", "duck_type_compatibility",
]
TY_PAGES = [
    "coming-from-mypy-or-pyright.md", "features/type-system.md", "reference/typing-faq.md",
    "reference/configuration.md", "suppression.md", "python-version.md",
]
SOURCES = (
    [(f"spec/{p}", f"https://raw.githubusercontent.com/python/typing/main/docs/spec/{p}.rst",
      f"https://typing.python.org/en/latest/spec/{p}.html") for p in SPEC_PAGES]
    + [(f"mypy/{p}", f"https://raw.githubusercontent.com/python/mypy/master/docs/source/{p}.rst",
        f"https://mypy.readthedocs.io/en/stable/{p}.html") for p in MYPY_PAGES]
    + [(f"ty/{p.removesuffix('.md')}", f"https://raw.githubusercontent.com/astral-sh/ty/main/docs/{p}",
        f"https://docs.astral.sh/ty/{p.removesuffix('.md')}/") for p in TY_PAGES]
    + [("pyright/mypy-comparison", "https://raw.githubusercontent.com/microsoft/pyright/main/docs/mypy-comparison.md",
        "https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md")]
)


@dataclass
class Chunk:
    id: str
    doc: str
    url: str
    text: str


def _norm(text: str) -> str:
    t = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"[`*]+", "", t)  # markup
    return re.sub(r"\s+", " ", t).strip().lower()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z_][a-z0-9_\-]{1,}", text.lower())


class Corpus:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or DEFAULT_DIR)
        self.chunks: list[Chunk] = []
        self._tf: list[Counter] = []
        self._df: Counter = Counter()
        self._extra_norm: list[str] = []  # KB texts etc. that also count as verifiable sources
        if self.root.exists():
            self._load()

    # ------------------------------------------------------------------ loading
    def _load(self) -> None:
        for path in sorted(self.root.rglob("*.txt")):
            raw = path.read_text(encoding="utf-8", errors="replace")
            url = ""
            if raw.startswith("SOURCE: "):
                url, _, raw = raw.partition("\n")
                url = url[len("SOURCE: "):].strip()
            doc = str(path.relative_to(self.root).with_suffix(""))
            for i, text in enumerate(_split(raw)):
                self.chunks.append(Chunk(f"DOC:{doc}#{i}", doc, url, text))
        for c in self.chunks:
            tf = Counter(_tokens(c.text))
            self._tf.append(tf)
            self._df.update(tf.keys())

    def add_verifiable_text(self, text: str) -> None:
        self._extra_norm.append(_norm(text))

    @property
    def empty(self) -> bool:
        return not self.chunks

    # ------------------------------------------------------------------ retrieval
    def search(self, query: str, k: int = 6, prefer: tuple[str, ...] = ()) -> list[Chunk]:
        if not self.chunks:
            return []
        q = _tokens(query)
        n = len(self.chunks)
        avg = sum(sum(tf.values()) for tf in self._tf) / n
        scores = []
        for i, tf in enumerate(self._tf):
            dl = sum(tf.values()) or 1
            s = 0.0
            for term in q:
                if term not in tf:
                    continue
                idf = math.log(1 + (n - self._df[term] + 0.5) / (self._df[term] + 0.5))
                s += idf * tf[term] * 2.2 / (tf[term] + 1.2 * (0.25 + 0.75 * dl / avg))
            if prefer and self.chunks[i].doc.startswith(prefer):
                s *= 1.25
            scores.append((s, i))
        scores.sort(reverse=True)
        return [self.chunks[i] for s, i in scores[:k] if s > 0]

    def get(self, chunk_id: str) -> Chunk | None:
        return next((c for c in self.chunks if c.id == chunk_id), None)

    # ------------------------------------------------------------------ verification
    def verify_quote(self, quote: str, min_len: int = 25) -> bool:
        """True iff ``quote`` occurs verbatim (modulo whitespace/markup/quote style) in a source."""
        q = _norm(quote).strip(" .\"'")
        if len(q) < min_len:
            return False
        if any(q in _norm(c.text) for c in self.chunks):
            return True
        return any(q in t for t in self._extra_norm)


def _split(raw: str, target: int = 1400) -> list[str]:
    paras = re.split(r"\n\s*\n", raw)
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) > target and cur:
            chunks.append(cur.strip())
            cur = ""
        cur += p + "\n\n"
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


# --------------------------------------------------------------------------- fetching


def fetch_docs(root: Path | None = None, ty_cmd: list[str] | None = None, refresh_rule_map: bool = False) -> list[str]:
    root = Path(root or DEFAULT_DIR)
    root.mkdir(parents=True, exist_ok=True)
    log = []
    for name, raw_url, human_url in SOURCES:
        dest = root / f"{name}.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(raw_url, timeout=30) as resp:  # noqa: S310 - fixed https URLs
                text = resp.read().decode("utf-8", errors="replace")
            dest.write_text(f"SOURCE: {human_url}\n{text}", encoding="utf-8")
            log.append(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            log.append(f"FAIL {name}: {exc}")
    if ty_cmd:
        try:
            out = subprocess.run([*ty_cmd, "explain", "rule", "--output-format", "json"], capture_output=True, text=True,
                                 timeout=60).stdout
            for rule in json.loads(out):
                dest = root / "ty-rules" / f"{rule['name']}.txt"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(
                    f"SOURCE: https://docs.astral.sh/ty/reference/rules/#{rule['name']}\n"
                    f"ty rule `{rule['name']}` (default level: {rule.get('default_level')})\n{rule.get('summary', '')}\n\n"
                    f"{rule.get('documentation', '')}",
                    encoding="utf-8",
                )
            log.append("ok   ty-rules (from local ty binary)")
        except Exception as exc:  # noqa: BLE001
            log.append(f"FAIL ty-rules: {exc}")
    if refresh_rule_map:
        log.append(refresh_rule_map_file(root / "ty" / "coming-from-mypy-or-pyright.txt"))
    return log


def refresh_rule_map_file(md_path: Path) -> str:
    from .concerns import DATA

    if not md_path.exists():
        return "FAIL rule-map: migration guide not downloaded"
    rows = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or "ty or Ruff rule" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        names = lambda c: re.findall(r"\[`([^`]+)`\]", c)  # noqa: E731
        note = re.sub(r"\[`[^`]+`\]\[[^\]]+\]", "", cells[0]).strip().strip(",").strip()
        rows.append({
            "ty": names(cells[0]), "mypy": [c for c in names(cells[1]) if not c.startswith("--")],
            "mypy_flags": [c for c in names(cells[1]) if c.startswith("--")], "pyright": names(cells[2]),
            "note": re.sub(r"\]\[[^\]]+\]", "]", note),
            "ty_issues": [f"https://github.com/astral-sh/ty/issues/{i}" for i in re.findall(r"\[#(\d+)\]", note)],
            "partial": bool(re.search(r"for other|other cases|partial", note, re.I)),
        })
    DATA.write_text(json.dumps({"_source": str(md_path), "rows": rows}, indent=1))
    return f"ok   rule-map ({len(rows)} rows) -> {DATA}"
