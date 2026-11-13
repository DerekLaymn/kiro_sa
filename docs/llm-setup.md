# LLM setup

typediff works without any LLM. The judge, the knowledge base (KB), the tests and `scripts/reproduce.sh` are
deterministic and never call a model. An LLM is needed for two things only:

1. **Program generation** (`typediff generate`, `typediff loop`, `typediff seeds --mutate`): a model writes or mutates the
   Python programs that are then checked.
2. **Adjudication** of discrepancies that the rules and the KB cannot decide (`judge`, `run`, `seeds`, `loop`, `report`):
   a model reads the evidence and proposes a verdict, which citation checks and a skeptic/advocate pass then constrain
   (see [architecture.md](architecture.md#llm-adjudication-and-the-gate)). Without an LLM those discrepancies stay in
   the human review queue.

The published campaign used a model for generation only. Its judge ran with `TYPEDIFF_LLM=null`.

## Where the API key goes

typediff reads the provider and the key from environment variables. Put them in a `.env` file in the directory you run
`typediff` from, or export them in your shell.

```bash
cp .env.example .env      # .env is git-ignored
$EDITOR .env              # set TYPEDIFF_LLM and the matching key
```

| Variable | Used for | Notes |
|---|---|---|
| `TYPEDIFF_LLM` | Selects the provider and model. Default `null` (no LLM). | Overridden by `--llm` on the command line. |
| `ANTHROPIC_API_KEY` | `anthropic:<model>` | Sent as the `x-api-key` header to `https://api.anthropic.com/v1/messages`. |
| `OPENAI_API_KEY` | `openai:<model>` | Sent as a bearer token. May stay empty for a local server (see `OPENAI_BASE_URL`). |
| `OPENAI_BASE_URL` | `openai:<model>` | Base URL of an OpenAI-compatible endpoint. Default `https://api.openai.com/v1`. The model spec can carry its own URL: `openai:<model>@<url>`. |
| `TYPEDIFF_LLM_MIN_INTERVAL` | HTTP providers | Seconds to wait between requests (rate limits). Default `0`. |
| `TYPEDIFF_CACHE` | HTTP providers | Directory of the response cache. Default `~/.cache/typediff/llm`. |
| `TYPEDIFF_DOCS` | `fetch-docs`, citation checks | Directory of the downloaded documentation corpus. Default `~/.cache/typediff/docs`. |
| `TYPEDIFF_MYPY`, `TYPEDIFF_TY`, `TYPEDIFF_PYRIGHT` | tool discovery | Command used to start each checker. Default: the executable next to the Python interpreter, then `PATH`. |
| `TYPEDIFF_RUNTIME_PYTHON` | runtime oracle | Interpreter that runs the generated programs. Default: the interpreter running typediff. |

How `.env` is handled (`typediff/envfile.py`):

- Only the `typediff` command reads it, from the current directory. The scripts in `scripts/` do not; export the
  variables first with `set -a; . ./.env; set +a`.
- A variable that is already set in the shell is never overridden.
- Empty values are ignored, so the template lines `ANTHROPIC_API_KEY=` do nothing until you fill them in.
- `TYPEDIFF_CACHE` and `TYPEDIFF_DOCS` are read when Python starts, before `.env` is loaded. Set those two in the shell.
- If the selected provider needs a key that is missing, typediff stops with
  `error: ANTHROPIC_API_KEY is not set, but TYPEDIFF_LLM selects the anthropic provider ...` and exit code 2.
- Never commit `.env`. `.gitignore` already excludes it; only `.env.example` is tracked.

## `TYPEDIFF_LLM` values

| Value | Behaviour |
|---|---|
| `null` | No LLM. Deterministic stages only; undecided discrepancies go to the human queue. `generate` and `loop` refuse to run (exit code 2). |
| `anthropic:<model>` | Anthropic Messages API. Needs `ANTHROPIC_API_KEY`. |
| `openai:<model>` | OpenAI chat completions. Needs `OPENAI_API_KEY`. |
| `openai:<model>@http://localhost:8000/v1` | Any OpenAI-compatible server (vLLM, Ollama, LiteLLM). No key needed when a base URL is given. |
| `file:<dir>` | The file bridge. Prompts are written to `<dir>`, answers are read from `<dir>`. See below. |

Examples:

```bash
TYPEDIFF_LLM=anthropic:<model> typediff --python-version 3.13 generate --area protocols --n 3 --out-dir runs/gen
typediff --llm openai:<model>@http://localhost:11434/v1 --python-version 3.13 generate --area protocols --n 3 --out-dir runs/gen
typediff --llm file:runs/inbox --python-version 3.13 generate --area protocols --n 3 --out-dir runs/gen
```

Replace `<model>` with a model id your provider offers. typediff does not validate model names.

## Caching and cost

- HTTP providers are wrapped in an on-disk cache. The key is a hash of the provider name, the system prompt, the user
  prompt, the temperature and the seed. Re-running the same command costs nothing for requests already answered.
- `null` and `file:` calls are never cached; the file bridge keeps its own files.
- `--max-llm-calls N` (on `generate`, `seeds` and `loop`) stops the run after `N` uncached calls. Use it for a first
  test.
- Generation makes one call per program. A program that fails the preflight lint is re-requested once, and an answer
  that is not valid JSON is re-asked up to two more times, so the worst case is a few calls per program. Each call asks
  for at most 3000 output tokens.
- Adjudication costs calls only for discrepancies the KB and rules left undecided: up to 3 rounds per batch of 8
  discrepancies, plus one skeptic or advocate call per verdict that needs it.
- No dollar figures are given because they depend on the model. Start with `--n 1 --max-llm-calls 10`, then scale up.

## Sampling settings

| Setting | Value | Where |
|---|---|---|
| Generation temperature | 0.8, fixed | `typediff/generator.py` |
| Generation `max_tokens` | 3000, fixed | `typediff/generator.py` |
| Other calls (adjudicator, strategist, reporter) | temperature 0.0 | defaults of `LLM.complete` |
| Self-consistency votes | temperature 0.7; off by default (`GateConfig.votes = 1`), not exposed on the command line | `typediff/adjudicator.py` |
| Seed | the variant index `k` of `generate --n N` (0 to N-1). It is part of the prompt and the cache key. The OpenAI-compatible client also sends it as `seed`. The Anthropic API does not receive it, and the file bridge uses it only in the prompt key. | `typediff/generator.py`, `typediff/llm.py` |

Because sampling is not fixed, two generation runs with the same model give different programs. See
[reproducibility.md](reproducibility.md) for what that means for results and how the stored answers avoid it.

## The file bridge (`file:<dir>`)

The bridge lets a person or another program play the model. Nothing needs an API key.

1. Run any generating command with `--llm file:<dir>`. For each request typediff writes
   `<dir>/<key>.prompt.md` (a `# SYSTEM` part and a `# USER` part). `<key>` is the first 16 hex characters of
   `sha256(system + user + seed)`.
2. Write the answer to `<dir>/<key>.answer.json`. For program generation the file holds one JSON object:

   ```json
   {"source": "<python program>", "hypothesis": "<what is being tested>", "features": ["protocol", "generic"]}
   ```

   Other roles use the schema stated in their prompt (`typediff/prompts.py`).
3. Run the same command again. Requests that now have an answer are used; the rest stay pending.
4. Check progress with `python scripts/inbox_check.py <dir>`. It prints prompt, answer, pending and orphan counts, and
   exits with 1 when an answer matches no prompt or a key is not 16 hex characters. The bridge silently ignores such
   answers, so run the check before you trust a batch.

An answer can be written by a person, by a script, or by a coding agent working through the prompts. typediff does not
care which. The campaign's generation used an agent for step 2.

## Model and settings used for the published results

| Setting | Value |
|---|---|
| Generator | `claude-haiku-5.5` as a stand-in model, reasoning effort `medium` |
| Transport | file bridge (agent sessions answering the prompts), so the temperature and seed above did not apply |
| Judge | `TYPEDIFF_LLM=null`: no LLM |
| Target Python | 3.13 |
| Programs per round | about 250 (250 in the last round) |

The 250 answers of the last round are stored in `examples/replay/day10/answers/`, so that round can be replayed
without a model. See [reproducibility.md](reproducibility.md#5-replay-the-last-round-without-an-llm) and
[generation.md](generation.md).

## Safety notes

- Generated programs are untrusted code and are executed by the runtime oracle. Run typediff in a container or a
  throwaway environment without network access when you use a model you do not control.
- Prompts contain program text and tool output. The judge prompt labels them as data and the experiment requests a
  model can make go through allow-lists (flags, side-effect-free probe expressions, size limits).
