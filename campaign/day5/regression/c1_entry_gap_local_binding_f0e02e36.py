# Day 5 morning regression: ty#4148 / mypy#22361 with the instance bound to a local first (seed-0bc328316b4c).
# ty 0.0.84 stack overflow and mypy 2.4.0 SIGSEGV; before the morning change `call_attr_own_type` missed `c = C(); c()`
# and both crashes stayed live. Covered by tests/test_upstream_day5_morning.py::test_local_bound_to_instance_and_called_closes_both_crashes.
class C:
    __call__: 'C'


def run() -> None:
    c = C()
    c()


try:
    run()
except TypeError:
    print('TypeError: C instance is not callable')
