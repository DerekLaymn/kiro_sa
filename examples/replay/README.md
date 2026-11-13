# Replay data

`day10/` holds what is needed to replay the Day-10 round (250 generated programs) without an LLM:

| Path | Content |
|---|---|
| `day10/answers/<key>.answer.json` | the 250 answers of the generator model (`claude-haiku-5.5`, effort medium); `<key>` is the hash of the prompt |
| `day10/parents/<group>/*.py` | the 45 parent programs of the round, grouped as in the run (`C_*`, `H_new`, `N_*`, `O_overload`, `R_reserve`) |

Run `scripts/replay_day10.sh` from anywhere in the repository. How it works, the expected numbers and the limits are in
[docs/generation.md](../../docs/generation.md). Total size: about 1.2 MB.
