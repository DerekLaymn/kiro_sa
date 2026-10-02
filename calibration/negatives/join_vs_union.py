from typing import reveal_type

mixed = [1, "a"]
reveal_type(mixed)
pair = (1, "a") if len(mixed) > 1 else ("b", 2)
reveal_type(pair)
