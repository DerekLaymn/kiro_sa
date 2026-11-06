def label(tag: str, name: str, width: int) -> str:
    return name.ljust(width)


label("t2", 6)
label("t2", "n")
label(1, 6)
label("t2", 6, 7, 8)
