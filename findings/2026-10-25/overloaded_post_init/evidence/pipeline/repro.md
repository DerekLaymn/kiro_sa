# typediff case repro
target Python 3.13 | versions: mypy=mypy 2.4.0 (compiled: yes), ty=ty 0.0.91, pyright=pyright 1.1.414, runtime=3.13.16
runtime: success
discrepancies: 1 | crashes: 0 | LLM calls: 0

| id | tier | verdict | tool | class | conf | decided by | statement |
|---|---|---|---|---|---|---|---|
| D1 | review | NEEDS_HUMAN | unknown | - | 0.00 | gate | L12: `def __post_init__(self, value: str) -> None: ...` |

## D1 - review
- kind: only_mypy; mypy: L12:29 error[override] Argument 2 of "__post_init__" is incompatible with supertype "dataclass"; supertype defines the argument type as "int"; ty: -
- reasoning: no LLM configured (TYPEDIFF_LLM=null): needs a human
- evidence [RUNTIME/weak/verified, supports neutral]: statement executed under CPython without a type-related exception (does NOT prove a rejection spurious)
- evidence [CONSENSUS/weak/verified, supports neutral]: pyright behaves like ty at this statement (weak evidence)
