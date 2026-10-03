"""Minimal, dependency-free LLM clients + robust JSON extraction.

Configure with ``TYPEDIFF_LLM``:
    anthropic:<model>                       (ANTHROPIC_API_KEY)
    openai:<model>                          (OPENAI_API_KEY, optional OPENAI_BASE_URL)
    openai:<model>@http://localhost:8000/v1 (any OpenAI-compatible server: vLLM, Ollama, LiteLLM ...)
    file:<dir>                              (manual: prompts written to <dir>, answers read back)
    null                                    (default: no LLM -> undecided cases go to the human queue)

Responses are cached on disk keyed by a hash of (model, system, user, temperature, seed) so re-running a
campaign never pays twice for the same question.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Protocol

CACHE_DIR = Path(os.environ.get("TYPEDIFF_CACHE", Path.home() / ".cache" / "typediff" / "llm"))


class LLM(Protocol):
    name: str

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str: ...


class NullLLM:
    name = "null"

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str:
        return json.dumps({"_null": True})


class FileLLM:
    """Human-in-the-loop / external-agent bridge: write prompt, return answer file if present."""

    def __init__(self, directory: str):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.name = f"file:{directory}"

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str:
        key = hashlib.sha256((system + user + str(seed)).encode()).hexdigest()[:16]
        (self.dir / f"{key}.prompt.md").write_text(f"# SYSTEM\n\n{system}\n\n# USER\n\n{user}\n", encoding="utf-8")
        answer = self.dir / f"{key}.answer.json"
        return answer.read_text(encoding="utf-8") if answer.exists() else json.dumps({"_null": True, "_prompt": key})


class _HTTP:
    name = "http"

    _last_call = 0.0

    def _post(self, url: str, headers: dict[str, str], body: dict[str, Any], retries: int = 6) -> dict[str, Any]:
        # TYPEDIFF_LLM_MIN_INTERVAL: seconds between requests (OpenRouter free tier = 20/min -> use 3.5)
        gap = float(os.environ.get("TYPEDIFF_LLM_MIN_INTERVAL", "0"))
        wait = _HTTP._last_call + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _HTTP._last_call = time.monotonic()
        data = json.dumps(body).encode()
        for attempt in range(retries):
            req = urllib.request.Request(url, data=data, headers={"content-type": "application/json", **headers})
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:  # noqa: S310 - user-configured endpoint
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 529) and attempt < retries - 1:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        delay = float(retry_after) if retry_after else 2 ** attempt * 3
                    except ValueError:
                        delay = 2 ** attempt * 3
                    time.sleep(min(delay, 120))
                    continue
                raise RuntimeError(f"LLM HTTP {exc.code}: {exc.read().decode(errors='replace')[:500]}") from exc
            except urllib.error.URLError:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt * 3)
                    continue
                raise
        raise RuntimeError("unreachable")


class AnthropicLLM(_HTTP):
    def __init__(self, model: str):
        self.model = model
        self.name = f"anthropic:{model}"
        self.key = os.environ["ANTHROPIC_API_KEY"]

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str:
        out = self._post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": self.key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": max_tokens, "temperature": temperature, "system": system,
             "messages": [{"role": "user", "content": user}]},
        )
        return "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text")


class OpenAICompatLLM(_HTTP):
    def __init__(self, model: str, base_url: str | None = None):
        self.model = model
        self.base = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.key = os.environ.get("OPENAI_API_KEY", "none")
        self.name = f"openai:{model}@{self.base}"

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str:
        out = self._post(
            f"{self.base}/chat/completions", {"authorization": f"Bearer {self.key}"},
            {"model": self.model, "temperature": temperature, "max_tokens": max_tokens, "seed": seed,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        return out["choices"][0]["message"]["content"] or ""


class CachedLLM:
    def __init__(self, inner: LLM, cache_dir: Path = CACHE_DIR):
        self.inner = inner
        self.name = inner.name
        self.dir = cache_dir
        self.calls = 0

    def complete(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 4096, seed: int = 0) -> str:
        if isinstance(self.inner, (NullLLM, FileLLM)):
            return self.inner.complete(system, user, temperature=temperature, max_tokens=max_tokens, seed=seed)
        key = hashlib.sha256(json.dumps([self.name, system, user, temperature, seed]).encode()).hexdigest()
        path = self.dir / key[:2] / f"{key}.txt"
        if path.exists():
            return path.read_text(encoding="utf-8")
        self.calls += 1
        text = self.inner.complete(system, user, temperature=temperature, max_tokens=max_tokens, seed=seed)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text


def from_env(spec: str | None = None) -> CachedLLM:
    spec = spec or os.environ.get("TYPEDIFF_LLM", "null")
    kind, _, rest = spec.partition(":")
    if kind == "anthropic":
        inner: LLM = AnthropicLLM(rest)
    elif kind == "openai":
        model, _, base = rest.partition("@")
        inner = OpenAICompatLLM(model, base or None)
    elif kind == "file":
        inner = FileLLM(rest or "llm_inbox")
    else:
        inner = NullLLM()
    return CachedLLM(inner)


# --------------------------------------------------------------------------- JSON handling


def extract_json(text: str) -> Any:
    """Pull the first top-level JSON object/array out of a model response (handles ``` fences, prose)."""
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if fence:
        t = fence.group(1).strip()
    for opener, closer in (("{", "}"), ("[", "]")):
        start = t.find(opener)
        if start < 0:
            continue
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                esc = (ch == "\\") and not esc
                if ch == '"' and not esc:
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(t[start:i + 1])
    raise ValueError("no JSON object found in model output")


def complete_json(llm: LLM, system: str, user: str, validate: Callable[[Any], list[str]], *, temperature: float = 0.0,
                  seed: int = 0, retries: int = 2, max_tokens: int = 4096) -> Any:
    """Ask, parse, validate; on schema errors re-ask with the error list appended."""
    prompt = user
    last_err: list[str] = []
    for _ in range(retries + 1):
        raw = llm.complete(system, prompt, temperature=temperature, seed=seed, max_tokens=max_tokens)
        try:
            obj = extract_json(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            last_err = [f"invalid JSON: {exc}"]
        else:
            if isinstance(obj, dict) and obj.get("_null"):
                return obj
            last_err = validate(obj)
            if not last_err:
                return obj
        prompt = (user + "\n\n## YOUR PREVIOUS ANSWER WAS REJECTED\n" + "\n".join(f"- {e}" for e in last_err)
                  + "\nReturn ONLY the corrected JSON object.")
    return {"_invalid": True, "_errors": last_err}
