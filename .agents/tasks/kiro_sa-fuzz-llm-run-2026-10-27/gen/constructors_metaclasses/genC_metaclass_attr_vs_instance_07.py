from typing import reveal_type


class Meta(type):
    count = 0

    def bump(cls) -> int:
        Meta.count += 1
        return Meta.count


class K(metaclass=Meta):
    pass


reveal_type(K.count)
reveal_type(K.bump())
print(K.bump())
k = K()
try:
    print(k.count)  # type: ignore
except AttributeError:
    print("AttributeError")
try:
    k.bump()  # type: ignore
except AttributeError:
    print("AttributeError")
