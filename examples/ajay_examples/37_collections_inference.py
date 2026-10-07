# area: gradual_any (inference)
# explores: dict literal inference with int/float values, get/setdefault overloads, defaultdict, Counter,
# OrderedDict, dict union, empty-dict inference from later use
from collections import Counter, OrderedDict, defaultdict
from typing import reveal_type

prices = {"apple": 1.5, "pear": 2}
reveal_type(prices)  # dict[str, float]
reveal_type(prices.get("kiwi"))  # float | None
reveal_type(prices.get("kiwi", 0))  # float | int
reveal_type(prices.setdefault("fig", 3.0))  # float
groups: defaultdict[str, list[int]] = defaultdict(list)
groups["odd"].append(1)
reveal_type(groups["even"])  # list[int]
c = Counter("hello")
reveal_type(c.most_common(1))  # list[tuple[str, int]]
od = OrderedDict(a=1)
reveal_type(od.popitem())  # tuple[str, int]
merged = prices | {"plum": 4}
reveal_type(merged)  # dict[str, float]
empty = {}
empty["k"] = 1
reveal_type(empty)  # dict[str, int] (mypy) / dict[Unknown, Unknown] (ty)
print(prices, dict(groups), c.most_common(1), merged, empty)
prices["x"] = "cheap"  # expect-error: str is not float
