echo "--- jq form, one word"
timeout 60 gh search issues "narrowing" --repo astral-sh/ty --limit 3 --json number,title,state,updatedAt --jq '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' 2>&1 | head
echo "--- two words"
timeout 60 gh search issues "overload union" --repo astral-sh/ty --limit 5 --json number,title,state,updatedAt --jq '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' 2>&1 | head
echo "--- four words"
timeout 60 gh search issues "overload union expansion typevar" --repo astral-sh/ty --limit 5 --json number,title,state,updatedAt --jq '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' 2>&1 | head
echo "--- three words"
timeout 60 gh search issues "overload union expansion" --repo astral-sh/ty --limit 5 --json number,title,state,updatedAt --jq '.[] | "\(.number)\t\(.state)\t\(.updatedAt[0:10])\t\(.title)"' 2>&1 | head
