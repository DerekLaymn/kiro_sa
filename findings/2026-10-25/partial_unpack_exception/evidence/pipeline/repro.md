# typediff case repro
target Python 3.13 | versions: mypy=mypy 2.4.0 (compiled: yes), ty=ty 0.0.91, pyright=pyright 1.1.414, runtime=3.13.16
runtime: exception (AttributeError: 'str' object has no attribute 'bit_length')
discrepancies: 1 | crashes: 0 | LLM calls: 0

| id | tier | verdict | tool | class | conf | decided by | statement |
|---|---|---|---|---|---|---|---|
| D1 | review | NEEDS_HUMAN | unknown | - | 0.00 | gate | L6: `print(value.bit_length())` |

## D1 - review
- kind: only_mypy; mypy: L6:15 error[union-attr] Item "str" of "int | str" has no attribute "bit_length"; ty: -
- KB matches: GRADUAL-OPERAND
- reasoning: no LLM configured (TYPEDIFF_LLM=null): needs a human
- evidence [RUNTIME/strong/verified, supports bug]: CPython raised AttributeError: 'str' object has no attribute 'bit_length' with this statement on the stack (frames [(9, '<module>'), (6, 'run')]). Checker output here: L6:15 error[union-attr] Item "str" of "int | str" has no attribute "bit_length". Check the exception is caused by the reported issue
- evidence [CONSENSUS/weak/verified, supports neutral]: pyright behaves like ty at this statement (weak evidence)
- evidence [EXPERIMENT/medium/verified, supports neutral]: E1 operand types: value.bit_length: mypy=(def () -> int) | Any ty=bound method Literal[1].bit_length() -> int pyright=() -> int runtime=None [uncomparable]; value: mypy=int | str ty=Literal[1] pyright=Literal[1] runtime=None [ty_more_precise]
