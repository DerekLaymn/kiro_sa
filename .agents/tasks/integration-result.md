# Integration result

Branch `integration-fixes` (worktree `.worktrees/integration`), no conflicts.
Merge commits: 5326641 fixA-evidence, 17b9c7b fixB-runtime-miss, f7004f6 fixC-provenance, 9c34db0 fixD-kb.

Tests: full pytest 76 passed (typediff imported from the worktree). `typediff kb-selftest`: all entries PASS (last 8 lines inspected, all PASS).

## KB entry review (fixD)
- ANNOTATION-ONLY-READ: narrow. Needs ty-only unresolved-reference for one name, pyright unbound, mypy silent, and an AST scan of the enclosing function/module scope. The scan finds a bare `x: T` before the read and no other binding (assign, import, def/class, for/with/walrus targets, except/match names, global/nonlocal, params). Class scope is excluded. Verdict: OK. Residual risk is `globals()`/`exec` binding or a binding in another module, which is negligible.
- MYPY-15182-NEW-RETURNS: narrow. Needs the mypy `__new__` misc error naming the class, ty == pyright, ty != mypy, and the runtime probe inhabiting ty's type. Verdict: OK. Whether the upstream fix is in mypy 2.4.0 is unverified, as the entry says.
- JOIN-VS-UNION-CALLABLE: narrow. Needs all three tools to agree on the same class set. The base class must be defined in the source, and every member must derive from it or have a `__new__` returning it or a subclass. It demotes a runtime exception only when it is at the same statement. Verdict: OK.
- MDTEST-TODO: the weakest. It matches `# TODO ... should error` anywhere in the 3 lines above the anchor, for RUNTIME_MISS and ONLY_MYPY. It does not check that the TODO refers to this statement, so an unrelated bug within 3 lines below a TODO could be dismissed. Verdict: acceptable because mdtest TODOs sit directly above the statement, and it is logged as KNOWN_LIMITATION rather than discarded. No change made. Possible tightening: require that the TODO line be followed only by blank or comment lines before the anchor.

Live leads on merged code: the metaclass ClassVar vs declared-only attr lead and ty__call__replace__9.py (harness noise from the mdtest python version) are not covered by any new entry, so both stay live review items.

Fixes made during integration: none.

## Commands
Merge into main:
`git -C /home/micropp/Documents/kiro_sa merge --no-ff integration-fixes`

Clean up afterwards:
```
cd /home/micropp/Documents/kiro_sa
for w in integration fixA-evidence fixB-runtime-miss fixC-provenance fixD-kb; do git worktree remove --force .worktrees/$w; done
git branch -d integration-fixes fixA-evidence fixB-runtime-miss fixC-provenance fixD-kb
```
