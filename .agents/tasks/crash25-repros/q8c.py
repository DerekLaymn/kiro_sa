class C:
    __new__: "Factory"

class Factory:
    __call__: type[C]

C()
