#!/usr/bin/env bash
D=/home/derek/.cache/typediff/docs
echo "#### LiteralString assignable (file + context)"
grep -rIn -B3 -A4 "is assignable to the type" $D/spec | head -30
echo "#### equivalent to type[Any]"
grep -rIn -B6 -A3 "equivalent to ..type\[Any\]" $D/spec | head -30
echo "#### type[C] subtype of type"
grep -rIn -i "type\[C\].*type\b" $D/spec | head -8
grep -rIn -i "every .type\[.*\]. is a subtype\|is a subtype of .type" $D/spec | head -8
