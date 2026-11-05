"""Day-4 morning: promote the 8 programs proposed in campaign/day3-report.md section 5 into runs/hits/ as d4p_<name>.py.

Each body is copied unchanged. The generator's own leading comment header (`# area:`, `# hypothesis:`, `# origin:`,
`# features:`, sometimes twice) is replaced by the three header lines the seeds loader needs (plus the `# features:` line
when the program had one)."""
import re
import sys
from pathlib import Path

ROOT = Path("/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa")
GEN = ROOT / "runs/day3/gen"
HITS = ROOT / "runs/hits"

# (name, source relative to runs/day3/gen, AREAS key, hypothesis, seed id)
PARENTS = [
    ("descriptors_readonly_prop_never", "descriptors_properties/gen7_14eb1842.py", "descriptors_properties",
     "A read-only property assignment after contradictory attribute asserts and a __dict__ write: ty infers the receiver as Never and skips the AttributeError line; mypy and pyright report it. Vary: bump through a method, a descriptor, a local int.",
     "seed-4aa8be0814f0"),
    ("enums_flag_or_literal_union_only_r", "enums_literals/d3p_enums_flag_or_literal_union__mut0_41da72aa.py", "enums_literals",
     "F.R | F.W on a Flag is a pseudo-member, not a Literal union; passing it to a Literal[F.R] parameter is an error for mypy while ty expands the Flag and treats the line as unreachable (Never). Vary: IntFlag, ^ and & operators, a local instead of a module variable.",
     "seed-e4277cc03f53"),
    ("narrowing_stale_alias_loop", "narrowing_builtin/d3p_narrowing_builtin_stale_alias_condition__mut1_71417fc0.py", "narrowing_builtin",
     "An aliased None check kept across a mutating call (ty reveals int where the runtime value is None), plus the same alias reassigned inside a loop. Vary: while loop, isinstance alias, attribute target reassigned at loop end.",
     "seed-61524ebfb287"),
    ("metaclass_or_reflected_ror", "constructors_metaclasses/d3p_constructors_metaclasses_reflected_operator_on_metaclass__mut1_714d2273.py", "constructors_metaclasses",
     "With metaclass B overriding __ror__ and type(A) a base of type(B), A | B calls the reflected method first at runtime ('right'); mypy picks the left __or__, ty infers a UnionType. Vary: *, +, @ with __rmul__ etc.",
     "seed-83edc0d9bc6c"),
    ("enums_intenum_true_alias_one", "enums_literals/d3p_enums_literals_intenum_true_aliases_one__mut1_2f2cf71e.py", "enums_literals",
     "IntEnum TRUE = True after ONE = 1 is an alias of ONE at runtime (same object); mypy and pyright keep Literal[Integer.TRUE], ty reveals Literal[Integer.ONE]. Vary: StrEnum duplicate values, match/assert_never over an aliased enum.",
     "seed-0de4710c02b5"),
    ("tuples_fold_subclass_eq", "tuples_unpacking/d3p_tuples_unpacking_constant_fold_subclass__mut0_fef00a03.py", "tuples_unpacking",
     "A tuple subclass overriding __eq__ to return True: ty folds the comparison to Literal[False] and then sees the code after `assert r is True` as Never; mypy gives bool. Vary: __lt__/__ne__/__le__, reflected comparison, two literal elements.",
     "seed-b25f9bf52142"),
    ("callables_crash_ty_panic_partial_loop", "callables/d3p_crash_ty_panic_partial_or_none_in_loop__mut1_82a9fbe2.py", "callables",
     "Widening a functools.partial with `| None` inside a while loop panics ty 0.0.84 (salsa 'too many cycle iterations'); fixed in ty 0.0.85, so it is a regression guard for the pinned version. Vary: staticmethod or classmethod objects instead of partial.",
     "seed-c47eb01468dc"),
    ("inheritance_hash_none_from_eq", "inheritance_mro/d3p_inheritance_mro_hash_none_from_eq__mut1_fdf751d0.py", "inheritance_mro",
     "A class defining __eq__ without __hash__ has __hash__ = None at runtime; mypy and ty do not model it (mypy#20230), and `assert Plain.__hash__ is None` makes the next lines unreachable for ty (Never) and silent for mypy. Vary: Hashable parameter, set/dict key, dataclass(eq=True).",
     "seed-a43a619b6518"),
]

HEADER = re.compile(r"#\s*(area|hypothesis|origin|features):")


def main() -> int:
    for i, (name, rel, area, hyp, seed) in enumerate(PARENTS, 1):
        src = (GEN / rel).read_text()
        lines = src.split("\n")
        feats = [ln for ln in lines if ln.startswith("# features:")][:1]
        k = 0
        while k < len(lines) and HEADER.match(lines[k]):
            k += 1
        body = "\n".join(lines[k:])
        head = [f"# area: {area}", f"# hypothesis: {hyp}",
                f"# origin: runs/day3/gen/{rel} ({seed}); campaign/day3-report.md section 5 item {i}", *feats]
        out = HITS / f"d4p_{name}.py"
        out.write_text("\n".join(head) + "\n" + body)
        print(f"wrote {out.name}  <- {rel}  (dropped {k} old header lines, body {len(body.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
