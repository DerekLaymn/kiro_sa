def g() -> None:
    # ty reports the unbound read and reveals its error-recovery type (Unknown); mypy has no definite-assignment check
    # and reveals str. The reveal difference is not an inference difference; the unbound read is judged on its own.
    value: str
    reveal_type(value.upper())
