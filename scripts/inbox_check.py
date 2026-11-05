#!/usr/bin/env python
"""Account for a file-bridge inbox: prompts, answers, pending prompts, answers that match no prompt.

    python scripts/inbox_check.py runs/day5/inbox

Exit 1 if an answer matches no prompt or a key is not 16 hex characters (the bridge silently ignores those).
"""

from __future__ import annotations

import sys

from typediff.llm import inbox_status


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    s = inbox_status(sys.argv[1])
    print(f"prompts={s['prompts']} (retry prompts={s['retry_prompts']}) answers={s['answers']} answered={s['answered']} "
          f"pending={len(s['pending'])} orphan_answers={len(s['orphan_answers'])} malformed_keys={len(s['malformed_keys'])}")
    for k, near in s["orphan_answers"].items():
        print(f"ORPHAN answer {k}.answer.json: no prompt with this key; prompts one edit away: {near or 'none'}")
    for k in s["malformed_keys"]:
        print(f"MALFORMED key {k}")
    return 1 if s["orphan_answers"] or s["malformed_keys"] else 0


if __name__ == "__main__":
    sys.exit(main())
