# Replay data

`day10/` holds what is needed to replay the last generation round of the study (250 programs, "round 10") without an
LLM:

| Path | Content |
|---|---|
| `day10/answers/<key>.answer.json` | the 250 answers of the generator model (`claude-haiku-5.5`, effort medium); `<key>` is the first 16 hex characters of the sha256 of the prompt (see [docs/llm-setup.md](../../docs/llm-setup.md#the-file-bridge-filedir)) |
| `day10/parents/<group>/*.py` | the 45 parent programs of the round, grouped as in the run (`C_*`, `H_new`, `N_*`, `O_overload`, `R_reserve`) |

Run `scripts/replay_day10.sh` from anywhere in the repository. How it works, the expected numbers and the limits are in
[docs/generation.md](../../docs/generation.md) and [docs/reproducibility.md](../../docs/reproducibility.md). Total size:
about 1.2 MB.

Do not edit a parent file or `typediff/prompts.py` without re-keying the answers: the prompt text, including the header
comments of a parent, is part of the key.
