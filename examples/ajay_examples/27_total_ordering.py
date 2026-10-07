# area: inheritance_mro (synthesized methods)
# explores: functools.total_ordering synthesizes __ge__ etc.; sorted()/max() need SupportsRichComparison
from functools import total_ordering
from typing import reveal_type


@total_ordering
class Version:
    def __init__(self, major: int, minor: int) -> None:
        self.major, self.minor = major, minor

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Version) and (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other: "Version") -> bool:
        return (self.major, self.minor) < (other.major, other.minor)

    def __repr__(self) -> str:
        return f"v{self.major}.{self.minor}"


class Plain:
    pass


vs = [Version(1, 2), Version(1, 0), Version(2, 0)]
reveal_type(Version(1, 0) >= Version(0, 9))  # bool (synthesized)
reveal_type(sorted(vs))  # list[Version]
reveal_type(max(vs))  # Version
print(sorted(vs), max(vs), Version(1, 0) >= Version(0, 9))
try:
    sorted([Plain(), Plain()])  # expect-error: Plain does not support <
except TypeError as exc:
    print("runtime:", exc)
