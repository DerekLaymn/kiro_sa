class Meta(type):
    __call__: type["C"]

class C(metaclass=Meta): ...

C()
