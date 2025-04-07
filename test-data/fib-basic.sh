#! /bin/bash

../vgr.py "ofs=" <<EOF || echo "FAILED"

# Since we don't use ";" between print params to
# indicate "no space", it has been converted to
# "," and ofs has been set to nothing.

LET fib0 = 0
LET fib1 = 1
LET x = 0

PRINT "fib(", x, ") = ", fib0
LET x = x + 1
PRINT "fib(", x, ") = ", fib1
LET x = x + 1

DO WHILE x <= 8
    LET fib2 = fib0 + fib1
    PRINT "fib(", x, ") = ", fib2
    LET fib0 = fib1
    LET fib1 = fib2
    LET x = x + 1
LOOP

EOF
