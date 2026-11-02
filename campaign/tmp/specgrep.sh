#!/usr/bin/env bash
D=/home/derek/.cache/typediff/docs
ls $D | head -20
echo "#### LiteralString"
grep -rIl "LiteralString" $D | head -8
grep -rIh -i "LiteralString.*subtype\|subtype.*LiteralString\|LiteralString.*assignable\|LiteralString.*compatible" $D | head -8
echo "#### type[Any] / type"
grep -rIh -i "type\[Any\].*equivalent\|equivalent.*type\[Any\]\|bare .type.\|subtype of .type." $D | head -8
echo "#### bytes quotes"
grep -rIh -i "Literal\[b" $D | head -4
