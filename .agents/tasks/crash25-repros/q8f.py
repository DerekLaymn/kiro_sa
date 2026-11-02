class A:
    __new__: type["B"]

class B:
    __new__: type[A]

A()
