from typing import Any, assert_type

# assert_type compares INFERRED types. Whether the inferred type of these unannotated call results keeps their
# Literal parts is left open by the typing spec (literal.rst): ty keeps them, mypy and pyright widen.
assert_type(slice(1234, None), "slice[int, Any, Any]")
assert_type(max(1, 2), int)
