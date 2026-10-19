# Testing the New Mutation Operators

This guide shows how to test the newly added `type_erasure` and `type_overwriting` operators.

## What Was Added

✅ **2 new mutation operators**: `type_erasure`, `type_overwriting`  
✅ **1 new operator category**: `GRADUAL_OPS` = `[type_erasure, type_overwriting, gradual_injection]`  
✅ **Updated prompts**: LLM strategist and generator now know about these operators  
✅ **Example file**: `examples/mutation_examples.py` with 6 examples

## Files Modified

1. **`typediff/prompts.py`** - Added operators to line 268-269 and usage guidelines
2. **`typediff/strategy.py`** - Added `GRADUAL_OPS` list on line 59
3. **`examples/mutation_examples.py`** (new) - Example transformations

---

## Quick Test (No LLM Required)

Verify the changes are recognized:

```bash
# 1. Check operators are in the prompt
grep -A2 "type_erasure" typediff/prompts.py

# 2. Check GRADUAL_OPS is defined
grep "GRADUAL_OPS" typediff/strategy.py

# 3. View examples
cat examples/mutation_examples.py
```

---

## Test With LLM (Requires API Key)

### Option 1: OpenRouter (Free Tier)

```bash
# Set up environment
export OPENAI_API_KEY="your-openrouter-key"
export TYPEDIFF_LLM_MIN_INTERVAL=3.5  # 20 req/min limit

# Generate 1 program using the new operators
TYPEDIFF_LLM="openai:qwen/qwen-2.5-72b-instruct:free@https://openrouter.ai/api/v1" \
  typediff --python-version 3.13 generate \
  --area gradual_any \
  --brief "Test type inference when annotations are removed from generic functions" \
  --n 1 \
  --ops type_erasure \
  --out-dir test_output

# Check the generated program
cat test_output/*.py
```

### Option 2: Anthropic Claude

```bash
export ANTHROPIC_API_KEY="your-key"

TYPEDIFF_LLM="anthropic:claude-sonnet-4" \
  typediff --python-version 3.13 generate \
  --area gradual_any \
  --brief "Test soundness by introducing wrong type annotations" \
  --n 1 \
  --ops type_overwriting \
  --out-dir test_output
```

### Option 3: Local Ollama

```bash
# Start Ollama with a coding model
ollama pull deepseek-coder

TYPEDIFF_LLM="openai:deepseek-coder@http://localhost:11434/v1" \
  typediff generate \
  --area gradual_any \
  --n 1 \
  --ops type_erasure,type_overwriting \
  --out-dir test_output
```

---

## Manual Testing (Understanding the Transformations)

Create a simple seed and manually apply the mutations:

### Example: type_erasure

**Seed file** (`test_seed.py`):
```python
from typing import reveal_type, TypeVar

T = TypeVar('T')

def double(x: T) -> tuple[T, T]:
    return (x, x)

result = double([1, 2, 3])
reveal_type(result)
```

**After manual type_erasure**:
```python
from typing import reveal_type, TypeVar

T = TypeVar('T')

def double(x):  # ← Removed T annotation
    return (x, x)

result = double([1, 2, 3])
reveal_type(result)
```

**Test both:**
```bash
# Original
mypy test_seed.py
ty check test_seed.py

# After erasure
mypy test_erased.py
ty check test_erased.py

# Compare results
```

---

## Integration Testing

Test that the strategy system uses the new operators:

```python
# test_gradual_ops.py
from typediff.strategy import GRADUAL_OPS, Strategy
from typediff.llm import CachedLLM, NullLLM
from pathlib import Path

# Check operators are registered
print("GRADUAL_OPS:", GRADUAL_OPS)
assert "type_erasure" in GRADUAL_OPS
assert "type_overwriting" in GRADUAL_OPS
print("✓ Operators registered")

# Test strategy (without LLM)
strategy = Strategy("test_strategy.json", llm=CachedLLM(NullLLM()))
area = "gradual_any"

# The strategy should know about these operators
print(f"✓ Strategy initialized for area: {area}")
print("✓ All tests passed!")
```

Run it:
```bash
python test_gradual_ops.py
```

---

## Full Campaign Test (With LLM)

Run a mini-campaign focusing on gradual typing:

```bash
# Generate 5 programs with the new operators
TYPEDIFF_LLM="anthropic:claude-sonnet-4" \
  typediff --python-version 3.13 \
  generate --from-seeds seeds/gradual_any \
  --n 5 \
  --ops type_erasure,type_overwriting,gradual_injection \
  --out-dir runs/gradual_test

# Judge them (deterministic, no LLM)
TYPEDIFF_LLM=null \
  typediff --python-version 3.13 \
  seeds runs/gradual_test \
  --out runs/gradual_results

# Triage the results
typediff triage runs/gradual_results --top 10
```

---

## Expected Output Examples

### Good Generation (type_erasure)

```python
# area: gradual_any
# hypothesis: ty infers Unknown when generic parameter annotation is removed

from typing import reveal_type, TypeVar

T = TypeVar('T')

def wrap(x):  # Generic parameter annotation removed
    return [x, x]

result = wrap(42)
reveal_type(result)  # mypy: list[int], ty: list[Unknown]?
```

### Good Generation (type_overwriting)

```python
# area: gradual_any
# hypothesis: checker trusts wrong return type annotation

from typing import reveal_type

def get_data() -> list[int]:  # Says list, returns dict
    return {"key": "value"}

data = get_data()
reveal_type(data)  # Does checker say list[int]?

try:
    data[0]  # List indexing on dict - crashes!
except (TypeError, KeyError):
    print("Runtime caught the type lie")
```

---

## Validation Checklist

After generation, check these criteria:

✅ **Preflight passes** - No "ERROR:" in output  
✅ **Standard library only** - No third-party imports  
✅ **Deterministic** - No random, time, I/O  
✅ **Executable** - All functions called  
✅ **Has reveal_type** - At least one reveal_type() call  
✅ **Applies mutation** - Annotations removed or wrong types added

---

## Common Issues and Solutions

### Issue 1: "generate needs an LLM"

**Solution:** Set `TYPEDIFF_LLM` environment variable
```bash
export TYPEDIFF_LLM="anthropic:claude-sonnet-4"
# or
export TYPEDIFF_LLM="openai:gpt-4"
```

### Issue 2: Rate limiting (OpenRouter)

**Solution:** Increase interval
```bash
export TYPEDIFF_LLM_MIN_INTERVAL=5.0  # 12 requests/min
```

### Issue 3: Invalid programs generated

**Problem:** LLM doesn't understand the mutation  
**Solution:** The prompts now include guidelines - retry or use a better model

### Issue 4: Mutations not applied

**Check:**
```bash
# The operator should appear in the mutation instruction
grep -r "type_erasure\|type_overwriting" test_output/
```

---

## Next Steps

Once you've verified the operators work:

1. **Add to campaign**: Include them in `FUZZING_PLAN.md` day 3-10 loop
2. **Create targets**: Make seed files specifically for erasure/overwriting
3. **Run at scale**: Generate 100+ variants to find real bugs
4. **File issues**: When you find bugs, use `typediff report` to draft the issue

---

## Debugging Tips

### See what the LLM receives:

```bash
# Use file mode to inspect prompts
TYPEDIFF_LLM="file:llm_debug" \
  typediff generate --area gradual_any --n 1 --ops type_erasure

# Check the prompt
cat llm_debug/*.prompt.md
```

### Enable verbose mode:

```python
# Add to your test script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual prompt test:

Copy the GENERATOR_SYSTEM and GENERATOR_USER from `prompts.py` and test directly with your LLM's playground.

---

## Success Criteria

You know the operators work when:

✅ `grep "type_erasure\|type_overwriting" typediff/prompts.py` finds them  
✅ Generated programs have annotations removed (`type_erasure`)  
✅ Generated programs have wrong types (`type_overwriting`)  
✅ Preflight validation passes  
✅ Programs run under CPython without syntax errors  
✅ At least one produces a `mypy ≠ ty` discrepancy

---

## Contact for Issues

If you encounter problems:
1. Check `typediff --help` for correct syntax
2. Verify LLM API keys are set
3. Review the examples in `examples/mutation_examples.py`
4. Check the diff: `git diff typediff/prompts.py typediff/strategy.py`

**Your mutations are ready to hunt bugs!** 🎯
