#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

// NB: Had to add commas between items in Display.
//     VGR grammar doesn't like a space separated list
MOVE 0 TO X
PERFORM UNTIL X > 8
    IF X < 2
        DISPLAY "fib(", X, ") = ", X
    ELSE
        MOVE 0 TO A
        MOVE 1 TO B
        MOVE 2 TO I
        PERFORM UNTIL I > X
            ADD A TO B GIVING T
            MOVE B TO A
            MOVE T TO B
            ADD 1 TO I
        END-PERFORM
        DISPLAY "fib(", X, ") = ", B
    END-IF
    ADD 1 TO X
END-PERFORM
STOP RUN

EOF
