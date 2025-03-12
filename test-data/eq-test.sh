#! /bin/bash

../vgr.py --echo <<EOF || echo "FAILED"

# Test out casting for comparisons
# Test out transitive property for equality
# int, float, str, and array

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
    Set fmt = "\t{} == {} -> {}"
    Set fmt4 = fmt * 4

-- Int to other values
    Set v = t.three_int
    Printf "\"{}\" tests-", v.class()
    Printf fmt4, v.repr(), c1.repr(), v == c1, v.repr(), c2.repr(), v == c2, v.repr(), c3.repr(), v == c3, v.repr(), c4.repr(), v == c4
    Printf fmt4, c1.repr(), v.repr(), c1 == v, c2.repr(), v.repr(), c2 == v, c3.repr(), v.repr(), c3 == v, c4.repr(), v.repr(), c4 == v
    Printf fmt4.replacestr("==", "<"), v.repr(), c1.repr(), v < c1, v.repr(), c2.repr(), v < c2, v.repr(), c3.repr(), v < c3, v.repr(), c4.repr(), v < c4
    Printf fmt4.replacestr("==", ">"), v.repr(), c1.repr(), v > c1, v.repr(), c2.repr(), v > c2, v.repr(), c3.repr(), v > c3, v.repr(), c4.repr(), v > c4
    Printf fmt4.replacestr("==", "<="), v.repr(), c1.repr(), v <= c1, v.repr(), c2.repr(), v <= c2, v.repr(), c3.repr(), v <= c3, v.repr(), c4.repr(), v <= c4
    Printf fmt4.replacestr("==", ">="), v.repr(), c1.repr(), v >= c1, v.repr(), c2.repr(), v >= c2, v.repr(), c3.repr(), v >= c3, v.repr(), c4.repr(), v >= c4
    Print

-- Float to other values
    Set v = t.three_float
    Printf "\"{}\" tests-", v.class()
    Printf fmt4, v.repr(), c1.repr(), v == c1, v.repr(), c2.repr(), v == c2, v.repr(), c3.repr(), v == c3, v.repr(), c4.repr(), v == c4
    Printf fmt4, c1.repr(), v.repr(), c1 == v, c2.repr(), v.repr(), c2 == v, c3.repr(), v.repr(), c3 == v, c4.repr(), v.repr(), c4 == v
    Printf fmt4.replacestr("==", "<"), v.repr(), c1.repr(), v < c1, v.repr(), c2.repr(), v < c2, v.repr(), c3.repr(), v < c3, v.repr(), c4.repr(), v < c4
    Printf fmt4.replacestr("==", ">"), v.repr(), c1.repr(), v > c1, v.repr(), c2.repr(), v > c2, v.repr(), c3.repr(), v > c3, v.repr(), c4.repr(), v > c4
    Printf fmt4.replacestr("==", "<="), v.repr(), c1.repr(), v <= c1, v.repr(), c2.repr(), v <= c2, v.repr(), c3.repr(), v <= c3, v.repr(), c4.repr(), v <= c4
    Printf fmt4.replacestr("==", ">="), v.repr(), c1.repr(), v >= c1, v.repr(), c2.repr(), v >= c2, v.repr(), c3.repr(), v >= c3, v.repr(), c4.repr(), v >= c4
    Print

-- In this case the str/pad_str will mismatch
    Set v = t.three_str
    Printf "\"{}\" tests-", v.class()
    Printf fmt * 4, v.repr(), c1.repr(), v == c1, v.repr(), c2.repr(), v == c2, v.repr(), c3.repr(), v == c3, v.repr(), c4.repr(), v == c4
    Printf fmt * 4, c1.repr(), v.repr(), c1 == v, c2.repr(), v.repr(), c2 == v, c3.repr(), v.repr(), c3 == v, c4.repr(), v.repr(), c4 == v
    Printf fmt4.replacestr("==", "<"), v.repr(), c1.repr(), v < c1, v.repr(), c2.repr(), v < c2, v.repr(), c3.repr(), v < c3, v.repr(), c4.repr(), v < c4
    Printf fmt4.replacestr("==", ">"), v.repr(), c1.repr(), v > c1, v.repr(), c2.repr(), v > c2, v.repr(), c3.repr(), v > c3, v.repr(), c4.repr(), v > c4
    Printf fmt4.replacestr("==", "<="), v.repr(), c1.repr(), v <= c1, v.repr(), c2.repr(), v <= c2, v.repr(), c3.repr(), v <= c3, v.repr(), c4.repr(), v <= c4
    Printf fmt4.replacestr("==", ">="), v.repr(), c1.repr(), v >= c1, v.repr(), c2.repr(), v >= c2, v.repr(), c3.repr(), v >= c3, v.repr(), c4.repr(), v >= c4
    Set v = t.three_pad_str
    Printf fmt4, v.repr(), c1.repr(), v == c1, v.repr(), c2.repr(), v == c2, v.repr(), c3.repr(), v == c3, v.repr(), c4.repr(), v == c4
    Printf fmt4, c1.repr(), v.repr(), c1 == v, c2.repr(), v.repr(), c2 == v, c3.repr(), v.repr(), c3 == v, c4.repr(), v.repr(), c4 == v
    Printf fmt4.replacestr("==", "<"), v.repr(), c1.repr(), v < c1, v.repr(), c2.repr(), v < c2, v.repr(), c3.repr(), v < c3, v.repr(), c4.repr(), v < c4
    Printf fmt4.replacestr("==", ">"), v.repr(), c1.repr(), v > c1, v.repr(), c2.repr(), v > c2, v.repr(), c3.repr(), v > c3, v.repr(), c4.repr(), v > c4
    Printf fmt4.replacestr("==", "<="), v.repr(), c1.repr(), v <= c1, v.repr(), c2.repr(), v <= c2, v.repr(), c3.repr(), v <= c3, v.repr(), c4.repr(), v <= c4
    Printf fmt4.replacestr("==", ">="), v.repr(), c1.repr(), v >= c1, v.repr(), c2.repr(), v >= c2, v.repr(), c3.repr(), v >= c3, v.repr(), c4.repr(), v >= c4
    Print

-- Make sure we have symetry with array
    Set v = t.array1; Set w = t.array2
    Printf "\"{}\"/\"{}\" tests-", v.type(), w.type()
    Printf fmt, v.repr(), w.repr(), v == w
    Printf fmt, w.repr(), v.repr(), w == v
    printf fmt.replacestr("==", "<"), w.repr(), v.repr(), w < v
    printf fmt.replacestr("==", ">"), w.repr(), v.repr(), w > v
    printf fmt.replacestr("==", "<="), w.repr(), v.repr(), w <= v
    printf fmt.replacestr("==", "<="), w.repr(), v.repr(), w >= v
    Print

-- Try out asserts to check these
Assert (v == t.three_int) == False : "Invalid array distribution for equals"
Assert (t.three.float == v) == False : "Invaid array distribution for equals"

EOF