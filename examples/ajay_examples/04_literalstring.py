# area: enums_literals
# explores: PEP 675 LiteralString - literals and literal-derived strings are accepted, arbitrary str is not
from typing import LiteralString, reveal_type


def run_query(sql: LiteralString) -> str:
    return sql


def build(table: LiteralString, user_input: str) -> None:
    q = "SELECT * FROM " + table
    reveal_type(q)  # LiteralString (or a literal)
    print(run_query(q))
    print(run_query(f"SELECT {table}"))  # f-string of LiteralStrings is LiteralString
    print(run_query(", ".join([table, table])))
    run_query(user_input)  # expect-error: str is not LiteralString
    run_query(q + user_input)  # expect-error


build("users", "1; DROP TABLE users")
