# typediff case variadic_callback
target Python 3.13 | versions: mypy=mypy 2.4.0 (compiled: yes), ty=ty 0.0.91, pyright=pyright 1.1.414, runtime=3.13.16
runtime: exception (TypeError: can only concatenate str (not "int") to str)
discrepancies: 1 | crashes: 0 | LLM calls: 0

| id | tier | verdict | tool | class | conf | decided by | statement |
|---|---|---|---|---|---|---|---|
| D1 | review | NEEDS_HUMAN | unknown | - | 0.00 | gate | L12: `print(invoke(increment, "bad"))` |

## D1 - review
- kind: only_mypy; mypy: L12:14 error[arg-type] Argument 1 to "invoke" has incompatible type "Callable[[int], int]"; expected "Callable[[str], int]"; ty: -
- reasoning: no LLM configured (TYPEDIFF_LLM=null): needs a human
- evidence [RUNTIME/strong/verified, supports bug]: CPython raised TypeError: can only concatenate str (not "int") to str with this statement on the stack (frames [(12, '<module>'), (5, 'invoke'), (9, 'increment')]). Checker output here: L12:14 error[arg-type] Argument 1 to "invoke" has incompatible type "Callable[[int], int]"; expected "Callable[[st
- evidence [CONSENSUS/weak/verified, supports neutral]: pyright behaves like mypy at this statement (weak evidence)
