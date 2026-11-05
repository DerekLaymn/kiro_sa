#!/bin/bash
# read-only gh searches for the mypy Hashable / __eq__ candidate (H1)
q() { # repo, type(issues|prs), query
  echo "##### [$2] $1 :: $3"
  gh search "$2" --repo "$1" --limit 15 --json number,title,state,url -q '.[] | "\(.number)\t\(.state)\t\(.title)"' -- "$3" 2>&1 | head -20
}
for p in "Hashable" "Hashable __eq__" "Hashable __hash__" "unhashable" "__hash__ None" "__hash__ = None" "implicit __hash__" "__eq__ without __hash__" "hashable protocol" "unhashable type" "Hashable dataclass" "hash() unhashable" "set of unhashable" "dict key unhashable" "mutable dataclass hashable" "__eq__ unhashable" "defines __eq__ but not __hash__" "eq=True hashable"; do
  q python/mypy issues "$p"
done
for p in "Hashable" "__hash__" "unhashable" "__eq__ __hash__" "hashable protocol"; do
  q python/mypy prs "$p"
done
