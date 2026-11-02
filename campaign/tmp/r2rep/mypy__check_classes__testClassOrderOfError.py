# area: gradual_any
# origin: python/mypy check-classes.test [case testClassOrderOfError]
class A:
    x = 1
class B(A):
    x = "a"  # E: Incompatible types in assignment (expression has type "str", base class "A" defined the type as "int")
class C(B):
    x = object()  # E: Incompatible types in assignment (expression has type "object", base class "B" defined the type as "str")

