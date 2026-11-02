# area: enums_literals
# origin: python/mypy check-expressions.test [case testIntLiteral]
a = 0
b: A
if int():
    b = 1 # E: Incompatible types in assignment (expression has type "int", variable has type "A")
if int():
    a = 1
class A:
    pass

