# Day 4 verification, batch v2 (Plan §6 checklist)

Candidates: the four rows 'stale alias condition', 'constant fold tuple subclass', 'read-only property Never' and 'Flag combination Never' of `campaign/day3-report.md` §4.2.
Date of runs: 2026-11-05. Everything below was run by hand; the minimised programs live in `/tmp/d4v/final/` (not tracked) and are pasted in full in each section.

## 0. Setup and conventions

| Tool | Pinned (project venv) | Latest (PyPI on 2026-11-05) | Master |
|---|---|---|---|
| mypy | 2.4.0 (compiled) | 2.4.1 (compiled), `/tmp/d3v-latest` | 2.5.0+dev.879da562a4bba1ff8023799afad195bc364b730a (not compiled), `/tmp/d3v-master` |
| ty | 0.0.84 | 0.0.97 (released 2026-11-04), `/tmp/d3v-latest` | not available (no source build) |
| pyright | 1.1.414 | 1.1.414 (is also the PyPI latest) | n/a |
| CPython | 3.13.16 | | |

Command pattern (cwd = directory of the program, `VIRTUAL_ENV` unset, `--python-version 3.13` everywhere). The pinned binaries in `.venv/bin` are already memguard shims, so wrapping them again fails with a systemd scope-name collision; they run as is. Latest and master always go through `memguard.sh`:

```
V=/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/.venv/bin
G=/home/derek/.config/kiro-hooks/memguard.sh
$V/mypy --python-version 3.13 --check-untyped-defs --no-incremental --no-error-summary --show-column-numbers --show-error-codes F.py
$V/ty check --python-version 3.13 --output-format concise --no-progress --color never F.py
$V/pyright --pythonversion 3.13 F.py
$G /tmp/d3v-latest/bin/mypy   ...same flags...   F.py
$G /tmp/d3v-latest/bin/ty check ...same flags... F.py
$G /tmp/d3v-latest/bin/pyright --pythonversion 3.13 F.py
$G /tmp/d3v-master/bin/mypy   ...same flags...   F.py
$V/python F.py
```

Pinned and latest outputs were identical in every run below, so each output block is shown once and marked "pinned = latest" unless noted. Master mypy equalled mypy 2.4.1 everywhere.

Bottom line, before the details:

| # | Candidate | ty | mypy | pyright | New bug? |
|---|---|---|---|---|---|
| 1a | stale alias condition (as reported: alias, then method call) | NOT_BUG, DUPLICATE ty#2792 | NOT_BUG, KNOWN_LIMITATION (mypy#13807) | NOT_BUG, DESIGN_DIVERGENCE | no |
| 1b | stale alias condition, **new finding while generalising**: alias narrowing survives a reassignment on a loop back edge | **BUG, INCORRECT_INFERENCE (observable as FALSE_NEGATIVE)**, conf 0.9 | NOT_BUG | NOT_BUG | **yes, ty** |
| 2 | constant fold tuple subclass | NOT_BUG, DUPLICATE ty#2171 (design: ty#2140) | NOT_BUG | NOT_BUG | no |
| 3 | read-only property Never | NOT_BUG, DUPLICATE ty#2792 (and the claim "ty is silent on the read-only assignment" is refuted) | NOT_BUG | NOT_BUG | no |
| 4 | Flag combination Never | NOT_BUG, DUPLICATE ty#876 (underlying symptom INCORRECT_INFERENCE) | NOT_BUG | NOT_BUG | no |

---

## 1. 'stale alias condition'

Day-3 programs: `narrowing_builtin/d3p_narrowing_builtin_stale_alias_condition__mut1_71417fc0.py` (seed-61524ebfb287) and `__mut0_7429471b.py` (seed-e027e3604195). Report claim: at `reveal_type(a.x)` mypy `int | None`, ty `int`, pyright like mypy, runtime `None`.

### 1.1 REPRODUCE (1a, the claim as reported)

`/tmp/d4v/final/c1_stale_alias_call.py` (20 lines):

```python
from typing import reveal_type


class A:
    def __init__(self, x: int | None) -> None:
        self.x = x

    def clear(self) -> None:
        self.x = None


def f(a: A) -> None:
    is_none = a.x is None
    a.clear()
    if not is_none:
        reveal_type(a.x)
        print(a.x)


f(A(3))
```

Output (pinned = latest, master mypy same as mypy):

```
mypy:    c1_stale_alias_call.py:16:21: note: Revealed type is "int | None"
ty:      c1_stale_alias_call.py:16:21: info[revealed-type] Revealed type: `int`
pyright: c1_stale_alias_call.py:16:21 - information: Type of "a.x" is "int | None"
CPython: Runtime type is 'NoneType'
         None
```

Reproduces on every version. It is a `reveal_type` difference only; no checker emits an error. The checks below decide whether `int` is a defect.

### 1.2 SPEC

- Typing spec, Type narrowing page (fetched from `https://typing.python.org/en/latest/spec/narrowing.html`): "Type checkers should narrow the types of expressions in certain contexts. This behavior is currently largely unspecified." The spec says nothing about aliased conditions, narrowing of member-access chains, or invalidation by calls. SILENT.
- mypy: open feature request python/mypy#13807 "Add support for control flow analysis of aliased conditions". Pyright's mypy-comparison doc: "Mypy does not currently support this".
- pyright (`docs/type-concepts-advanced.md`, Aliased Conditional Expression): the technique is "limited to cases where expression `a` is a simple identifier (as opposed to a member access expression or subscript expression)". So mypy and pyright both leave `a.x` un-narrowed by design; their `int | None` is not evidence against ty.
- ty: alias narrowing was added deliberately (ruff#24302 "Support basic narrowing with aliased conditional expressions", merged 2026-04-25, closes ty#719 "almost"). mdtest `narrow/aliased_conditions.md` has a section "Attribute access alias" that expects `a.x` to narrow through an alias.

### 1.2b Argue ty's side

ty narrows `a.x` after any `if a.x is not None:` and does not invalidate on calls. Variants below show that ty, mypy and pyright all print `int` for the direct form, so `int` after `a.clear()` is the shared, known unsoundness of member-access narrowing, not something the alias adds. ty's tracker has it as open issue ty#2792 "Consider invalidating attribute narrowing based on method calls known to mutate that attribute" (a user reports the same with `session.refresh(user)`). The alias only reaches `a.x` because ty chose to support attribute targets.

### 1.3 STRONGEST ORACLE

Runtime value `None` contradicts ty's `int` (RUNTIME, strong). But the same contradiction holds for the direct form in all three tools (variant 1a-2), which is why it is a known limitation and not a ty-only defect.

### 1.4 GENERALISE (1a)

| Variant (file in `/tmp/d4v/w/`) | ty | mypy | pyright | runtime | Reading |
|---|---|---|---|---|---|
| alias, then `a.clear()` (`stale_a`) | `int` | `int \| None` | `int \| None` | None | claim |
| 1a-2 direct `if a.x is not None: a.clear()` (`stale_b_direct`) | `int` | `int` | `int` | None | all tools unsound: known limitation |
| property + `isinstance` alias, then `clear()` (`stale_f_prop`) | `int` | `int \| None` | `int \| None` | None | same as claim |
| property + direct `isinstance` (`stale_g_prop_direct`) | `int` | `int` | `int` | None | all tools unsound |
| alias, then module-level helper mutates (`stale_h_global_fn`) | `int` | `int \| None` | `int \| None` | None | same as claim |
| alias, then `a.x = None` (`stale_c_assign`) | `None` | `None` | `None` | None | pass |
| local `x` alias, then `x = None` (`stale_d_local`) | `None` | `None` | `None` | None | pass |
| alias, no mutation (`stale_e_noclear`) | `int` | `int \| None` | `int \| None` | int | ty is right and more precise |
| alias, then rebind root `a = other` (`al_b_rebind`) | `int \| None` | `int \| None` | `int \| None` | None | pass |
| alias reassigned to another check (`al_c_realias`) | `int \| None` | `int \| None` | `int \| None` | None | pass |
| alias, then tuple-swap `a, b = b, a` (`al_e_walrus`) | `int \| None` | `int \| None` | `int \| None` | None | pass |
| alias, then `if random: a.x = None` (`al_h_branch`) | `int \| None` | `int \| None` | `int \| None` | None | pass |

### 1.5 DUPLICATES (1a)

- `/tmp/d3v-trk/ty.json` (4060 issues, refreshed 2026-11-05), venv python, regexes: `narrow.{0,60}(invalidat|stale|method call|mutat)`, `(invalidat|stale).{0,60}narrow`, `attribute narrowing.{0,60}(call|mutat)`, `alias.{0,40}(condition|narrow)|narrow.{0,40}alias`, `sound.{0,40}narrow.{0,40}(attribute|member)`. Hits: **ty#2792 (OPEN)**, ty#4379 (closed), ty#719 (closed, feature), ty#3846 (closed, custom `__setattr__`).
- `gh search issues` on astral-sh/ty: "aliased conditional" gave ty#3212 (open, indirect narrowing through a property), ty#719, ty#1258 (closed, isinstance alias). Phrases "attribute narrowing method call", "narrowing invalidated function call mutates attribute", "narrowing stale after call", "is None alias variable narrowing attribute" returned nothing new.
- `gh search prs` on astral-sh/ruff: "aliased conditional" gave ruff#24302 (merged) and ruff#23937 (open, the full implementation).
- mypy: `gh search issues` "aliased conditional expressions" gave mypy#19029, #15653, #15332 (all closed); mypy#13807 (open) read via `gh issue view`. pyright: "aliased conditional expression member access", "narrowing member access not invalidated by call", "aliased conditional expression loop", "narrowing alias loop" gave nothing relevant (erictraut's answer in ty#719 explains the feature is pyright's, borrowed from TypeScript).
- known_upstream.json: MYPY-20969 (mypy keeps subscript narrowing after assignment) is the mirror image on the mypy side and concerns a different tool; no ty entry covers this.

Best three read: ty#2792 (body above: narrowing kept across `self.modify()`), ty#719 (alias feature, closed by ruff#24302), mypy#13807 (alias feature missing in mypy).

### 1.6 PLAYGROUND

UNVERIFIED-PLAYGROUND (no playground link was created; filing is out of scope).

### 1.7 VERDICT (1a)

- ty: NOT_BUG, Dismissal DUPLICATE of https://github.com/astral-sh/ty/issues/2792, confidence 0.8, faulty_tool none.
- mypy: NOT_BUG, KNOWN_LIMITATION (https://github.com/python/mypy/issues/13807), confidence 0.9.
- pyright: NOT_BUG, DESIGN_DIVERGENCE (documented limit to identifiers), confidence 0.9.

---

### 1b. NEW FINDING: ty alias narrowing ignores a reassignment that reaches the use over a loop back edge

While generalising 1a I tried the other thing the alias feature promises in its own mdtest: "If the target is reassigned between the definition of the alias and its use as a condition, narrowing does not take place." Straight-line and branch reassignments hold (table 1a rows `stale_c`, `stale_d`, `al_h_branch`). A reassignment at the end of a loop body, which reaches the next iteration's use over the back edge, does not.

### 1b.1 REPRODUCE

`/tmp/d4v/final/c1_alias_loop_backedge.py` (11 lines):

```python
def f(x: int | None) -> int:
    is_none = x is None
    total = 0
    for _ in range(2):
        if not is_none:
            total += x + 1
        x = None
    return total


print(f(3))
```

Output (pinned = latest for all four tools; master mypy same as mypy 2.4.1):

```
mypy:    c1_alias_loop_backedge.py:6:22: error: Unsupported operand types for + ("None" and "int")  [operator]
         c1_alias_loop_backedge.py:6:22: note: Left operand is of type "int | None"
ty:      All checks passed!
pyright: c1_alias_loop_backedge.py:6:22 - error: Operator "+" not supported for "None" (reportOptionalOperand)
CPython: TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'   (exit=1)
```

Same on ty 0.0.84 and 0.0.97. With `reveal_type(x)` in place of the addition (`alias_loop_reveal`): ty `int`, mypy and pyright `int | None`, runtime second iteration `NoneType`.

### 1b.2 SPEC and docs

- Typing spec: narrowing "largely unspecified" (see 1.2). SILENT.
- ty's own contract, mdtest `narrow/aliased_conditions.md`, section "Narrowing is invalidated when target is reassigned": states that narrowing does not take place if the target is reassigned between the alias definition and its use. The same file has "Alias reassigned on a loop backedge" but only for the alias variable, not for the target. The loop-back-edge reassignment of the *target* is not covered by any test there.
- Direct narrowing in ty already handles this shape: `if x is not None:` before the loop and `x = None` at the end gives `int | None` (variant `al_f_direct_loop`), and ty#4379 (closed 2026-08-28) fixed the root-reassigned-in-while case for direct narrowing.

### 1b.2b Argue ty's side

(i) Alias narrowing is "basic" by the PR's own words (ruff#24302: cross-scope and chained aliases not supported yet). Counter: those limits are listed as TODO in the mdtest; loop back edges are not, and the section on target reassignment states the opposite contract. (ii) pyright and mypy do not narrow at all here, so their answer is not evidence. (iii) A design reading "an alias is evaluated at the definition, later iterations are out of scope" would be unsound and also contradicts the straight-line behaviour. No reading of the docs makes `int` intended.

### 1b.3 STRONGEST ORACLE

CPython raises `TypeError` on the exact line where ty says the operand is `int` (RUNTIME, strong). In addition ty contradicts itself: direct narrowing with the same loop gives `int | None`, alias narrowing gives `int` (SELF_CONTRADICTION, strong). mypy and pyright also reject, but that is only weak consensus.

### 1b.4 GENERALISE

| Variant (file) | ty | mypy | pyright | runtime | Reading |
|---|---|---|---|---|---|
| `x + 1`, reassign at loop end (`alias_loop_min`) | silent | error | error | TypeError | bug |
| `reveal_type(x)` (`alias_loop_reveal`) | `int` | `int \| None` | `int \| None` | NoneType on iteration 2 | bug |
| attribute target, `a.x = None` at loop end, `a.x + 1` (`alias_loop_attr_fn`) | silent | error | error | TypeError | bug |
| attribute target, reveal (`al_d_loop`) | `int` | `int \| None` | `int \| None` | None on iteration 2 | bug |
| `while` loop (`al_j_while`) | `int` | `int \| None` | `int \| None` | None on iteration 2 | bug |
| `isinstance` alias (`al_k_isinstance`) | `int` | `int \| str` | `int \| str` | str on iteration 2 | bug |
| `ok = x is not None` alias, `while` loop (`alias_loop_walrus_cond`) | `int` | `int \| None` | `int \| None` | None on iteration 2 | bug |
| control: direct `if a.x is not None:` before loop (`al_f_direct_loop`) | `int \| None` | `int \| None` | `int \| None` | | pass |
| control: reassignment *before* the use in the body (`alias_loop_assign_first`) | `None` | `None` | `None` | None | pass |
| control: `for x in xs` rebinds the target (`alias_loop_for_target`) | `int \| None` | `int \| None` | `int \| None` | None | pass |

The failing shape is exactly: alias defined before the loop, use in the loop, target reassigned later in the same loop body.

### 1b.5 DUPLICATES

- ty.json regexes: `aliased (conditional|condition|narrowing)`, `intermediate (boolean|variable)`, `(bool|boolean) variable.{0,120}narrow`, `narrowing constraint.{0,80}(loop|back.?edge)`, `(loop|back.?edge).{0,100}(alias|narrowing constraint)`, `is_none|is_not_none`, `(stale|outdated).{0,40}(narrow|condition)`, `while.{0,60}narrow.{0,60}(reassign|invalidat)`. Hits are only ty#719, ty#2904 (duplicate of #719), ty#3212, and unrelated alias/loop titles. None mentions a loop back edge with alias narrowing.
- `gh search issues` (astral-sh/ty, no state flag): "aliased conditional expression loop", "narrowing boolean variable loop reassignment", "intermediate variable narrowing loop", "alias narrowing stale loop", "narrowing constraint loop reassigned", "intermediate boolean variable narrowing": all returned nothing. "aliased conditional" returned ty#3212, #719, #1258 (none about loops).
- `gh search prs` (astral-sh/ruff): "aliased conditional" returned ruff#24302 and ruff#23937; "intermediate boolean variable narrowing" and "narrowing alias loop" returned nothing. ruff#24302's description does not mention loops.
- Related but different: ty#4379 (closed, direct narrowing, root reassigned in a `while`), ty#2792 (open, calls).
- known_upstream.json entries listed in the task (TY-4882/4883/4884/4898/4899/4900, MYPY-22339/22343/22344/22360/22361, MYPY-20969, MYPY-21937, TY-3765, TY-876): none is about alias narrowing in loops. MYPY-19889 is an unrelated dataclass InitVar issue.

Result: no duplicate found. Run one last search on the exact title before filing.

### 1b.6 PLAYGROUND

UNVERIFIED-PLAYGROUND.

### 1b.7 VERDICT

- ty: **BUG**, symptom INCORRECT_INFERENCE (narrowed type `int` where the value can be `None`), observable as FALSE_NEGATIVE (`unsupported-operator` missing on `x + 1`), confidence 0.9, faulty_tool ty. Draft in `campaign/day4/issue-drafts-v2.md`. Reproducer in `runs/hits/d4v_ty_alias_loop_backedge.py`.
- mypy: NOT_BUG (correct error). pyright: NOT_BUG (correct error).

---

## 2. 'constant fold tuple subclass'

Programs: `tuples_unpacking/d3p_tuples_unpacking_constant_fold_subclass__mut1_abe32df5.py` (seed-e1e14ede1dfc), `__mut0_fef00a03.py` (seed-b25f9bf52142), and the Day-2 log-only file `calibration/must_stay_live/ty_constant_fold_tuple_subclass.py` (included, see 2.1).

Reading of the seed reports: in `mut0_fef00a03` ty prints `Never` for `r` only because `assert r is True` runs after ty folded `r` to `Literal[False]`; the fold is the root cause and `Never` is its aftermath.

### 2.1 REPRODUCE

`/tmp/d4v/final/c2_tuple_subclass_fold.py` (16 lines):

```python
from typing import Literal, reveal_type


class Restricted(tuple[Literal[1]]):
    def __lt__(self, other: tuple[Literal[1], ...], /) -> bool:
        return True

    def __eq__(self, other: object, /) -> bool:
        return True


x = Restricted((1,))
reveal_type(x.__lt__((1,)))
reveal_type(x < (1,))
reveal_type(x == (2,))
print(x < (1,), x == (2,))
```

Output (pinned = latest, master mypy same):

```
mypy:    13:13 Revealed type is "bool"   14:13 Revealed type is "bool"   15:13 Revealed type is "bool"
ty:      13:13 info[revealed-type] Revealed type: `bool`
         14:13 info[revealed-type] Revealed type: `Literal[False]`
         15:13 info[revealed-type] Revealed type: `Literal[False]`
pyright: Type of "x.__lt__((1, ))" is "bool" / "x < (1, )" is "bool" / "x == (2, )" is "bool"
CPython: True True
```

The Day-2 file `ty_constant_fold_tuple_subclass.py` run as is (`assert_type(r, bool)` after `r = Restricted((1,)) < (1,)`):

```
mypy (pinned, latest, master): no output
ty (pinned, latest): fold_mustlive.py:15:1: error[type-assertion-failure] Type `Literal[False]` does not match asserted type `bool`
pyright: 0 errors, 0 warnings, 0 informations
CPython: True
```

Reproduces on ty 0.0.84 and 0.0.97. The Day-2 file stays live (nothing in the KB closes it; this verification only classifies it).

### 2.2 SPEC

Typing spec tuples page (local cache `spec/tuples.txt`, grepped for "subclass", "__eq__", "compar"): no hit. SILENT on comparison folding and on tuple subclasses that override comparison methods. Narrowing is "largely unspecified" (see 1.2). ty's docs pages in the cache (`features/type-system`, `typing-faq`, `coming-from-mypy-or-pyright`) do not mention it. It is documented as intended only in the tracker: Carl Meyer in ty#2140: ty is "working as designed", because `tuple` includes subclasses that "are free to arbitrarily override `__eq__`"; Alex Waygood in the same thread: "we're planning to ban `__eq__` overrides (and overrides of other comparison methods) on tuple subclasses, or many of the `Literal` types we infer for tuple comparisons aren't sound". Open issue ty#2171 (labels unsoundness, diagnostics, help wanted) tracks "emit a diagnostic on unsafe dunder method overrides on tuple subclasses": narrowings are sound only if tuple subclasses do not override `__len__`, `__bool__` or `__eq__`.

### 2.2b Argue ty's side / desugar probe

Desugaring `x < (1,)` to `x.__lt__((1,))` and `Restricted.__lt__(x, (1,))`: ty gives `bool` for both, `Literal[False]` for the operator form. That is a real self-contradiction in the output, but it is the documented price of the "tuple subclasses do not override comparison dunders" assumption, which ty applies to every tuple type. Proof that the assumption is global and not special to this class: a plain parameter `t: tuple[Literal[1]]` folds `t == (2,)` and `t < (1,)` to `Literal[False]` too (`fold_v2_param`). ty's fold is by design, with a diagnostic planned (ty#2171). The one weaker point for ty: here the override sits in the same file and ty could see it. The maintainers have not asked for that special case.

### 2.3 STRONGEST ORACLE

RUNTIME: `x < (1,)` is `True`; SELF_CONTRADICTION: `x.__lt__((1,))` is `bool`. Both strong, both already acknowledged by ty maintainers.

### 2.4 GENERALISE

| Variant (file) | ty | mypy | pyright | runtime |
|---|---|---|---|---|
| `<` override (`fold_lt`) | `Literal[False]` | `bool` | `bool` | True |
| `==` override (`fold_eq`) | `Literal[False]` | `bool` | `bool` | True |
| `!=` and `<=` overrides (`fold_v1_ne`) | `Literal[False]`, `Literal[True]` | `bool`, `bool` | `bool`, `bool` | True, False |
| reflected, `(1,) < Restricted(..)` with `__gt__` override (`fold_reflected`) | `Literal[False]` | `bool` | `bool` | True |
| two literal elements (`fold_v5_lt_nolit`) | `Literal[False]` | `bool` | `bool` | True |
| declared `r: Restricted`, `r == (2,)` (`fold_v3_annot`) | `Literal[False]` (but `r.__eq__((2,))` is `bool`) | `bool` | `bool` | |
| non-literal elements, `Pair(tuple[int, int])` (`fold_v4_int_elems`, `fold_nonliteral`) | `bool` | `bool` | `bool` | True |
| `NamedTuple` subclass with `__lt__` override (`fold_namedtuple`) | `bool` | `bool` | `bool` | False |
| plain `(1,) < (1,)`, `(1,) == (2,)` (`fold_plain`) | `Literal[False]` (correct) | `bool` | `bool` | False |
| parameter `t: tuple[Literal[1]]` (`fold_v2_param`) | `Literal[False]` | `bool` | `bool` | |

The fold needs fixed-length tuples with literal elements; non-literal elements and NamedTuples are not folded.

### 2.5 DUPLICATES

- ty.json: `tuple.{0,60}subclass` (11 hits), `tuple.{0,50}(subclass).{0,80}(__eq__|__lt__|comparison|compar)`, `(__eq__|__lt__).{0,80}tuple.{0,40}subclass`, `constant.fold|fold.{0,20}(tuple|comparison)`. Matches: **ty#2171 (OPEN)**, **ty#2140 (closed)**, ty#3413 (tuple addition assumes no odd `__add__`), ty#215, ty#4659.
- `gh search issues` astral-sh/ty: "unsafe tuple subclass" returned ty#2171; "tuple subclass __eq__", "tuple subclass override comparison Literal", "tuple subclass __lt__ Literal[False]", "tuple comparison overloaded dunder narrowing" returned nothing.
- `gh search prs` astral-sh/ruff "tuple subclass": ruff#28005 "Account for known subclasses in equality inference" (merged 2026-08-24, fixes ty#4377, so included in 0.0.97; it does not change these results), ruff#29090, ruff#28446, ruff#25078 (closed, more precise tuple addition), ruff#28769 (open, tuple subclass iterator overrides). "tuple comparison Literal" returned nothing.
- known_upstream.json: no entry for this; TY-4883 is a different tuple-alias performance issue.

### 2.6 PLAYGROUND

UNVERIFIED-PLAYGROUND.

### 2.7 VERDICT

- ty: NOT_BUG, Dismissal DUPLICATE of https://github.com/astral-sh/ty/issues/2171 (design decision recorded in https://github.com/astral-sh/ty/issues/2140), confidence 0.85, faulty_tool none. The missing diagnostic on the override is exactly ty#2171.
- mypy: NOT_BUG (`bool` is correct, no folding). pyright: NOT_BUG.
- Reproducer kept as an instructive parent: `runs/hits/d4v_ty_tuple_subclass_dunder_fold.py`.

---

## 3. 'read-only property Never'

Program: `descriptors_properties/gen7_14eb1842.py` (seed-4aa8be0814f0). Report claim: mypy `[misc] Property "readonly" ... read-only` at `t.readonly = 5`, ty silent and infers `t: Never`, pyright like mypy.

### 3.1 REPRODUCE

Bisection first. In the 35-line original ty gives `t: Thing` up to `t.__dict__["doubled"] = 99`, and `Never` from the line after `assert t.doubled == 99` (revealed at lines 36, 38, 41 of `ro_orig_reveal.py`; mypy and pyright print `Thing` at every point). Without the preceding asserts ty does report the read-only assignment:

```
ty (pinned = latest), ro_min.py:   ro_min.py:15:1: error[invalid-assignment] Cannot assign to read-only property `readonly` on object of type `Thing`: Attempted assignment to `Thing.readonly` here
mypy:                              ro_min.py:15:1: error: Property "readonly" defined in "Thing" is read-only  [misc]
pyright:                           ro_min.py:15:14 - error: Cannot assign to attribute "readonly" for class "Thing"
CPython:                           AttributeError: property 'readonly' of 'Thing' object has no setter
```

So the claim "ty is silent on read-only property assignment" is false. ty is silent only because the statement is unreachable. Minimal program, `/tmp/d4v/final/c3_readonly_never.py` (24 lines):

```python
from typing import reveal_type


class C:
    def __init__(self, n: int) -> None:
        self.n = n

    @property
    def readonly(self) -> int:
        return self.n

    def bump(self) -> None:
        self.n = 99


def f(c: C) -> None:
    assert c.n == 8
    c.bump()
    assert c.n == 99
    reveal_type(c)
    c.readonly = 5


f(C(8))
```

Output (pinned = latest, master mypy same as mypy 2.4.1):

```
mypy:    c3_readonly_never.py:20:17: note: Revealed type is "c3_readonly_never.C"
         c3_readonly_never.py:21:5: error: Property "readonly" defined in "C" is read-only  [misc]
ty:      c3_readonly_never.py:20:17: info[revealed-type] Revealed type: `Never`          (no error at line 21)
pyright: c3_readonly_never.py:20:17 - information: Type of "c" is "C"
         c3_readonly_never.py:21:18 - error: Cannot assign to attribute "readonly" for class "C"
CPython: Runtime type is 'C'
         AttributeError: property 'readonly' of 'C' object has no setter
```

### 3.2 SPEC

Narrowing "largely unspecified" (see 1.2); no spec rule on call invalidation or on reporting in unreachable code. SILENT. None of the ty doc pages in the local cache mention call invalidation; it is requested as a feature in ty#2792.

### 3.2b Argue ty's side

`assert c.n == 8` followed by `assert c.n == 99` with nothing in between is contradictory, so unreachable is the right answer for straight-line code. Check `ro_n4_local` (`n: int`, two contradictory asserts): ty `Never` and pyright reports nothing at all (also unreachable); only mypy keeps checking. ty only goes wrong because a method call between the asserts rebinds `self.n`, and ty does not invalidate attribute narrowing on calls. That is ty#2792, shared by variant `ro_n5_noassert1` where pyright also computes `c.n: Never` (it just does not propagate the `Never` to `c`). The `__dict__` write in the original is another mutation that ty cannot see.

### 3.3 STRONGEST ORACLE

RUNTIME: `AttributeError` raised on the line ty did not check. Strong, but it follows from the call-invalidation gap, not from a property-handling defect.

### 3.4 GENERALISE

| Variant (file) | ty | mypy | pyright | runtime |
|---|---|---|---|---|
| bare read-only assignment (`ro_min`) | error `invalid-assignment` | error | error | AttributeError |
| same inside `try/except AttributeError` (`ro_try`) | error | error | error | caught |
| asserts around `c.bump()` (`ro_n2_method`) | `c: Never` | `C` | `C` | C |
| non-data descriptor, `t.__dict__[..] = 99` between asserts (`ro_n1_desc`) | `Never` | `Thing` | `Thing` | Thing |
| direct assignment `c.n = 99` between asserts (`ro_n3_assign`) | `C` | `C` | `C` | C |
| local `n: int`, contradictory asserts (`ro_n4_local`) | `Never` | `int` | unreachable | |
| nested `if c.n == 8: c.bump(); if c.n == 99:` (`ro_n5_noassert1`) | `Never`, `Never` | `int`, `C` | `Never`, `C` | reached |

### 3.5 DUPLICATES

- ty.json: `read-only property.{0,80}(Never|unreachable)`, `__dict__.{0,60}(narrow|descriptor)`, `non-data descriptor.{0,80}(narrow|instance)`, `narrow.{0,60}(==|equal).{0,60}(Literal|int)`, `__dict__\[`, `assert .* == \d+\n.*assert .* == \d+`: nothing property- or descriptor-specific. The call-invalidation root cause is **ty#2792 (OPEN)**; its comment thread has the same pattern with `assert user.pw_reset_link is None` followed by `session.refresh(user)`.
- `gh search issues` astral-sh/ty: "narrowing attribute equality unreachable Never", "assert attribute == literal then different literal Never", "non-data descriptor instance dict shadow", "read-only property assignment unreachable no diagnostic", "narrowing == literal int attribute": nothing. `gh search prs` ruff "narrowing attribute method call": nothing.
- mypy and pyright are not accused, so no tracker search for them.

### 3.6 PLAYGROUND

UNVERIFIED-PLAYGROUND.

### 3.7 VERDICT

- ty: NOT_BUG, Dismissal DUPLICATE of https://github.com/astral-sh/ty/issues/2792 (attribute narrowing not invalidated by calls), confidence 0.8, faulty_tool none. The Day-3 reading "ty misses the read-only property error" is refuted by `ro_min`.
- mypy: NOT_BUG (correct `[misc]` error). pyright: NOT_BUG (correct error).
- Reproducer kept as an instructive parent: `runs/hits/d4v_ty_attr_eq_narrow_unreachable.py`.

---

## 4. 'Flag combination Never'

Program: `enums_literals/d3p_enums_flag_or_literal_union__mut0_41da72aa.py` (seed-e4277cc03f53). Report claim: mypy `[arg-type]` on `only_r(combined)`, ty silent with `combined: Never`, pyright like mypy, persists with `strict-equality-semantics=true`, "so TY-STRICT-EQUALITY does not explain it".

### 4.1 REPRODUCE

Bisection with `reveal_type(combined)` after each statement (`flag_orig_reveal.py`): ty prints `Literal[F.R, F.W]` after `combined = F.R | F.W` and after both `assert (combined is F.x) is False` lines (ty does not narrow on `(expr) is False`); it prints `Never` after `assert combined.value == 3`, because ty derived `combined.value` as `Literal[1, 2]` from the expanded members and `== 3` is then impossible. So the final `only_r(combined)` is unreachable. mypy and pyright print `F` at every point. `/tmp/d4v/final/c4_flag_combination.py` (23 lines):

```python
import enum
from typing import Literal, reveal_type


class F(enum.Flag):
    R = 1
    W = 2


def only_r(x: Literal[F.R]) -> int:
    return 1


c = F.R | F.W
reveal_type(c)
only_r(c)
if c is F.R:
    print("R")
elif c is F.W:
    print("W")
else:
    reveal_type(c)
    print("both")
```

Output (pinned = latest, master mypy same):

```
mypy:    c4_flag_combination.py:15:13: note: Revealed type is "c4_flag_combination.F"
         c4_flag_combination.py:16:8: error: Argument 1 to "only_r" has incompatible type "F"; expected "Literal[F.R]"  [arg-type]
ty:      15:13 info[revealed-type] Revealed type: `Literal[F.R, F.W]`
         16:8  error[invalid-argument-type] Argument to function `only_r` is incorrect: Expected `Literal[F.R]`, found `Literal[F.R, F.W]`
         22:17 info[revealed-type] Revealed type: `Never`
pyright: 15:13 Type of "c" is "F"
         16:8  error: Argument of type "F" cannot be assigned to parameter "x" of type "Literal[F.R]" ...
         22:17 Type of "c" is "F"
CPython: Runtime type is 'F' / Runtime type is 'F' / both
```

In this smaller program ty does report the argument error, for the wrong reason (it thinks the value is `F.R` or `F.W`). In the original it is silent only because earlier asserts made the line `Never`. The root cause is the inferred `Literal[F.R, F.W]`; `Never` follows from narrowing that wrong type.

### 4.2 SPEC

Typing spec, Enums, "Enum Literal Expansion" (fetched from `https://typing.python.org/en/latest/spec/enums.html`): "This rule does not apply to classes that derive from enum.Flag because these enums allow flags to be combined in arbitrary ways." and expansion into members is allowed only for enums "that does not derive from enum.Flag". ty's output expands a Flag combination to the member union, which the spec exempts. ty's docs: no page mentions Flag; ty's tracker has the unchecked item "Handling of `enum.Flag` (enum expansion may not be performed for subclasses of `enum.Flag`)" in ty#876.

### 4.2b Argue ty's side

ty does not claim Flag support yet. sharkdp closed ty#3765 (`IntFlag` result narrowed too much) with "We do not support `enum.Flag` yet, please see https://github.com/astral-sh/ty/issues/876". Cause visible in typeshed's `Flag.__or__(self, other: Self) -> Self`: ty solves `Self` from the literal operand types (`Literal[F.R]`, `Literal[F.W]`) instead of the class. Several PRs on Flag were tried and closed unmerged (ruff#19617, #22733, #23808). So the behaviour is known, tracked and unfinished, not an unnoticed bug.

### 4.3 STRONGEST ORACLE

SPEC quote above, plus RUNTIME: `(F.R | F.W) is F.R` and `is F.W` are both `False`, the value is `<F.R|W: 3>`, and the `else` branch of the is-chain runs ("both") where ty says `Never`. Strong evidence of an incorrect inference in ty. It is already tracked, hence a duplicate.

### 4.4 GENERALISE

| Variant (file) | ty | mypy | pyright | runtime |
|---|---|---|---|---|
| `F.R \| F.W` (`flag_v1_ops`) | `Literal[F.R, F.W]` | `F` | `F` | `F.R\|W` |
| `F.R & F.W` | `Literal[F.R, F.W]` | `F` | `F` | `F(0)` |
| `F.R ^ F.W` | `Literal[F.R, F.W]` | `F` | `F` | `F.R\|W` |
| `~F.R` | `Literal[F.R]` | `F` | `F` | `F.W` |
| `F.R \| F.R` | `Literal[F.R]` (correct) | `F` | `F` | `F.R` |
| `I.A \| I.B` on `IntFlag` | `Literal[I.A]` | `I` | `I` | `3` |
| `ok: Literal[F.R, F.W] = F.R \| F.W` (`flag_v3_declared`) | accepted | accepted | rejected | `ok is F.R` False |
| same with `IntFlag` (`flag_v4_intflag`) | `c` is `Literal[I.A]`, accepted | `I`, accepted | `I`, rejected | `3` |
| `is`-chain with `else` (`flag_v2_else`) | `Never` in `else` | no output | `F` | `both` |
| `c.value`, `c in (F.R, F.W)` (`flag_v5_member_in`) | `Literal[1, 2]`, `bool` | `Literal[1]? \| Literal[2]?`, `bool` | `int`, `bool` | `3`, `False` |

mypy accepts the `Literal[F.R, F.W]` declaration silently in `flag_v3_declared`, which is a mypy-side leniency and not part of this candidate.

### 4.5 DUPLICATES

- ty.json: `enum\.Flag|IntFlag` (ty#3765 closed, ty#1889 open overview, **ty#876 open**, ty#183), `Flag.{0,40}(__or__|union|combin|pseudo)`, `\bF\.R\s*\|\s*F\.W`, `Self.{0,60}Literal.{0,40}(enum|member)`, `Literal\[\w+\.\w+, \w+\.\w+\].{0,60}(Flag|bitwise)`: ty#876 is the match.
- `gh search issues` astral-sh/ty: "enum.Flag combination Literal", "Flag bitwise or Literal members", "IntFlag or narrowed", "Flag pseudo-member", "Self return literal receiver enum": no new result beyond the tracker hits. `gh search prs` astral-sh/ruff "enum Flag": ruff#19617, #22733, #23808 (closed, unmerged), #27148, #27802, #22231 (unrelated). "IntFlag" hit the API rate limit; covered by the tracker grep of ty#3765.
- `gh issue view` read: ty#876 (checkbox "Handling of `enum.Flag`" unchecked, state OPEN as of 2026-11-05), ty#3765 (closed, redirect to #876).
- known_upstream.json: **TY-876** (`reveal_mismatch`, `Literal\[`) and **TY-876-ASSERT** already cover this root cause. They did not fire on the Day-3 report row because that discrepancy was `only_mypy` on `only_r(combined)`. mypy#21937 (MYPY-21937, mypy expands Flag like a plain Enum) is the opposite-side bug and does not apply here (mypy gives `F`).

### 4.6 PLAYGROUND

UNVERIFIED-PLAYGROUND.

### 4.7 VERDICT

- ty: NOT_BUG as a new finding, Dismissal DUPLICATE of https://github.com/astral-sh/ty/issues/876, confidence 0.9; underlying symptom INCORRECT_INFERENCE, faulty_tool ty (already tracked).
- mypy: NOT_BUG (correct `[arg-type]`). pyright: NOT_BUG.
- KB gap worth fixing by whoever owns the KB: TY-876 only matches `reveal_mismatch` and `type-assertion-failure`; an `only_mypy` `arg-type` where ty is silent because Flag-derived `Never` made the line unreachable is not matched. Not edited here (out of scope).
- Reproducer kept as an instructive parent: `runs/hits/d4v_ty_flag_or_else_never.py`.

---

## 5. Files written

- `campaign/day4/verify-v2.md` (this file)
- `campaign/day4/issue-drafts-v2.md` (one ty draft, candidate 1b; not filed)
- `runs/hits/d4v_ty_alias_loop_backedge.py` (bug), `d4v_ty_tuple_subclass_dunder_fold.py`, `d4v_ty_attr_eq_narrow_unreachable.py`, `d4v_ty_flag_or_else_never.py` (instructive). All four compile under the venv python, pass `typediff.generator.preflight(src, "3.13")` with no ERROR and no WARN, carry the three header lines, and exit 0 under CPython. `runs/` is in `.gitignore` (line 8), so these files are not committed.
- Rate limit note: `gh search` returned HTTP 403 (secondary rate limit) after about 30 calls; the affected phrases were re-run after a pause, except "IntFlag" (ruff PRs), noted in 4.5.
