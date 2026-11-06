#!/usr/bin/env bash
# read-only tracker searches (gh search only); nothing is written on GitHub
for q in "overload __post_init__" "dataclass __post_init__ override InitVar" "__post_init__ overloaded incompatible with supertype dataclass"; do
  echo "== python/mypy: $q"
  gh search issues --repo python/mypy "$q" --limit 10 --json number,title,state 2>&1 | head -30
done
for q in "narrowing sequence pattern non-final class intersection" "match class pattern negation intersection list rest"; do
  echo "== astral-sh/ty: $q"
  gh search issues --repo astral-sh/ty "$q" --limit 10 --json number,title,state 2>&1 | head -30
done
echo "== astral-sh/ty#1578"
gh issue view 1578 --repo astral-sh/ty --json number,title,state,stateReason 2>&1 | head -10
