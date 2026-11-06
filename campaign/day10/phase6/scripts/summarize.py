#!/usr/bin/env python3
"""usage: summarize.py name...  -> results/<name>.sum.txt, one short line per diagnostic and tool.
Reads results/<name>.txt written by runall.sh."""
import os
import re
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.environ.get("RESDIR", "results")  # results2 for round-2 probes
for name in sys.argv[1:]:
    src = open(f"{P}/{R}/{name}.txt").read().splitlines()
    out = []
    tool = None
    i = 0
    while i < len(src):
        ln = src[i]
        m = re.match(r"^--- (\S+ \S+)", ln)
        if m:
            tool = m.group(1)
            out.append(f"--- {ln[4:]}")
            i += 1
            continue
        if tool and tool.startswith("ty"):
            m = re.match(r"^(error|warning|info)\[([\w-]+)\]: (.*)", ln)
            if m:
                loc = ""
                j = i + 1
                while j < len(src) and not src[j].startswith("-->") and not src[j].strip().startswith("-->"):
                    j += 1
                    if j - i > 3:
                        break
                if j < len(src):
                    lm = re.search(r":(\d+):(\d+)\s*$", src[j])
                    loc = f"L{lm.group(1)}" if lm else ""
                # find the caret line with message
                k = j + 1
                note = ""
                while k < len(src) and not re.match(r"^(error|warning|info)\[", src[k]) and not src[k].startswith("Found") and k - j < 14:
                    cm = re.match(r"^\s*\|\s*\^+\s*(.*)$", src[k])
                    if cm and cm.group(1):
                        note = cm.group(1)
                        break
                    k += 1
                out.append(f"  {loc} {m.group(1)}[{m.group(2)}] {m.group(3)} {('| ' + note) if note else ''}")
            elif ln.startswith("rc=") or ln.startswith("Found") or ln.startswith("All checks"):
                out.append("  " + ln)
        elif tool and tool.startswith("mypy"):
            ln2 = re.sub(r"^.*?/repro/", "", ln)
            if ln2.strip():
                out.append("  " + ln2)
        elif tool and tool.startswith("pyright"):
            ln2 = re.sub(r"^\s*/.*?/repro/", "  ", ln)
            if ln2.strip() and not ln2.strip().startswith("/"):
                out.append(ln2)
        elif tool and tool.startswith("cpython"):
            out.append("  " + ln)
        i += 1
    open(f"{P}/{R}/{name}.sum.txt", "w").write("\n".join(out) + "\n")
print("ok", len(sys.argv) - 1)
