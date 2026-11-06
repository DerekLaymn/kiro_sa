class Box:
    def label(self) -> str:
        return "x"


def run(b: Box) -> None:
    assert b.label() == 4
    b.no_such_attribute
    reveal_type(b)
