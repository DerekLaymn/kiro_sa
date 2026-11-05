#!/bin/bash
S=/tmp/d7pd/gh_search.sh
bash $S /tmp/d7pd/gh_c2.out "microsoft/pyright" "Maximum call stack size exceeded|RangeError|descriptor decorated __get__|decorator __get__ descriptor|retainTypeAlias|stack overflow descriptor|infinite recursion descriptor|crash decorated method self|decorator without self class body"
bash $S /tmp/d7pd/gh_c4.out "microsoft/pyright" "descriptor __set__ inferred type|descriptor class access union|descriptor assignment __init__ inferred|overload __get__ instance None class access|descriptor declared type inference|descriptor self assignment inferred type|data descriptor class variable union"
bash $S /tmp/d7pd/gh_c1b.out "astral-sh/ty,astral-sh/ruff,microsoft/pyright" "try except assignment|except narrowing assignment|exception handler flow|unpack ValueError|binding try block|try block reachability|raise during assignment|definition in try block|except clause|try statement"
bash $S /tmp/d7pd/gh_c3.out "astral-sh/ty,astral-sh/ruff" "narrowing descriptor __set__|setter invalidate narrowing|property setter narrowing|attribute narrowing invalidated|narrowing mutated attribute|descriptor store narrowing"
bash $S /tmp/d7pd/gh_c5.out "astral-sh/ty,astral-sh/ruff" "sequence pattern Sequence[object]|match sequence pattern narrowing|case tuple pattern intersection|sequence pattern non-final class|match sequence pattern object|unsupported-operator match"
echo ALLSEARCHDONE > /tmp/d7pd/search.done
