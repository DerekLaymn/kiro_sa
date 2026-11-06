def r(a, b, nd=2):
    return f"{a}/{b}={a/b:.{nd}f}"
def p(a, b):
    return f"{a}/{b}={100*a/b:.1f}%"
print("Day10 judge: disc/prog", r(247, 250), "live/prog", r(172, 250), "prog live", p(101, 250), "wo", r(142, 250), p(91, 250), "closed", p(75, 247))
print("Day10 final: live", r(168, 250), p(99, 250), "wo", r(138, 250), p(89, 250), "closed", p(79, 247))
print("Day9 judge: disc", r(335, 250), "crash", r(4, 250), "live", r(224, 250), p(129, 250), "wo", r(180, 250), p(103, 250), "closed", p(115, 339))
print("Day9 final: live", r(198, 250), p(113, 250), "wo", r(154, 250), p(87, 250), "closed", p(141, 339))
print("Day8 judge: live", r(155, 250), p(104, 250), "wo", r(135, 250), p(92, 250), "closed", p(69, 224))
print("Day8 final: live", r(152, 250), p(104, 250), "wo", r(132, 250), p(91, 250), "closed", p(72, 224))
print("Day7 judge: live", r(107, 224), p(68, 224), "wo", r(88, 224), p(60, 224), "closed", p(75, 182))
print("Day7 final: live", r(75, 224), p(48, 224), "wo", r(63, 224), p(42, 224), "closed", p(107, 182))
print("Day6 judge: live", r(218, 250), p(127, 250), "closed", p(103, 321), "disc", r(259, 250), "crash", r(62, 250))
print("Day5 judge: live", r(136, 250), p(105, 250), "closed", p(60, 196), "disc", r(154, 250), "crash", r(42, 250))
print("Day5 replay: live", r(110, 250), p(87, 250), "closed", p(86, 196))
print("Day4 judge: live", r(142, 246), p(83, 246), "closed", p(73, 215), "disc", r(175, 246), "crash", r(40, 246))
print("Day3 judge: live", r(48, 160), p(41, 160), "closed", p(20, 68), "disc", r(50, 160), "crash", r(18, 160))
print("Day6 rep: ", r(212, 250), r(194, 250))
# groups
G = {"C_pyright_range": (6, 6), "C_tvt": (4, 15), "H_new": (12, 17), "N_class": (24, 9), "N_flow": (24, 25), "N_types": (24, 7), "N_wrap": (24, 9), "O_overload": (9, 11), "R_reserve": (24, 30), "fresh": (99, 43)}
for k, (a, b) in G.items():
    print(k, r(b, a))
print("N_* total", r(9 + 25 + 7 + 9, 96))
A = {"context_managers": (32, 22), "dunder_dispatch": (14, 18), "typevartuple_unpack": (7, 16), "generics_variance": (14, 15), "narrowing_user": (16, 15), "overloads": (17, 15), "callables": (17, 12), "abstract_classes": (18, 11), "typeddict": (15, 11), "narrowing_builtin": (3, 7), "paramspec_concatenate": (19, 7), "descriptors_properties": (6, 6), "gradual_any": (18, 5), "constructors_metaclasses": (8, 4), "enums_literals": (3, 3), "self_classmethods": (11, 3), "inheritance_mro": (14, 2), "final_classvar": (14, 0), "protocols": (4, 0)}
for k, (a, b) in A.items():
    print(k, r(b, a))
print("context+dunder", r(22 + 18, 46), "Day9 new areas", r(48, 50), "share live", p(40, 172))
print("Day10 live by kind share closed by CONFIG", p(12, 75))
print("tests growth", 730 - 144)
