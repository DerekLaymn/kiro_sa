# Claim C final verification: mypy PEP 695 variance inference and writable `Callable[[T], None]` attributes

Investigation date: this session. Read-only with respect to /home/micropp/Documents/kiro_sa (only this report was written there). All work in `/tmp/mypyC/`.

## 1. Summary answer

**Verdict: FILE AS BUG. Confidence about 75%.** (Not "question": there is a concrete one-condition fix, mypy's own docs and a maintainer comment state the principle being violated, and the full mypy check suite passes with the fix.)

**Single strongest reason:** mypy already has a rule "a writable attribute makes the type parameter invariant" (`infer_variance`, `if settable: co = False`), and its docs say "a public, mutable attribute" makes a class invariant. The rule is only applied in the covariant direction. Under the contravariant direction it is missing, so `self.cb = cb` with `cb: Callable[[T], None]` is inferred contravariant, which is exactly as unsound as the covariant case the rule was written for. mypy's own protocol check rejects the same shape (`Contravariant type variable ... used in protocol where invariant one is expected`).

**Strongest objection and whether it stands:** "The typing spec doesn't say anything about settable members, and contravariant soundness is best-effort in Python." This **partly stands**. The spec's variance-inference algorithm says "normal assignability rules" and is silent on mutable attributes. So the report must not claim a spec violation. It does not rescue the current behaviour, because mypy itself applies the mutable-attribute rule in the covariant direction, and the spec's protocol section does say a mutable attribute makes a class invariant. The maintainer who wrote the relevant comment (ilevkivskyi, #18334) said in so many words that a settable attribute makes `Foo[T]` invariant.

**Proposed fix result:** two small changes in `mypy/subtypes.py` (4 added lines). The plain-class repro and the original int/float repro are rejected. The full `testcheck` + `testtypes` + `testsubtypes` run passes: `8479 passed, 29 skipped, 7 xfailed`. No existing test changes. Only mypy_primer can show real-world fallout, which I cannot run.

**Not a duplicate:** no open or closed mypy issue/PR found covering this case (searched, details in section 5).

Report path: `/home/micropp/Documents/kiro_sa/.agents/tasks/mypy-variance-C-final.md`

## 2. Environment

| Tool | Version | Notes |
|---|---|---|
| CPython | 3.13.15 | all venvs; target `--python-version 3.13` |
| mypy | 2.4.0 | `/tmp/mypyC/v240` |
| mypy | 2.4.1 (newest on PyPI at test time) | `/tmp/mypyC/vnew` |
| mypy master | `2.5.0+dev.934e703a861cfa3b0d29f1e87d9cf7d016001618` | clone `/tmp/mypyC/mypy-master`, editable install, not compiled |
| ty | 0.0.84 and 0.0.95 (newest) | identical results everywhere |
| pyright | 1.1.414 | |
| zuban | 0.10.2 | |

Flags: `mypy --python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental`. Test files in `/tmp/mypyC/cases/`, generator `/tmp/mypyC/gen.py`, matrix script `/tmp/mypyC/matrix.py`, raw log `/tmp/mypyC/run.log`.

Note: the `uv pip install -p NAME` form failed for `v240` (it parsed the name as a Python version); I reinstalled with `--python v240/bin/python`. The 2.4.0 results above come from the corrected install.

## 3. Reproduction without int/float promotion, and variants

Base classes used in every file:
```python
class Animal: ...
class Dog(Animal):
    def bark(self) -> None: print("woof")
class Cat(Animal): ...
```
Each file has two probes (the oracle; mypy has no reveal-able variance, so I use assignment probes):
- **A** (`Handler[Animal]` returned as `Handler[Dog]`): accepted means the checker treats T as contravariant (or bivariant).
- **B** (`Handler[Dog]` returned as `Handler[Animal]`): accepted means covariant.

Matrix. Each cell is `A/B`, `ok` = accepted, `rej` = rejected. "mypy" column is identical for 2.4.0, 2.4.1 and master (unpatched). "ty" is identical for 0.0.84 and 0.0.95.

| Variant | mypy (2.4.0 / 2.4.1 / master) | ty | pyright | zuban | CPython at runtime |
|---|---|---|---|---|---|
| a. `self.cb = cb` in `__init__`, lambda writer | **ok**/rej | rej/rej | rej/rej | **ok**/rej | AttributeError |
| b. same, plain `def` writer | **ok**/rej | rej/rej | rej/rej | **ok**/rej | AttributeError |
| c. class-body annotation `cb: Callable[[T], None]` | **ok**/rej | rej/rej | rej/rej | rej/ok (odd, see below) | AttributeError |
| d. `@dataclass` field | **ok**/rej | rej/rej | rej/rej | **ok**/rej | AttributeError |
| e. property with setter | **ok**/rej | rej/rej | rej/rej | **ok**/rej | AttributeError |
| f. CONTROL old-style `Generic[T]`, invariant TypeVar | rej/rej | rej/rej | rej/rej | rej/rej | n/a |
| g. CONTROL read-only `@property` | ok/rej | ok/rej | ok/rej | ok/rej | ok (legit contravariant) |
| h. CONTROL `self.cb: Final = cb` | ok/rej | ok/rej | ok/rej | ok/rej | ok (legit contravariant) |
| i. CONTROL `_cb` underscore name | ok/rej | ok/rej | ok/rej | ok/rej | n/a (intentional exemption) |
| j. CONTROL method `def cb(self, v: T)` | ok/rej | ok/rej | ok/rej | ok/rej | n/a |
| k. CONTROL writable `list[T]` attribute | rej/rej | rej/rej | rej/rej | rej/rej | n/a |
| l. CONTROL writable plain `T` attribute | rej/rej | rej/rej | rej/rej | rej/rej | n/a |

(Files j, k, l have a constructor-signature mismatch in my generic runner, which adds unrelated `call-arg`/`arg-type` errors. The A/B cells were read by line number, so they are unaffected.)

What reproduces: variants a, b, c, d, e on all three mypy versions. The int/float promotion is not needed. The `_cb`, `Final` and read-only property controls behave as designed. Writable `T` and `list[T]` attributes are already invariant in mypy, which is the evidence that the settable rule works for everything except the contravariant case.

Zuban mirrors mypy for a, b, d, e. Zuban's variant c output (`Invalid self argument "Handler[T]" to attribute function "cb"` plus rej/ok) is a different bug in zuban's treatment of class-body Callable attributes; I did not investigate it and it should not be cited as support.

Runtime output of variant a (same pattern for all):
```
RUNTIME: AttributeError 'Cat' object has no attribute 'bark'
```
Original int/float repro (mypy 2.4.1: "Success: no issues found"):
```
AttributeError: 'float' object has no attribute 'bit_length'
```

## 4. mypy's own inconsistency (exact messages)

File `/tmp/mypyC/cases/proto.py`, mypy master:
```python
T_contra = TypeVar("T_contra", contravariant=True)
class P(Protocol[T_contra]):
    cb: Callable[[T_contra], None]
```
```
cases/proto.py:5: error: Contravariant type variable "T_contra" used in protocol where invariant one is expected  [misc]
```
Structural matching treats the writable Callable attribute as invariant (both directions rejected):
```
cases/proto.py:24: error: Argument 1 to "g" has incompatible type "Impl"; expected "PRO[Dog]"  [arg-type]
    Expected: def (Dog, /) -> None
    Got:      def (Animal, /) -> None
cases/proto.py:26: error: Incompatible types in assignment (expression has type "ImplDog", variable has type "PRO[Animal]")  [assignment]
    Expected: def (Animal, /) -> None
    Got:      def (Dog, /) -> None
```
This is `is_protocol_implementation` in `mypy/subtypes.py` (about lines 1352-1366 on master): "`if IS_SETTABLE in superflags: # Check opposite direction for settable attributes.`". ty and pyright agree with the protocol-side behaviour (ty: `Type variable T_contra in protocol P should be invariant, but is contravariant`; pyright: `"cb" is invariant because it is mutable`).

So mypy knows that a writable `Callable[[T], None]` attribute is invariant when it is checking a protocol, and when it is checking a class under old-style variance (variant f). Only PEP 695 inference misses it.

## 5. Code reading, history, and issue/PR/discussion search

### 5.1 The code (`mypy/subtypes.py`, master 934e703a8)

`infer_variance` (line ~2439-2513). Core loop:
```python
flags = get_member_flags(member, self_type)
settable = IS_SETTABLE in flags
node = info[member].node
if isinstance(node, Var):
    ...
    if has_underscore_prefix(member):
        # Special case to avoid false positives (and to pass conformance tests)
        settable = False
# TODO: handle settable properties with setter type different from getter.
typ = find_member(member, self_type, self_type)
if typ:
    typ = erase_return_self_types(typ, self_type)
    typ2 = expand_type(typ, {tvar.id: object_type})
    if not is_subtype(typ, typ2):
        co = False
    if not is_subtype(typ2, typ):
        contra = False
        if settable:
            co = False
```
`typ2` is the member with T replaced by `object`. `not is_subtype(typ, typ2)` means T is used contravariantly; `not is_subtype(typ2, typ)` means T is used covariantly. The settable clause lives only inside the second branch, so a settable covariant member becomes invariant but a settable contravariant member stays contravariant. That is the whole bug.

`get_member_flags` (line ~1570-1625): methods return `set()`, so they are never settable. Every ordinary `Var` that is not `Final` and not a property gets `{IS_VAR, IS_SETTABLE}`, and there is no special case for Callable-typed Vars. So the hypothesis "mypy treats Callable attributes like methods" is **rebutted for ordinary attributes**: a Callable attribute is flagged settable like any other. The proof by experiment: adding the symmetric clause fixes variants a, b, c, e, which it could not do if the attribute were handled as a method.

**Exception: dataclasses.** `mypy/plugins/dataclasses.py` `_propertize_callables` (line ~790-808; added in #10292, 2021-04-23, "Extend the dataclass plugin to deal with callable properties") turns every Callable-typed dataclass field into a `Var` with `is_property = True`, `is_settable_property = True`, to avoid method self-binding. `get_member_flags` has `if v.is_property: return {IS_VAR}` which drops `IS_SETTABLE`, so a plain symmetric fix does not cover variant d. A second one-line change is needed (below). That is a real "Callable attrs are treated specially" effect, but it is dataclass-specific, an implementation artefact, and unrelated to variance intent.

### 5.2 `git log -S` / blame

- The settable lines (`settable = IS_SETTABLE in flags`, `if settable: co = False`) come from `5fb8d6262` "[PEP 695] Partial support for new type parameter syntax in Python 3.12 (#17233)", Jukka Lehtosalo, 2024-05-17, the original PEP 695 implementation.
- The underscore carve-out (`has_underscore_prefix`) is `fce14a028`, PR #17782, 2024-09-18, "Allow covariance with attribute that has "_" name prefix", written to pass conformance test `ShouldBeCovariant5`.
- The `TODO: handle settable properties with setter type different from getter` is `1eb9d4ce3` (Ivan Levkivskyi, 2025-01-25, #18510).
- Searching the PEP 695 test file `test-data/unit/check-python312.test` for `Callable`: no inference test uses a Callable-typed attribute. Searching `git show 5fb8d6262` for the contravariant direction: no sign that a settable contravariant member was considered. I found no evidence of a deliberate decision to exempt it. (This is absence of evidence; the author could not be asked.)

### 5.3 Items read (full body and comments)

| Item | Date | What it says | Defends current behaviour? |
|---|---|---|---|
| mypy #17709 https://github.com/python/mypy/issues/17709 | opened and closed 2024-08-25, not planned | Reporter thought an empty PEP 695 class was bivariant. erictraut replied the reporter's test was wrong (the variable was narrowed on assignment); reporter agreed and apologised. | **No.** Closed because of user error in the repro (narrowing), nothing about design. Does not apply here; my probes use function return statements, not reassigned local variables. |
| mypy #20501 https://github.com/python/mypy/issues/20501 | opened 2025-12-31, open | Reporter wants `_v: T` to be invariant. sterliakov: underscore means internal by convention and matches other checkers. bzoracler shows an unsound `_v` example and notes the underscore rule is unreliable. | Defends the **underscore exemption only**. Says nothing about public Callable attributes. Related but not a duplicate. |
| mypy #17623 https://github.com/python/mypy/issues/17623 | 2024-08-02 to 2026-07-07 | Frozen dataclass / NamedTuple covariance broken by `__replace__`; long discussion. | Not relevant to settable Callable attributes. Shows maintainers do special-case synthesised members. |
| mypy #18334 https://github.com/python/mypy/issues/18334 | 2024-12-24, closed not planned 2025-10-15 | `instance: Self` made `Foo[T]` invariant. **ilevkivskyi:** `instance: Foo[T]` "is invariant: `instance` is a settable attribute. So this is actually true positive." | **Supports the claim's principle**: a maintainer states settable attributes drive invariance. |
| mypy #18147 https://github.com/python/mypy/issues/18147 | 2024-11-12, open | Variance of two type vars with an untyped `self.__a = value` assignment. | Unrelated (inference of untyped attribute). |
| mypy #20366 https://github.com/python/mypy/issues/20366 | 2025-12-05, closed | Docs wrongly say user generics are invariant by default; Jelle: under PEP 695 unused T is covariant. | Unrelated; confirms docs are being corrected. |
| mypy #20997 https://github.com/python/mypy/issues/20997 | 2026-03-09, open | Polymorphic `Self | complex` return changes inference. Points to PR #19466. | Unrelated to attributes. |
| mypy PR #17782 | merged 2024-09-18 | Underscore carve-out. | Defends underscore only. |
| mypy PR #18510 | merged 2025-01-25 | Setter types different from getter. Description: "Two things that are not implemented are multiple inheritance, and new generic syntax (inferred variance). In these cases setter types are simply ignored." | **Supports** that inferred-variance handling of settable members is known to be incomplete. |
| mypy PR #19466 | open since 2025-07-16 | Polymorphic method variance fix. No settable/Callable discussion. | Unrelated. |
| mypy PR #21564 | closed unmerged 2026-05-29 | LLM-generated draft ignoring plugin-synthesised members in `infer_variance`. | Unrelated. It shows the CONTRIBUTING.md stance on LLM contributions (see section 8). |
| python/typing #2281 https://github.com/python/typing/issues/2281 | closed 2026-05-10 | Divergence between checkers on variance of methods with bound self type. | Unrelated to attributes, but confirms variance inference is an open area with checker divergence. |
| discuss.python.org "Should variance inference ignore underscore-prefixed attributes?" https://discuss.python.org/t/102978 | 2025-08-20 | Carl Meyer: the underscore exception "is only sound if" outside access is a type error. Sam Goldman: "soundness with respect to contravariance is in practice best effort in Python" and he would be happy if there were consensus to be strict about contravariance of attributes. | Partly. This is the main source of the "best effort" objection. It was a personal opinion in a thread about underscores; no decision was taken. |
| discuss.python.org "Unsoundness of contravariant `Self` type" https://discuss.python.org/t/86338 | 2025-03/09 | About `Self` in method parameters; ilevkivskyi says treating Self safely would be a pain and he is "not interested" in reopening. | Covers `Self` in **method** parameters only, not plain type parameters on writable attributes. Not a precedent for this case. |

Searches run (GitHub search API, repo python/mypy, issues and PRs, open and closed, title/body/comments): `infer_variance`, `infer_variance settable`, `PEP 695 variance unsound`, `variance inference callable attribute`, `contravariant attribute mutable PEP 695`, `inferred contravariant settable attribute`, `type parameter variance mutable attribute callable`, `Callable attribute contravariant`, `variance writable attribute Callable`, `contravariant mutable attribute not invariant`, `variance inference mutable contravariant`. No hit matched this case. Web search of discuss.python.org and python/typing for the same ideas found only the two threads above. The GitHub search API is not exhaustive for body text, so a final manual search just before filing is still advisable (checklist, section 9).

### 5.4 Spec and docs

| Source | Exact wording (short) | What it requires / does not |
|---|---|---|
| Typing spec, variance inference https://typing.python.org/en/latest/spec/generics.html#variance-inference | "Type parameters are inferred to be invariant, covariant, or contravariant depending on how they are used." Step 3: lower assignable to upper "using normal assignability rules". | Requires the inferred variance to follow from how T is used and to use normal assignability. **Does not** mention mutable or settable members, nor Callable. Silent on this case. |
| PEP 695, variance inference https://peps.python.org/pep-0695/#variance-inference | Same algorithm: "Python type checkers already include the ability to determine the variance of type parameters for the purpose of validating variance within a generic protocol class." | Ties inference to the protocol capability. Silent on mutable attributes. |
| Typing spec, protocols https://typing.python.org/en/latest/spec/protocol.html | Example comment: `attr: T  # this class is invariant, since it has a mutable attribute`. | Requires (for protocols) that a mutable attribute makes the protocol invariant in T. Does not say the same for ordinary classes. |
| python/typing conformance `generics_variance_inference.py` | Underscore `_x` attribute case (`ShouldBeCovariant5`), settable property `ShouldBeInvariant1`, frozen dataclass, methods. | Nothing with a Callable-typed attribute, and no contravariant settable case. Silent. |
| mypy docs `docs/source/generics.rst` (master) | "Without an underscore prefix, the class would be invariant, as the attribute would be understood as a public, mutable attribute". And: declaring the attribute `Final` makes it covariant. | The documented intention matches the claim. The text talks about covariance, but its reasoning (public mutable attribute implies invariant) is direction-independent. |

Honest statement: **the spec is silent on this exact case.** The report must not say "violates the spec". It can say "mypy documents the rule that a public, mutable attribute makes the class invariant, applies it in one direction, and a mutable attribute is invariant in the spec's own protocol example".

## 6. Adversarial section: every objection I could think of

| # | Objection | Evidence for | Evidence against | Verdict |
|---|---|---|---|---|
| 1 | Spec is silent, so mypy may do anything | Spec text has no settable/Callable rule (verified). | mypy chose a settable rule for the covariant case; spec protocol example and mypy docs state the mutable-attribute rule; ty and pyright infer invariant. | **Partly stands.** Do not claim spec violation. Claim inconsistency with mypy's own rule. |
| 2 | mypy treats Callable attributes like methods | dataclass plugin does turn Callable fields into properties (#10292). `find_member` binds callables in some access paths. | `get_member_flags` has no Callable special-case for ordinary Vars; flag is `{IS_VAR, IS_SETTABLE}`. Symmetric clause fixes a/b/c/e, which would not work if they were treated as methods. Methods (variant j) are never settable. | **Rebutted** for ordinary attributes. **Partly** true for dataclasses, where it's a plugin artefact. |
| 3 | Underscore names are exempt on purpose | #17782, #20501 comments. | Repro uses public `cb`. Variant i confirms underscore stays exempt, and the fix keeps that exemption (`settable = False` runs before the new clause). | **Rebutted.** |
| 4 | It relies on int/float promotion | Original repro does. | Animal/Dog/Cat variants a-e reproduce with no promotion. | **Rebutted.** |
| 5 | Contrived lambda | Original uses a lambda. | Variant b uses a normal `def`; variants c, d, e use realistic shapes (declared attribute, dataclass field, property setter). The pattern (store a callback, let another function replace it) is common in UI/event code. | **Rebutted** (mostly; "how common is it in real code" is unmeasured). |
| 6 | Variance inference is heuristic, best effort | Sam Goldman's comment (not a mypy maintainer); ilevkivskyi: low priority for self-type holes (#18334, discuss 86338). | Those discussions concern `Self` in method signatures. Here it is a plain type parameter in a writable attribute, the same shape mypy already handles for `T` and `list[T]`; fix is one condition. | **Partly stands.** Maintainers could still call it low priority. Frame as a small inconsistency, not a soundness crusade. |
| 7 | Duplicate | Several related issues (#20501, #18334, #18510). | None describes a settable contravariant attribute; searches found no match. | **Rebutted** (checked as far as the search API allows). |
| 8 | Already fixed on master | Checked. | Master `934e703a8` still accepts variants a-e. | **Rebutted.** |
| 9 | Use an explicit old-style TypeVar | Variant f is rejected correctly with invariant TypeVar. | With `TypeVar(contravariant=True)` on a non-protocol class, mypy, pyright and ty all accept it (tested, `/tmp/mypyC/zz_explicit.py`); so explicit declaration is a user promise, whereas PEP 695 inference is advertised as inferring a safe variance. In the protocol case mypy itself rejects the explicit contravariant TypeVar. | **Rebutted** as a defence; valid as a **workaround** to mention. |
| 10 | Behaviour change would break users (false positives) | Existing code with `self.cb = cb` and `Handler[Animal]` passed as `Handler[Dog]` would start failing. | It is the same trade-off as for `T` attributes; workarounds exist (`_cb` + property, `Final`, read-only property). I cannot measure impact without mypy_primer. | **Stands as a risk for the fix**, not for the bug. Say so in the issue. |
| 11 | "Tool disagreement is not evidence" (the ty#4656 lesson) | ty and pyright disagree with mypy. | I did not rely on that. The evidence is mypy's own code, docs, protocol check and runtime crash from type-clean code. | **Rebutted.** |
| 12 | The unsoundness needs a "bad" caller | `use()` is passed a narrowed view and writes. | That is the textbook reason mutable containers are invariant (mypy docs `list[Shape]` example). | **Rebutted.** |

**Overall: FILE AS BUG**, confidence ~75%. The remaining 25% is maintainers closing it as "known best-effort / low priority" or wanting the spec clarified first; either outcome costs the user little if the tone stays modest.

## 7. Proposed fix, tested locally (suggestion only, not pushed)

Clone `/tmp/mypyC/mypy-master` (unmodified remote state; local working-tree edits only). Diff saved at `/tmp/mypyC/fix_full.diff`:

```diff
--- a/mypy/subtypes.py
+++ b/mypy/subtypes.py
@@ def get_member_flags(...):
     if isinstance(v, Var):
         if v.is_property:
+            if v.is_settable_property:
+                return {IS_VAR, IS_SETTABLE}
             return {IS_VAR}
@@ def infer_variance(...):
                 if not is_subtype(typ, typ2):
                     co = False
+                    if settable:
+                        contra = False
                 if not is_subtype(typ2, typ):
```
- Part 1 (3 lines in `infer_variance`) fixes variants a, b, c, e. The settable property case works because the getter returns the Callable, which is contravariant, and the property is flagged settable.
- Part 2 (the `get_member_flags` change) is only needed for dataclass fields (variant d), because the dataclass plugin marks Callable fields as properties. I'd offer it as optional in the issue, since it widens `IS_SETTABLE` for plugin-made properties and may interact with protocol matching.
- Results with both parts: matrix rows a, b, c, d, e become `rej/rej`; controls f-l unchanged; original int/float repro now reports `Argument 1 to "use" has incompatible type "Handler[float]"; expected "Handler[int]"  [arg-type]`.
- Tests: `pytest -n 6 mypy/test/testcheck.py mypy/test/testtypes.py mypy/test/testsubtypes.py` gave `8479 passed, 29 skipped, 7 xfailed`. A focused subset (`-k "ariance or python312 or python313 or Protocol or protocol or dataclass or Dataclass"`) gave `646 passed, 1 skipped`. No test needed changes.
- Not done: mypy_primer (needs the repo's CI), self-check on mypy itself (`python -m mypy --config-file mypy_self_check.ini -p mypy`), a new regression test in `test-data/unit/check-python312.test`. A natural test: `testPEP695InferVarianceSettableCallableAttribute` modelled on `testPEP695InferVarianceSimpleFromAttribute`.
- Caveat: I tested on an uncompiled master install.

## 8. Final GitHub issue text (python/mypy, "Bug Report" template)

Template headings verified from `.github/ISSUE_TEMPLATE/bug.md`: Bug Report / To Reproduce / Expected Behavior / Actual Behavior / Your Environment. Label `bug` is applied automatically by the template.

**mypy-play link: I could not create one.** Playground links need a GitHub gist, and creating a gist would be publishing something under the user's account, which the brief forbids. The user can paste the repro into https://mypy-play.net/, choose Python 3.13, click "Gist", and paste the URL under "To Reproduce". Without it the issue still stands since the repro is self-contained.

CONTRIBUTING.md note: mypy discourages LLM-generated contributions from new contributors (PR #21564 was a draft that cited this). The user should write the issue in their own words, using the text below as notes, and say how they found it (fuzzing/differential testing) rather than hiding it. Keep the issue short.

---

**Title:** `PEP 695 variance inference treats a writable Callable[[T], None] attribute as contravariant`

**Bug Report**

For a class using PEP 695 syntax, `infer_variance` makes `T` contravariant when `T` appears only as the parameter of a `Callable` stored in a public, writable attribute. This looks inconsistent with how mypy treats other writable attributes: a writable `T` or `list[T]` attribute makes the class invariant, and mypy's docs say a public mutable attribute makes the class invariant. As a result, mypy accepts code that crashes at runtime with an `AttributeError`.

I could not find an existing issue for this (closest: #18334 and #20501, which are about `Self` and underscore names). I am not claiming a spec violation: as far as I can tell the typing spec doesn't say anything about mutable attributes for inferred variance, only for protocols.

**To Reproduce**

```python
from collections.abc import Callable

class Animal: ...
class Dog(Animal):
    def bark(self) -> None: print("woof")
class Cat(Animal): ...

class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb

def use(h: Handler[Dog]) -> None:
    h.cb = lambda d: d.bark()      # fine for a Handler[Dog]

ha = Handler[Animal](lambda a: print(a))
use(ha)                            # mypy: no error (Handler[Animal] accepted as Handler[Dog])
ha.cb(Cat())                       # AttributeError: 'Cat' object has no attribute 'bark'
```

The same happens with a plain `def` instead of a lambda, with a class-body annotation `cb: Callable[[T], None]`, with a `@dataclass` field, and with a property that has a setter. The original reproducer with `int`/`float` (no promotion needed in the version above):

```python
class Handler[T]:
    def __init__(self, cb: Callable[[T], None]) -> None:
        self.cb = cb
def use(h: Handler[int]) -> None:
    h.cb = lambda v: print(v.bit_length())
hf = Handler[float](lambda x: print(x.is_integer()))
use(hf)
hf.cb(1.5)   # AttributeError: 'float' object has no attribute 'bit_length'
```

**Expected Behavior**

`Handler[Animal]` is not accepted where `Handler[Dog]` is expected, i.e. `Handler` is inferred invariant in `T`, as it is for:
- the same class with an old-style invariant `TypeVar` and `Generic[T]`;
- a writable `T` attribute or `list[T]` attribute in a PEP 695 class;
- a protocol with the same member (`class P(Protocol[T_contra]): cb: Callable[[T_contra], None]` is already rejected by mypy with `Contravariant type variable "T_contra" used in protocol where invariant one is expected`).

Pyright and ty infer invariance here and report an error on the `use(ha)` line.

**Actual Behavior**

mypy 2.4.0, 2.4.1 and current master (`934e703a8`) report no errors with `--python-version 3.13 --check-untyped-defs`. Swapping the direction (`Handler[Dog]` where `Handler[Animal]` is expected) is correctly rejected, so `Handler` is inferred contravariant. Behaviour table, rows are variants of the class, `ok` = assignment accepted:

| variant | `Handler[Animal]` to `Handler[Dog]` (mypy) | pyright / ty |
|---|---|---|
| `self.cb = cb` in `__init__` | ok (unsound) | error |
| plain `def` instead of lambda | ok (unsound) | error |
| class-body `cb: Callable[[T], None]` | ok (unsound) | error |
| `@dataclass` field | ok (unsound) | error |
| property with setter | ok (unsound) | error |
| `Final` attribute / read-only property | ok (correct) | ok |
| `_cb` (underscore) | ok (documented exemption) | ok |
| old-style `Generic[T]`, invariant TypeVar | error | error |
| writable `T` or `list[T]` attribute | error | error |

**Possible cause (suggestion only)**

In `infer_variance` (`mypy/subtypes.py`), the "settable" rule is applied only to the covariant direction:

```python
if not is_subtype(typ, typ2):
    co = False
if not is_subtype(typ2, typ):
    contra = False
    if settable:
        co = False
```

A settable member with `T` in a contravariant position leaves `contra = True`. A symmetric clause (`if not is_subtype(typ, typ2): co = False; if settable: contra = False`) makes the examples above invariant. With that change, `pytest mypy/test/testcheck.py mypy/test/testtypes.py mypy/test/testsubtypes.py` passes locally on master (8479 passed), but I have not run mypy_primer, so I don't know how much existing code would be affected. Dataclass fields need one more change, because the dataclass plugin turns Callable fields into properties (`_propertize_callables`), and `get_member_flags` returns `{IS_VAR}` without `IS_SETTABLE` for those. Happy to open a PR if this direction is acceptable.

**Things I checked that might make this intended**
- The underscore carve-out (#17782, #20501) is deliberate; my examples use a public name, and the `_cb` variant is still accepted.
- The typing spec's variance-inference section does not mention mutable members, so the spec does not settle this either way.
- Callable attributes are not handled like methods in `get_member_flags` (they get `IS_SETTABLE`), except for dataclass fields.
- A contravariant `TypeVar` declared explicitly on a non-protocol class is accepted by mypy, pyright and ty. That is a user promise, whereas inferred variance is supposed to be safe.
- Maintainers have said elsewhere (#18334 and discuss.python.org threads) that some contravariance holes, mainly around `Self`, are known trade-offs. I don't think this falls in that group since `T` is an ordinary type parameter, but I may be wrong.
- Making these classes invariant could break code that relies on the current behaviour; workarounds are `Final`, a read-only property, or a `_`-prefixed name.

**Your Environment**

- Mypy version used: 2.4.0, 2.4.1, and master 2.5.0+dev.934e703a861cfa3b0d29f1e87d9cf7d016001618
- Mypy command-line flags: `--python-version 3.13 --check-untyped-defs --show-error-codes --no-incremental`
- Mypy configuration options from `mypy.ini` (and other config files): none
- Python version used: 3.13.15 (CPython)

Other checkers (for context): pyright 1.1.414 and ty 0.0.84/0.0.95 report an error on `use(ha)`. zuban 0.10.2 behaves like mypy.

---

## 9. What to write in the GitHub form (checklist)

Go to https://github.com/python/mypy/issues/new/choose and select **Bug Report**.

1. **Title:** the title above. It names the construct and the checker behaviour and avoids "unsound" claims in the headline.
2. **Labels:** the template adds `bug`. Non-members cannot choose others; do not ask for more. Maintainers will add `topic-pep-695` or similar.
3. **Body:** paste the sections "Bug Report" to "Your Environment" above, in this order. Rewrite sentences into your own words (CONTRIBUTING discourages pasted LLM text from new contributors), and keep the repro code exactly as is.
4. **Playground:** open https://mypy-play.net/, Python 3.13, paste the Animal/Dog/Cat repro, Gist button, paste the URL under "To Reproduce". Not required, but the template prefers it.
5. **Paste mypy output** for the first repro: run `mypy --python-version 3.13 --check-untyped-defs --show-error-codes file.py` and show "Success: no issues found in 1 source file", and show the CPython traceback.
6. **Do not** claim: "violates the typing spec", "mypy is wrong and pyright is right", "this is a security issue", or "other checkers agree so it's a bug". Say what is inconsistent inside mypy and what the runtime does.
7. **Do not** mention the earlier ty report unless asked.
8. **Do not** open a PR before a maintainer replies. A PR from a new contributor needs a test in `test-data/unit/check-python312.test` and a mypy_primer run.
9. **Be ready to answer:** "what breaks in real code?" The honest answer is "I haven't measured; mypy_primer would show it".

Pre-submit checklist:
- [ ] Re-run the repro on current master and on the latest release the same day (`pip install -U mypy`; and `pip install git+https://github.com/python/mypy.git`).
- [ ] Search python/mypy issues once more for: `contravariant Callable attribute`, `infer_variance settable`, `PEP 695 variance writable`, open and closed.
- [ ] Repro is self-contained, passes `python repro.py` to the AttributeError as shown.
- [ ] No spec-violation claim; "things I checked" paragraph kept.
- [ ] Wording modest; no sweeping soundness claims; offer to help with a PR.
- [ ] Mention your AI/tooling use honestly if you rely on it for the fix idea (CONTRIBUTING.md asks for disclosure).

## 10. Files

- `/tmp/mypyC/cases/*.py` variant files, `/tmp/mypyC/gen.py` generator, `/tmp/mypyC/matrix.py` runner
- `/tmp/mypyC/run.log` raw output, `/tmp/mypyC/matrix.txt` unpatched matrix, `/tmp/mypyC/matrix_fixed2.txt` matrix with the patch applied to master (only the "mypyMaster" column changes)
- `/tmp/mypyC/proto.out` protocol check output
- `/tmp/mypyC/fix_full.diff` proposed patch; `/tmp/mypyC/pytest_full.txt` full test log
- `/tmp/mypyC/gh/` fetched issues/PRs/discussions
