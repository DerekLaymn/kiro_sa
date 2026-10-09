# area: dataclasses
# explores: dataclass(order=True) comparisons, slots=True, frozen hashing, __match_args__, field(init=False)
from dataclasses import dataclass, field
from typing import reveal_type


@dataclass(order=True, frozen=True, slots=True)
class Card:
    rank: int
    suit: str = field(compare=False)
    label: str = field(init=False, default="card")


@dataclass
class Plain:
    x: int


cards = sorted([Card(3, "h"), Card(1, "s")])
reveal_type(cards)  # list[Card]
reveal_type(Card(1, "s") < Card(2, "h"))  # bool
reveal_type({Card(1, "s")})  # set[Card]: frozen dataclasses are hashable
reveal_type(Card.__match_args__)  # tuple[Literal["rank"], Literal["suit"]]
print(cards, Card(1, "s").label)
try:
    Plain(1) < Plain(2)  # expect-error: order=False, no __lt__
except TypeError as exc:
    print("runtime:", exc)
try:
    Card(1, "s", "x")  # expect-error: `label` has init=False
except TypeError as exc:
    print("runtime:", exc)
