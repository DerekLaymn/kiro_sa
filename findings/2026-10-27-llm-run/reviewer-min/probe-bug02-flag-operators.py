import enum
from typing import reveal_type


class F(enum.Flag):
    R = 1
    W = 2


class I(enum.IntFlag):
    R = 1
    W = 2


reveal_type(F.R | F.W)
reveal_type(F.R & F.W)
reveal_type(F.R ^ F.R)
reveal_type(I.R | I.W)

b = F.R | F.W
if b is F.R:
    print("R")
elif b is F.W:
    print("W")
else:
    # Reachable at runtime (b is F.R|W). A type error here is invisible if the branch is "unreachable".
    reveal_type(b)
    print(1 + "bad")
