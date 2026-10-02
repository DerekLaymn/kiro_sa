"""Standalone CPython runner (no typediff imports - it runs under the *target* interpreter).

    python runtime_harness.py <program.py> <out.json> [timeout_seconds]

Executes the program as ``__main__`` and writes JSON with:
  * status / exception type / message / traceback frames inside the program
  * executed line numbers (coverage oracle for reachability claims)
  * one probe per runtime ``reveal_type(x)`` call: the *shape* of the value
    (type + MRO, literal value, enum member, element shapes) so the pipeline can check
    whether the value actually inhabits each checker's revealed type.

SECURITY: generated programs are untrusted. Run this inside a sandbox/container with no
network; the rlimits below are a seatbelt, not isolation.
"""

from __future__ import annotations

import builtins
import json
import os
import signal
import sys
import traceback
import types

MAX_ITEMS = 6
MAX_PROBES = 500


def _qual(cls: type) -> str:
    mod = getattr(cls, "__module__", "?")
    return f"{mod}.{getattr(cls, '__qualname__', getattr(cls, '__name__', '?'))}"


def describe(value, depth: int = 2) -> dict:
    cls = type(value)
    shape: dict = {"type": _qual(cls), "mro": [_qual(c) for c in getattr(cls, "__mro__", (cls,))]}
    try:
        shape["repr"] = repr(value)[:160]
    except Exception:  # noqa: BLE001 - user __repr__ may raise
        shape["repr"] = "<repr failed>"
    shape["callable"] = callable(value)
    if isinstance(value, type):
        shape["is_class"] = True
        shape["class_mro"] = [_qual(c) for c in value.__mro__]
    try:
        import enum

        if isinstance(value, enum.Enum):
            shape["enum"] = f"{cls.__qualname__}.{value.name}"
    except Exception:  # noqa: BLE001
        pass
    if isinstance(value, (bool, int, str, bytes, float, complex)) or value is None:
        shape["literal"] = repr(value)
    if depth > 0:
        try:
            if isinstance(value, (list, tuple, set, frozenset)):
                items = list(value)[:MAX_ITEMS] if not isinstance(value, (set, frozenset)) else list(value)[:MAX_ITEMS]
                shape["len"] = len(value)
                shape["items"] = [describe(v, depth - 1) for v in items]
            elif isinstance(value, dict):
                shape["len"] = len(value)
                shape["dict_items"] = [[describe(k, depth - 1), describe(v, depth - 1)] for k, v in list(value.items())[:MAX_ITEMS]]
        except Exception:  # noqa: BLE001 - exotic containers
            pass
    return shape


def main() -> None:
    target, out_path = os.path.abspath(sys.argv[1]), sys.argv[2]
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
    except Exception:  # noqa: BLE001 - not available on every platform
        pass

    result: dict = {"status": "success", "probes": [], "frames": [], "python_version": sys.version.split()[0]}
    executed: set[int] = set()

    def probe(obj, *args, **kwargs):
        frame = sys._getframe(1)
        if frame.f_code.co_filename == target and len(result["probes"]) < MAX_PROBES:
            result["probes"].append({"line": frame.f_lineno, "shape": describe(obj)})
        return obj

    import typing

    typing.reveal_type = probe  # type: ignore[assignment]
    builtins.reveal_type = probe  # type: ignore[attr-defined]
    try:
        import typing_extensions

        typing_extensions.reveal_type = probe  # type: ignore[assignment]
    except ImportError:
        pass

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != target:
            return None
        if event == "line":
            executed.add(frame.f_lineno)
        return tracer

    def on_alarm(signum, frame):
        raise TimeoutError(f"program exceeded {timeout}s")

    with open(target, encoding="utf-8") as fh:
        source = fh.read()
    module = types.ModuleType("__main__")
    module.__file__ = target
    sys.modules["__main__"] = module
    sys.argv = [target]
    try:
        code = compile(source, target, "exec")
    except SyntaxError as exc:
        result.update(status="exception", exc_type="SyntaxError", exc_message=str(exc), exc_line=exc.lineno)
        _dump(out_path, result, executed)
        return
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, on_alarm)
        signal.alarm(timeout)
    sys.settrace(tracer)
    try:
        exec(code, module.__dict__)
    except SystemExit as exc:
        if exc.code not in (None, 0):
            result.update(status="exception", exc_type="SystemExit", exc_message=str(exc.code))
    except TimeoutError as exc:
        result.update(status="timeout", exc_type="TimeoutError", exc_message=str(exc))
    except BaseException as exc:  # noqa: BLE001 - we report everything the program raises
        frames = [(f.lineno, f.name) for f in traceback.extract_tb(exc.__traceback__) if f.filename == target]
        result.update(
            status="exception",
            exc_type=type(exc).__qualname__,
            exc_message=str(exc)[:500],
            exc_line=frames[-1][0] if frames else None,
            frames=frames,
        )
    finally:
        sys.settrace(None)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    _dump(out_path, result, executed)


def _dump(out_path: str, result: dict, executed: set[int]) -> None:
    result["executed_lines"] = sorted(executed)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh)


if __name__ == "__main__":
    main()
