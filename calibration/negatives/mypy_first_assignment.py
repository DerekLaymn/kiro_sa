# mypy gives an undeclared variable ONE type, fixed at its first assignment (common_issues: "Redefinitions with
# incompatible types"); ty and pyright infer the union of the assigned types. Declared variables are not covered.
def f(flag: bool) -> None:
    y = 1
    if flag:
        y = "s"
    print(y)


count = 0
count = "zero"
