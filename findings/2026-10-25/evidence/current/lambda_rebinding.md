# typediff case lambda_rebinding
target Python 3.13 | versions: mypy=mypy 2.4.0 (compiled: yes), ty=ty 0.0.91, pyright=pyright 1.1.414, runtime=3.13.16
runtime: exception (TypeError: unsupported operand type(s) for +: 'NoneType' and 'int')
discrepancies: 1 | crashes: 0 | LLM calls: 0

| id | tier | verdict | tool | class | conf | decided by | statement |
|---|---|---|---|---|---|---|---|
| D1 | review | NEEDS_HUMAN | unknown | - | 0.00 | gate | L7: `callback = lambda: value + 1` |

## D1 - review
- kind: only_ty; mypy: -; ty: L7:24 error[unsupported-operator] Operator `+` is not supported between objects of type `int | None` and `Literal[1]`
- KB matches: PARTIAL-TYPES
- reasoning: no LLM configured (TYPEDIFF_LLM=null): needs a human
- evidence [RUNTIME/strong/verified, supports bug]: CPython raised TypeError: unsupported operand type(s) for +: 'NoneType' and 'int' with this statement on the stack (frames [(12, '<module>'), (7, '<lambda>')]). Checker output here: L7:24 error[unsupported-operator] Operator `+` is not supported between objects of type `int | None` and `Literal[1]`.
- evidence [CONSENSUS/weak/verified, supports neutral]: pyright behaves like ty at this statement (weak evidence)
- evidence [EXPERIMENT/medium/verified, supports neutral]: E1 operand types: value: mypy=int ty=int pyright=int runtime=builtins.int [equal]
