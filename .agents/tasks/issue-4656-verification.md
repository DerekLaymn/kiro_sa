# Verification of ty issue #4656 ("Self parameter is not enforced on inherited methods")

Read-only investigation. Nothing under `typediff/` or `examples/` was modified. All scripts and raw outputs are in `/tmp/v4656/` (details in section 8).

## 1. Verdict

**PARTLY RIGHT.** The maintainer (carljm) is right that this is deliberate behaviour and not a spec violation, so "Not planned" is a fair outcome. One of his arguments is overstated.

The strongest reason he is right: PEP 673 defines `Self` in a method signature as a TypeVar bound to the class. Ordinary TypeVar solving then allows `Self := Node` in `Leaf().add(Node())`. Rejecting the call is a different design choice, not something the spec requires. The maintainer's Liskov example holds up when I run it. The `use_node(leaf)` program is accepted by all five checkers I tried (ty, mypy, pyright, pyrefly, zuban), and it crashes in CPython. Nothing in the typing spec's conformance suite covers this case either.

Where he overstates: "The ty interpretation does not have this problem." ty is also unsound here, by a different route. ty binds `Self` to the receiver for attributes (`B().x` is `B`), but joint-solves `Self` for method parameters. A method that stores its `Self` parameter into a `Self`-typed attribute therefore puts a `Node` into a slot ty believes holds a `Leaf`. I reproduced this with the PEP's own `LinkedList.next: Self | None` example. ty reports "All checks passed" and CPython raises `AttributeError`. carljm has already called the attribute specialisation unsound himself (section 3, C3).

The filed report was really "ty differs from mypy/pyright on an acknowledged spec ambiguity". ty's own tracker already held this exact design discussion (#1172, Sept 2025).

## 2. Claim table

| # | Claim | Status | Proof pointer |
|---|---|---|---|
| C1 | Spec says `Self` is a TypeVar bounded by the defining class | **SUPPORTED** (with a caveat: other PEP text points the other way) | PEP 673 "Use in Method Signatures"; section 3 |
| C2 | Solving `Self := Node` in `Leaf().add(Node())` is a legitimate reading | **PARTLY**. It is the literal desugaring, but the spec is ambiguous and the conformance suite has no test for it. | `conf/generics_self_basic.py`; `pep_setter_method.py` |
| C3 | mypy/pyright reading inherently breaks LSP; ty's reading does not have the problem | **PARTLY**. First half SUPPORTED, second half REFUTED. | `lsp_use_node_runtime.py`; `pep_bypass_clean.py` |
| C4 | `Node.add` must handle any `Node` since it is not overridden | **SUPPORTED as a typing fact; a crash is still reachable** via `Self`-typed state | `attr.py`, `pick.py`, `pep_bypass_clean.py` |
| C5 | typediff's claim quality | **WEAK.** The evidence rested on a display bug and ignored existing design discussion. | section 7 |

## 3. Evidence

### Environment and versions

Commands run in `/tmp/v4656/venv` (CPython 3.14.7 on Fedora).

```
ty 0.0.84
mypy 2.4.0 (compiled: yes)
pyright 1.1.414
pyrefly 1.3.2        (extra; pip-installable)
zuban 0.10.0         (extra; pip-installable)
```

These are the same ty/mypy/pyright versions typediff was calibrated with.

Two caveats:
- `gh` is not installed. I read the GitHub threads through the public REST API via web_fetch.
- `pyrefly check` with no config silently reports "0 errors" even for `x: int = "a"` (it falls back to a `basic` preset). All pyrefly results below use a `pyproject.toml` with `[tool.pyrefly]` in `/tmp/v4656/cases/`, and I verified the setup catches that error.

### C1. What the spec says

Sources: https://typing.python.org/en/latest/spec/generics.html#self and https://peps.python.org/pep-0673/. I read the full PEP text.

Text that supports the maintainer:
- "Use in Method Signatures": *"Self used in the signature of a method is treated as if it were a TypeVar bound to the class."* The PEP's desugaring is `def set_scale(self: SelfShape, ...) -> SelfShape` with `SelfShape = TypeVar(..., bound="Shape")`. The TypeVar is scoped to the method.
- "Use in Parameter Types" says the parameter form is equivalent to `def difference(self: Self, other: Self)`, with a method-scoped bound TypeVar. The PEP calls it *"parameters that expect instances of the current class"*. Content paraphrased.

Text that points the other way:
- "Use in Generic Classes": *"The behavior is to preserve the type argument of the object on which the method was called."* It then says that on a `Container[int]` object, `Self` is bound to `Container[int]`. This is receiver-binding language, though it is about type arguments.
- "Use in Attribute Annotations" is the strongest counter-text. It says `xs.next = LinkedList[int](...)` on an `OrdinalLinkedList` is a *"Type error: Expected OrdinalLinkedList, got LinkedList[int]."* It then says this is semantically equivalent to a property whose setter is `def next(self: Self, next: Self | None)`. That setter is a method with `Self` in a parameter, and the PEP requires the base instance to be rejected.

Nothing in the PEP or the spec discusses LSP, variance, or the soundness of `Self` in parameter position. That part is not addressed. The Pyre author made the same observation in https://discuss.python.org/t/unsoundness-of-contravariant-self-type/86338 (post 1).

**Status: SUPPORTED**, with the attribute/setter wording as a real counter-signal.

### C2. Is `Self := Node` a legitimate reading?

**Conformance suite.** I downloaded `generics_self_{basic,usage,advanced,protocols,attributes}.py` from `python/typing` `main`, plus ty's result files `conformance/results/ty/*.toml`.
- `generics_self_basic.py` defines `Shape.difference(self, other: Self)` and `class Circle(Shape)`. It never calls `Circle().difference(Shape())`. No other test covers a base-class instance passed to a `Self` parameter through a subclass receiver.
- ty's results for all five Self files are `conformance_automated = "Pass"` (checked for `advanced`, `attributes`, `basic`, `protocols`, `usage`).
- Conclusion: the suite is silent here, so neither side can claim a conformance violation. I did not check pyrefly's or zuban's conformance results.

**Live probes (run with each checker):**

```
# pep_difference.py: PEP's own `difference(self, other: Self)` through Circle
ty: accepts | mypy: rejects | pyright: rejects | pyrefly: rejects | zuban: rejects

# pep_linkedlist_attr.py: PEP attribute example, verbatim shape
all five: reject (ty: "Expected OrdinalLinkedList | None, found LinkedList[int]")

# pep_setter_method.py: PEP's "equivalent" property setter and a plain set_next(self, v: Self | None)
ty: accepts both | mypy, pyright, pyrefly, zuban: reject both
```

So ty follows the PEP's attribute example (no conformance failure) but accepts the exact "equivalent" setter form the PEP spells out. That means ty is not fully consistent with the PEP's stated equivalence. It is consistent with the PEP's TypeVar desugaring.

Other sources on the ambiguity:
- Sam Goldman (Pyre) in the discuss.python.org thread, post 18. Paraphrased: PEP 673's TypeVar translation supports carljm's method-scoped reading; mypy, pyright and pyrefly behave as if `Self` were a class-scoped parameter; both are reasonable interpretations.
- Jia Chen, post 1. Paraphrased: mypy is "unsound but spec-conforming", pyright "unsound and non-spec-conforming", Pyre "sound and spec-conforming".

**Status: PARTLY.** It is a legitimate literal reading, but it is not the only one, and the spec never says which is right.

### C3. "mypy/pyright reading breaks LSP; ty's does not"

**First half (SUPPORTED).** The maintainer's `use_node` example, extended to a crash (`lsp_use_node_runtime.py`):

```
ty: All checks passed!
mypy: (no output)         pyright: 0 errors
pyrefly: 0 errors         zuban: Success
CPython 3.14.7: AttributeError: 'Node' object has no attribute 'leaf_only'
```

All five checkers accept a program that crashes. Under the receiver-pinning reading, `node.add(Node())` inside `use_node` and `use_node(leaf)` are both legal, while `leaf.add(Node())` is illegal. There is no way for the checker to prevent that, exactly as carljm says.

Other evidence that the pinning reading is unsafe:
- Rebecca Chen (Pyrefly): "ideally, type checkers should reject all three examples" (the `Self` version, the bounded-TypeVar version, and the concrete-type version). Paraphrased from post 4 of the discuss.python.org thread.
- Eric Traut (pyright): agreed all three samples should be flagged as errors, and made a pyright fix so overrides are flagged (post 5).
- Ivan Levkivskyi (mypy, post 8): accepting this is a very conscious mypy decision. Treating it safely would make `Self` painful to use. A StackOverflow question quotes the mypy docs as saying generic self types in arguments are accepted even though unsafe (https://stackoverflow.com/questions/77807656). I did not open the mypy docs myself.
- carljm made the ty argument publicly on 2025-09-08 (post 13 of that thread), a year before this issue. His comment on #4656 repeats it.

**Second half (REFUTED).** "The ty interpretation does not have this problem."

The problem is real in ty, through a different route. In `attr.py`:

```python
class Node:
    def __init__(self) -> None:
        self.children: list[Self] = []
    def add(self, c: Self) -> Self:
        self.children.append(c)
        return self
class Leaf(Node):
    def leaf_only(self) -> int: return 1
x = Leaf()
reveal_type(x.children)      # ty: list[Leaf]  (attribute Self bound to receiver)
x.add(Node())                # ty accepts: Self solved to Node
print(x.children[0].leaf_only())
```

ty accepts the program with no error. CPython raises `AttributeError`. mypy, pyright, pyrefly and zuban reject `x.add(Node())`.

A cleaner version using the PEP's own `LinkedList` pattern (`pep_bypass_clean.py`):

```
ty: All checks passed!
mypy: error: Argument 1 to "set_next" of "LinkedList" has incompatible type "LinkedList"; expected "Ordinal"
pyright: error: ... "LinkedList" is not assignable to "Ordinal" (reportArgumentType)
pyrefly: ERROR Argument `LinkedList` is not assignable to parameter `n` with type `Ordinal`
CPython: AttributeError: 'LinkedList' object has no attribute 'ordinal_value'
```

In `pep_bypass_crash.py`, ty rejects the direct assignment `o.next = LinkedList()` (as the PEP demands) but accepts `o.set_next(LinkedList())`. The two are the same operation.

carljm already knows the attribute side is unsound. In the same discuss.python.org thread (post 20, 2025-09-10, paraphrased) he says the only sound and useful reading of `Self`-typed attributes is sugar for the enclosing class name, and that mypy and pyright's `B().x == B` specialisation is unsound. ty still reveals `B` for `B().x` (`attr_only.py`), so ty still uses the unsound attribute specialisation.

**Do the checkers agree with each other?** No, and ty is not always alone:

| Form | ty | mypy | pyright | pyrefly | zuban |
|---|---|---|---|---|---|
| bound call `Leaf().add(Node())` | accept | reject | reject | reject | reject |
| unbound `Leaf.add(Leaf(), Node())` | accept | **accept** | reject | reject | **accept** |

The issue's claim "mypy and pyright both report this call" is true for the main form but not for the unbound form (mypy and zuban accept it).

Control: a plain free function with the same shape, `def add(self: T, c: T) -> T`, called as `add(Leaf(), Node())`, is accepted by all five with `T := Node` (`freefunc.py`). So joint solving is what every checker does in the ordinary TypeVar case. mypy, pyright and others only pin the receiver when binding a method through an instance.

**Is each checker's behaviour a deliberate trade-off?** mypy: yes (Ivan Levkivskyi, post 8). pyright: deliberate practicality trade-off for protocols (Eric Traut, post 9), but it flags the override. ty: deliberate per the maintainer.

**Status: PARTLY.** The LSP point against mypy/pyright is correct. "ty does not have this problem" is incorrect once `Self`-typed attributes are involved.

### C4. "`Node.add` must handle any `Node`"

As a typing fact this is right. The body of `Node.add` is checked with `Self <: Node`, so `c` can only be used as a `Node`. Because the method is not overridden, no code can assume `c` is a `Leaf`. ty's own return-type handling backs this up (`pick.py`):

```python
def pick(self, other: Self) -> Self: return other
r = Leaf().pick(Node())
reveal_type(r)        # ty: Node   (mypy, pyright, pyrefly, zuban: Leaf, after rejecting the arg)
r.leaf_only()         # ty: error[unresolved-attribute]
```

So ty is self-consistent at the call site: if a `Node` is accepted, the result is typed `Node`, and the later bad access is caught. The crash only gets through when the value is written into state ty types as receiver-bound (`list[Self]`, `Self | None`), which is the body-level assumption "my `Self` slots hold my own type".

**Reproduction of `examples/self_param_unsound.py`** (run read-only from its original path):

```
ty: only prints the reveal (bound method Leaf.add(c: Leaf) -> Leaf); no error
mypy: error: Argument 1 to "add" of "Node" has incompatible type "Node"; expected "Leaf"
pyright: error: Argument of type "Node" cannot be assigned to parameter "c" of type "Leaf"
pyrefly: 0 errors under its default no-config preset (section 1 caveat); with config, rejects
CPython: AttributeError: 'Node' object has no attribute 'leaf_only'
```

The crash is attributable to **two things together**: the `Self` parameter and the `Self`-typed mutable attribute. `pick.py` has the `Self` parameter alone, and ty catches the use. The attribute alone is harmless. Is the crash contrived? It needs `Self`-typed stored state, which is the PEP's own `LinkedList` pattern, so it is not very contrived, but it does need that pattern.

**Override versus inherited.** The issue is right that ty behaves differently (`override.py`, `override_super.py`):
- Inherited (no override): accepted.
- Same-signature override `def add(self, c: Self) -> Self`: ty reports "Argument type `Node` does not satisfy upper bound `Leaf` of type variable `Self`".
- Even `return super().add(c)` in the override: rejected.

This is a consequence of the model (the override declares its own `Self <: Leaf`), not a random inconsistency. What is missing is the diagnostic at the override itself. `ty explain rule invalid-method-override` says it checks for LSP violations and is error-level by default, yet ty emits no override error for `Leaf.add(self, c: Self)` (I also ran with `--error invalid-method-override`; still nothing). pyright does flag it (`reportIncompatibleMethodOverride`), mypy, pyrefly and zuban do not.

By the maintainer's own `use_node` argument, that override is the real violation. ty's tracker has it as the open bug #2255 ("override of method that takes `Self` as non-receiver should be a Liskov violation"). carljm's last comment there (2026-08-28) says ty does not currently implement sound Liskov checking of `Self` used on non-receiver parameters, and that the issue stays open to track it. So ty's model relies on a check it has not finished.

**Status: SUPPORTED** as a typing fact, with the caveat above.

## 4. Tool-behaviour matrix

A = accepts (no diagnostic on that call), R = rejects. Outputs in `/tmp/v4656/cases/all_out.txt` and `pyrefly_out.txt`.

| Case | ty 0.0.84 | mypy 2.4.0 | pyright 1.1.414 | pyrefly 1.3.2 | zuban 0.10.0 |
|---|---|---|---|---|---|
| base `Leaf().add(Node())` | A | R | R | R | R |
| keyword `Leaf().add(c=Node())` | A | R | R | R | R |
| unbound `Leaf.add(Leaf(), Node())` | A | **A** | R | R | **A** |
| `list[Self]` `add_all([Node()])` | A | R | R | R | R |
| generic `IntBox().merge(Box[int]())` | A | R | R | R | R |
| override, same signature | R at call | R at call | R at call and at `def` | R at call | R at call |
| `use_node(Leaf())` with `node.add(Node())` | A | A | A | A | A |
| explicit TypeVar `self: T, c: T` | A | R | R | R | R |
| PEP property-setter / `set_next(v: Self)` | A | R | R | R | R |
| `Leaf().pick(Node())` reveal | `Node` | `Leaf` | `Leaf` | `Leaf` | `Leaf` |

Summary: ty is the only checker that accepts the main case; mypy and zuban also accept the unbound call. Everyone, including ty, accepts the maintainer's `use_node` program and crashes.

## 5. Steelman of both sides

**Maintainer's side (ty).**
- The spec text literally defines `Self` as a method-scoped bounded TypeVar. The same signature written as a free function is solved jointly by all five checkers.
- The body of `Node.add` is checked against `Node`. Pinning `Self` to the receiver makes any non-final class with `Self` in a parameter an automatic LSP violation.
- ty's model moves the error to the override site, where the violation actually is (and is tracked as #2255).
- The return type stays right: `Leaf().pick(Leaf())` is `Leaf`, `Leaf().pick(Node())` is `Node`.
- This was decided openly in Sept 2025 (#1172, discuss.python.org post 13).

**User's side (mypy, pyright, pyrefly, zuban).**
- Four of five checkers reject; users reading PEP 673 ("parameters that expect instances of the current class", `Self` bound to the receiver's type) expect `Leaf` here. The generic-classes section uses receiver-binding language.
- The PEP's own attribute example gives `OrdinalLinkedList` and rejects a base instance. It states this is equivalent to a `Self`-typed setter, which ty accepts.
- ty's own output (`bound method Leaf.add(c: Leaf)`) told users the opposite. The maintainers call that a display bug (#4673, #1172).
- ty's model is only sound with a complete override check (#2255 is open) and a non-specialising attribute rule.

**Spec ambiguity or spec violation?** Spec ambiguity. The TypeVar desugaring supports ty; the attribute/generic prose supports the other reading; the conformance suite has no test; the mypy, pyright and Pyre authors describe several incompatible readings as acceptable in the discuss.python.org thread. A design choice, not a spec violation, so "Not planned" is defensible.

## 6. What to reply to the maintainer

Recommendation: **do not argue the call-site behaviour.** It is deliberate, publicly argued a year ago, and consistent with the PEP's desugaring. A reply that says "mypy and pyright disagree" adds nothing.

Only one point is actually new to this thread, and even that is partly known to carljm: ty's `Self` attribute specialisation plus joint-solved `Self` parameters is unsound (section 3, C3). If the user wants to reply, keep it short:

> Thanks for the explanation, that makes sense and I see it matches the discussion on discuss.python.org. One follow-up in case it helps prioritise: with your model, `Self`-typed attributes are still specialised to the receiver (`B().x` is `B`), so a method that stores its `Self` parameter in such an attribute, like the PEP's `LinkedList.next: Self | None`, is accepted and then fails at runtime. Repro is `pep_bypass_clean.py`. If that's already tracked elsewhere, please ignore.

Secondary issues worth filing:
- The reveal/display bug is already filed (#4673, related #1172).
- The missing override diagnostic is already tracked (#2255).
- The attribute-versus-parameter asymmetry: no new issue; add the repro as a comment to #2255 or #4673 only if the user wants, since it duplicates a point carljm already made.
- The one gap I found is documentation: the ty FAQ page I checked (https://docs.astral.sh/ty/reference/typing-faq/) says nothing about `Self` solving. My web search for other ty docs failed, so I did not confirm the rest of the docs. Optional: ask for a short note that ty solves `Self` jointly for parameters, which differs from mypy, pyright and pyrefly.

## 7. C5 and lessons for the typediff pipeline

**Assessment of the original claim.** The `SELF_CONTRADICTION/strong` evidence in `DESIGN.md` section 8 rested on two facts: ty reveals `x.add` as `(c: Leaf)`, and ty rejects `_: Leaf = Node()`. The reveal is a display artefact ty already considered wrong in #1172 (September 2025, open, labelled bug, milestone ty-1.1), where the same example appears with the comment that the reveal "seems to contradict" the accepted call. The assignment check is irrelevant to whether the call should be rejected. So the "self-contradiction" was a known display bug, not a contradiction of behaviour.

Other defects in the worked example:
- `DESIGN.md` section 8 says a quick tracker search "found no obvious duplicate". #1172 (open, same example), #2255 (open) and discuss.python.org #86338 all cover this.
- The `RUNTIME/strong` evidence is the downstream `x.children[0].leaf_only()` crash. That crash needs the `Self`-typed attribute and is caused by attribute specialisation, not only by the call. The reducer output in section 8 drops `children` and `leaf_only`, so the reduced repro no longer crashes at all.
- The CONSENSUS/weak evidence (pyright sides with mypy) cannot distinguish "ty is wrong" from "mypy and pyright pin the receiver".

**Classification it should have received:** NOT_BUG, `DESIGN_DIVERGENCE` or `SPEC_AMBIGUITY`, and queued for human review rather than CONFIRMED.

**Evidence that would have prevented the report:**
- A desugar oracle: rewrite `Self` to a method-scoped bounded TypeVar and re-run (`explicit_typevar.py`). ty gives the same answer as its `Self` version, so ty is self-consistent and spec-literal.
- A free-function probe (`freefunc.py`): all checkers solve to `Node`.
- An LSP probe (`lsp_use_node_runtime.py`): all checkers accept and crash, so mypy and pyright cannot serve as an oracle for a ty false negative.
- A tracker/forum search on body text (the #1172 body contains the exact example).
- A conformance check (nothing covers it, so no SPEC evidence is available).

**Concrete changes (recommendations only, nothing implemented):**
1. **New KB entry `TY-SELF-UPPER-BOUND`** (kind: design divergence, hint plus auto-dismiss only if the probes below confirm). Matcher:
   - the source has a `FunctionDef` in class `C` with `Self` inside a non-receiver parameter annotation;
   - the call receiver's static type is a strict subclass of `C` and the method is not overridden between them;
   - the argument's type is `C` or another supertype of the receiver;
   - the other tool's diagnostic is an `arg-type`/`reportArgumentType`-style rejection naming the subclass.

   Dismissal text should cite ty#4656, ty#1172, ty#2255, and discuss.python.org #86338 post 13. Set `runtime_override=False` for the call-site discrepancy, because both models are unsound (section 3, C3). A crash that goes through a `Self`-typed attribute should instead be routed to review with a note.
2. **Demote `SELF_CONTRADICTION` to weak** whenever the contradictory side is a `reveal_type` of a bound method or callable that contains `Self` or a TypeVar in a parameter. Require call-versus-call contradictions (two calls to the same signature) for "strong".
3. **Add a spec-desugar oracle** that rewrites `Self` to a bounded TypeVar, re-checks with the same tool, and dismisses as consistent-with-spec if the answer does not change.
4. **Add an LSP probe** that synthesises `def probe(n: Base): n.m(Base())` plus `probe(Sub())` and marks the other tool's reading unsound when it accepts both. That disqualifies the other tool as an oracle for this class of discrepancy.
5. **Add a conformance step** that checks whether `python/typing/conformance/tests/<area>_*.py` contains the pattern. If not, cap the finding at SPEC_AMBIGUITY and do not use SPEC evidence.
6. **Make the duplicate check real**: query the GitHub search API for body text (not only titles), including `Not planned` closures and discuss.python.org, and fail closed (review queue) when a near-match exists. Add a "prior maintainer stance" lookup and feed it to the SKEPTIC prompt.
7. **Attribute runtime evidence to a cause**: automatically re-run with the suspected mechanism removed (as `pick.py` does by dropping the attribute) and attach the result. If the crash disappears in the control, tag the RUNTIME evidence as "depends on X".
8. **Pyrefly config**: if pyrefly is ever added as a tie-breaker, always pass a config file; its no-config preset silently reports 0 errors.

## 8. Files, commands, and what I could not verify

All under `/tmp/v4656/`:
- `venv/` with the five tools; `install.txt` (pinned/observed versions).
- `cases/*.py` test programs: `base`, `kw`, `unbound`, `listself`, `generic`, `override`, `override_super`, `usenode`, `explicit_typevar`, `freefunc`, `attr`, `attr_only`, `pick`, `lsp_use_node_runtime`, `pep_difference`, `pep_linkedlist_attr`, `pep_setter_method`, `pep_bypass_crash`, `pep_bypass_clean`.
- `cases/run_all.sh`, `all_out.txt`, `pyrefly_out.txt`, `runtime_out.txt`, `pep_out.txt`, `ctrl_out.txt`, `bypass_out.txt`, `bypass_clean_out.txt`.
- `conf/` conformance tests and ty's result files from `python/typing` `main`.
- `dp86338.txt` (discuss.python.org thread text), `ty2255_comments.txt` (issue #2255 comments).

Sources: ty issues #4656, #4673, #4387, #1172, #2255 (GitHub REST API: `api.github.com/repos/astral-sh/ty/issues/<n>` and `/comments`), https://peps.python.org/pep-0673/, https://typing.python.org/en/latest/spec/generics.html#self, https://discuss.python.org/t/unsoundness-of-contravariant-self-type/86338, https://github.com/python/typing/discussions/1761, https://docs.astral.sh/ty/reference/typing-faq/. Quotes are kept under 25 words; other source text is paraphrased.

Not verified:
- Whether `gh` would show different data than the REST API (it is not installed).
- Any part of the ty docs beyond the typing FAQ (my web search tool errored twice).
- Pyrefly and zuban conformance results.
- The mypy docs' own wording (seen only via a StackOverflow quote).
- Comments on #4673 (the API returned an empty list).
- The ty dates in the API output are later than my own knowledge; I report them as returned.
