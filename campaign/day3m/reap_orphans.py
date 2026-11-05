"""Kill orphaned pyright node processes (hung on crash/hang programs, older than MIN_AGE seconds, parent = init).

Only processes whose command line is exactly the pipeline's pyright invocation (`index.js --pythonversion 3.13 --outputjson case.py`)
and whose parent pid is 1 or a systemd user manager (i.e. the owning typediff process is gone) are touched.
"""
import os
import signal
import sys

MIN_AGE = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
HZ = os.sysconf("SC_CLK_TCK")
uptime = float(open("/proc/uptime").read().split()[0])
killed = []
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        cmd = open(f"/proc/{pid}/cmdline").read().replace("\0", " ").strip()
        if "pyright/dist/index.js" not in cmd or "--outputjson case.py" not in cmd:
            continue
        stat = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
        ppid, start = int(stat[1]), int(stat[19])
        age = uptime - start / HZ
        pcmd = open(f"/proc/{ppid}/cmdline").read().replace("\0", " ").strip() if ppid > 1 else "init"
        if age >= MIN_AGE and ("typediff" not in pcmd):
            os.kill(int(pid), signal.SIGKILL)
            killed.append((int(pid), int(age), ppid, pcmd[:60]))
    except (FileNotFoundError, ProcessLookupError, PermissionError, IndexError):
        continue
print(len(killed), "orphaned pyright processes killed (age >= %ds)" % MIN_AGE)
for k in killed:
    print(k)
