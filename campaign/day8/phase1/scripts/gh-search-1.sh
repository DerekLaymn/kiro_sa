cd /home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa
q() { echo "### $*"; gh search issues --limit 8 "$@" --json repository,number,title,state,url --jq '.[] | "\(.state) \(.url) \(.title)"' 2>&1; sleep 3; }
q --repo astral-sh/ty "self annotation supertype of its class"
q --repo astral-sh/ty "annotated self type not a supertype"
q --repo astral-sh/ty "self Callable ParamSpec __init__"
q --repo astral-sh/ty "ParamSpec self annotated Callable"
q --repo astral-sh/ty "invalid self annotation"
q --repo astral-sh/ty "explicit self type validate"
q --repo astral-sh/ty "P@__init__"
q --repo astral-sh/ty "attribute assignment on self annotated Callable"
q --repo astral-sh/ty "unresolved-attribute self.x __init__ annotated self"
echo "### view 4899"; gh issue view 4899 --repo astral-sh/ty --json title,state,body --jq '"\(.state) \(.title)\n\(.body)"' 2>&1 | head -60
