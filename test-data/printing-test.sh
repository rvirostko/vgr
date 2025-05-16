#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

Echo False
Verbose False
Debug False

set a = 5
set b = 10
set c = 15

# Generates nothing
Print "---Nothing between these lines---"
Printf;
Printf ""
Printf "", a
Printf "", a, b
Print "---Nothing between these lines---"

Print;

Print "---Two blank lines---"
Printf "\n"
Printf "{}", "\n"
Print "---Two blank lines---"

Print;

Print "---Two identical lines---"
Printf "{} > {}", a, b
Printf " && "
Printf "{} < {}", b, c
Printf "{}", arg.ors
Printf "{0} > {1} && {1} < {2}\n", a, b, c
Print "---Two identical lines---"

set rs_fmt = "\n---{}\n---OFS={}, ORS={}\n"
Printf rs_fmt, "Defaults:", arg.ofs.repr(), arg.ors.repr()
Print a, b, c
Printf "\n"

set arg.ofs = " | "
set arg.ors = " |\n"

Printf rs_fmt, "Overrides:", arg.ofs.repr(), arg.ors.repr()
Print a, b, c
Printf "\n"

set arg.ofs = NONE
set arg.ors = NONE

Printf rs_fmt, "Unset:", arg.ofs.repr(), arg.ors.repr()
Print a, b, c
Printf "\n"

EOF
