#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

// Derived from 'C' code,
// but not looking very much like it...
fib0 = 0;
fib1 = 1;

// Print the first two Fibonacci numbers (0 and 1)
printf "fib(0) = {}\n", fib0;
printf "fib(1) = {}\n", fib1;

// Calculate and display Fibonacci numbers from fib(2) to fib(8)
x = 2;
while (x <= 8):
    fib = fib0 + fib1;
    printf "fib({}) = {}\n", x, fib ;
    fib0 = fib1;
    fib1 = fib;
    x = x + 1;
end;

EOF
