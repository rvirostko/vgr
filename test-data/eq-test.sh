#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

# Test out casting for comparisons
# Test out transitive property for equality
# Test out printf syntax
# int, float, str, and array

Echo False
Verbose False
Debug False

-- Generate our "threes" data
    set t.three_int = 3
    set t.three_float = t.three_int.float()
    set t.three_str = t.three_int.str()
    set t.three_pad_str = " " + t.three_str + " "
    set t.array1 = [t.three_int, t.three_float, t.three_str]
    set t.array2 = [t.three_str, t.three_int, t.three_float]

-- Load the data into testing slots
    Set c1 = t.three_int
    Set c2 = t.three_float
    Set c3 = t.three_str
    Set c4 = t.three_pad_str
    -- This is for output "columns"
    Set fmt = "\t{1} {0} {2} -> {3}"
    Set vals = ["2", "3"]
    Set fmt4 = fmt.append(
        fmt.ReplaceStr(vals, ["4", "5"]),
        fmt.ReplaceStr(vals, ["6", "7"]),
        fmt.ReplaceStr(vals, ["8", "9"]),
        "\n")
    Set fmt = fmt + "\n"
    Set rfmt = "\t{2} {0} {1} -> {3}"
    Set rfmt4 = rfmt.append(
        rfmt.ReplaceStr(vals, ["4", "5"]),
        rfmt.ReplaceStr(vals, ["6", "7"]),
        rfmt.ReplaceStr(vals, ["8", "9"]),
        "\n")

-- Int to other values
    Set v = t.three_int
    Printf "\"{}\" tests-\n", v.class()
    Printf fmt4, "==", v.repr(), c1.repr(), v == c1, c2.repr(), v == c2, c3.repr(), v == c3, c4.repr(), v == c4
    Printf rfmt4, "==", v.repr(), c1.repr(), c1 == v, c2.repr(), c2 == v, c3.repr(), c3 == v, c4.repr(), c4 == v
    Printf fmt4, "<", v.repr(), c1.repr(), v < c1, c2.repr(), v < c2, c3.repr(), v < c3, c4.repr(), v < c4
    Printf fmt4, ">", v.repr(), c1.repr(), v > c1, c2.repr(), v > c2, c3.repr(), v > c3, c4.repr(), v > c4
    Printf fmt4, "<=", v.repr(), c1.repr(), v <= c1, c2.repr(), v <= c2, c3.repr(), v <= c3, c4.repr(), v <= c4
    Printf fmt4, ">=", v.repr(), c1.repr(), v >= c1, c2.repr(), v >= c2, c3.repr(), v >= c3, c4.repr(), v >= c4
    Print

-- Float to other values
    Set v = t.three_float
    Printf "\"{}\" tests-\n", v.class()
    Printf fmt4, "==", v.repr(), c1.repr(), v == c1, c2.repr(), v == c2, c3.repr(), v == c3, c4.repr(), v == c4
    Printf rfmt4, "==", v.repr(), c1.repr(), c1 == v, c2.repr(), c2 == v, c3.repr(), c3 == v, c4.repr(), c4 == v
    Printf fmt4, "<", v.repr(), c1.repr(), v < c1, c2.repr(), v < c2, c3.repr(), v < c3, c4.repr(), v < c4
    Printf fmt4, ">", v.repr(), c1.repr(), v > c1, c2.repr(), v > c2, c3.repr(), v > c3, c4.repr(), v > c4
    Printf fmt4, "<=", v.repr(), c1.repr(), v <= c1, c2.repr(), v <= c2, c3.repr(), v <= c3, c4.repr(), v <= c4
    Printf fmt4, ">=", v.repr(), c1.repr(), v >= c1, c2.repr(), v >= c2, c3.repr(), v >= c3, c4.repr(), v >= c4
    Print

-- In this case the str/pad_str will mismatch
    Set v = t.three_str
    Printf "\"{}\" tests-\n", v.class()
    Printf fmt4, "==", v.repr(), c1.repr(), v == c1, c2.repr(), v == c2, c3.repr(), v == c3, c4.repr(), v == c4
    Printf rfmt4, "==", v.repr(), c1.repr(), c1 == v, c2.repr(), c2 == v, c3.repr(), c3 == v, c4.repr(), c4 == v
    Printf fmt4, "<", v.repr(), c1.repr(), v < c1, c2.repr(), v < c2, c3.repr(), v < c3, c4.repr(), v < c4
    Printf fmt4, ">", v.repr(), c1.repr(), v > c1, c2.repr(), v > c2, c3.repr(), v > c3, c4.repr(), v > c4
    Printf fmt4, "<=", v.repr(), c1.repr(), v <= c1, c2.repr(), v <= c2, c3.repr(), v <= c3, c4.repr(), v <= c4
    Printf fmt4, ">=", v.repr(), c1.repr(), v >= c1, c2.repr(), v >= c2, c3.repr(), v >= c3, c4.repr(), v >= c4
    Set v = t.three_pad_str
    Printf fmt4, "==", v.repr(), c1.repr(), v == c1, c2.repr(), v == c2, c3.repr(), v == c3, c4.repr(), v == c4
    Printf rfmt4, "==", v.repr(), c1.repr(), c1 == v, c2.repr(), c2 == v, c3.repr(), c3 == v, c4.repr(), c4 == v
    Printf fmt4, "<", v.repr(), c1.repr(), v < c1, c2.repr(), v < c2, c3.repr(), v < c3, c4.repr(), v < c4
    Printf fmt4, ">", v.repr(), c1.repr(), v > c1, c2.repr(), v > c2, c3.repr(), v > c3, c4.repr(), v > c4
    Printf fmt4, "<=", v.repr(), c1.repr(), v <= c1, c2.repr(), v <= c2, c3.repr(), v <= c3, c4.repr(), v <= c4
    Printf fmt4, ">=", v.repr(), c1.repr(), v >= c1, c2.repr(), v >= c2, c3.repr(), v >= c3, c4.repr(), v >= c4
    Print

-- Make sure we have symetry with array
    Set v = t.array1; Set w = t.array2
    Printf "\"{}\"/\"{}\" tests-\n", v.type(), w.type()
    Printf fmt, "==", v.repr(), w.repr(), v == w
    Printf fmt, "==", w.repr(), v.repr(), w == v
    printf fmt, "<", w.repr(), v.repr(), w < v
    printf fmt, ">", w.repr(), v.repr(), w > v
    printf fmt, "<=", w.repr(), v.repr(), w <= v
    printf fmt, "<=", w.repr(), v.repr(), w >= v
    Print

-- Try out asserts to check these
    Assert (v == t.three_int) == False : "Invalid array distribution for equals"
    Assert (t.three.float == v) == False : "Invaid array distribution for equals"

EOF