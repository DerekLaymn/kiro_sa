import sys
from typing import reveal_type

if sys.version_info < (3, 8):
    legacy = 1
    reveal_type(legacy)
print("ok")
