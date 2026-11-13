"""Tiny ``.env`` loader (stdlib only). Never overrides a variable that is already set in the environment."""

from __future__ import annotations

import os
import re
from pathlib import Path

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def parse_env_text(text: str) -> dict[str, str]:
    """``KEY=value`` lines; ``#`` comments, ``export`` prefix and matching quotes are understood. Empty values are
    skipped, so a template line such as ``ANTHROPIC_API_KEY=`` does not count as setting the key."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _LINE.match(line)
        if not m or line.lstrip().startswith("#"):
            continue
        key, value = m.groups()
        if value[:1] in ("'", '"') and value.count(value[0]) >= 2:
            value = value[1:value.index(value[0], 1)]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        if value:
            out[key] = value
    return out


def load_dotenv(path: str | Path = ".env") -> list[str]:
    """Load ``path`` into ``os.environ`` without overriding existing variables; return the names that were set.
    A missing file is not an error."""
    p = Path(path)
    if not p.is_file():
        return []
    loaded = []
    for key, value in parse_env_text(p.read_text(encoding="utf-8")).items():
        if key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
