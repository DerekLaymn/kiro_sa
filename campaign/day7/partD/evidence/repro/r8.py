class Desc:
    __get__: "Desc"


class Host:
    attr = Desc()


h = Host()
h.attr
