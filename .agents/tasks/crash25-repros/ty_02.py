class A1:
class A2:
class A3:
class A4:
class A5:
class A6:
class A7:
class A8:
class A9:
class A10:
class A11:
class A12:
class A13:
class A14:
class A15:
class A16:
class B1:
class B2:
class B3:
class B4:
class B5:
class B6:
class B7:
class B8:
class B9:
class B10:
class B11:
class B12:
class B13:
class B14:
class B15:
class B16:
type UA = (
    A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 | A11 | A12 | A13 | A14 | A15 | A16
)
type UB = (
    B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B9 | B10 | B11 | B12 | B13 | B14 | B15 | B16
)
def test(a: UA, b: UB) -> bool:
    t = a, b
    match t:
        case A1(), B1():
        case A9(), B9():
        case A10(), B10():
        case A11(), B11():
        case A12(), B12():
        case A13(), B13():
        case A14(), B14():
        case A15(), B15():
        case A16(), B16():
        case _:
            reveal_type(t, expected_text="Any")
