#!/usr/bin/env bash
# Day 9 generator: one headless kiro-cli session (claude-haiku-5.5, medium effort, agent engine v3) answers a batch of
# file-bridge prompts. Usage: gen_worker.sh KEY [KEY ...]   (keys = 16-hex prompt ids in runs/day9/inbox)
ROOT=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
INBOX=$ROOT/runs/day9/inbox
WORK=/tmp/d9/work
mkdir -p "$WORK" /tmp/d9/logs
LIST=""
for k in "$@"; do LIST="$LIST
- prompt: $INBOX/$k.prompt.md -> write answer to: $INBOX/$k.answer.json"; done
MSG="You are the program generator for a type-checker fuzzing pipeline. For EACH item below: read the prompt file (it has a SYSTEM and a USER section with the exact task and constraints), do what it asks (write one Python 3.13 program), and write the JSON answer file with the fs_write tool. The answer file must be ONE JSON object with exactly the keys \"source\" (the full program text as a JSON string), \"hypothesis\" (one sentence) and \"features\" (a list of short strings). Do not run the program, do not run type checkers, do not use any tool other than reading the prompt and writing the answer. Write the answer file path exactly as given (the 16-hex key must not change). Items:$LIST
When all answer files are written, reply with the single word DONE."
cd "$WORK" || exit 1
kiro-cli chat --agent-engine v3 --model claude-haiku-5.5 --effort medium --no-interactive --trust-tools=fs_read,fs_write "$MSG" > "/tmp/d9/logs/worker-$$-$1.log" 2>&1
echo "rc=$? keys=$#" >> "/tmp/d9/logs/worker-$$-$1.log"
