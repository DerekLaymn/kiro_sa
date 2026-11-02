from typediff.kb import BY_ID

for i in ("UPSTREAM-MYPY-948", "TY-STRICT-EQUALITY", "TY-REDECLARATION", "TY-CHECK-NOT-IMPLEMENTED", "MYPY-OPTIONAL-CHECK", "TY-UNKNOWN-UNION"):
    e = BY_ID[i]
    print("==", i, e.auto, e.kinds)
    print(e.example)
