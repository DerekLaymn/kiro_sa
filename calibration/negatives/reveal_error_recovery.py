def g(a: int, b: str) -> None:
    # Both checkers report the unsupported `+` (no discrepancy there). ty then reveals its error-recovery type
    # (Unknown) while mypy keeps a concrete type (int). The reveal difference is not an inference difference.
    reveal_type(a + b)
