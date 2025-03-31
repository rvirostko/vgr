#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

verbose true

set a to [1,2,3]
set b to a

print
set c to a + (b + 3)
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to (b - 3) + a
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to a + (b * 2)
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to a + (b / 2)
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to a + (b // 2)
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to a + (b % 2)
exhibit a, b, c
assert a == b && a != c && b != c

print
set c to a + (b ** 2)
exhibit a, b, c
assert a == b && a != c && b != c

EOF
