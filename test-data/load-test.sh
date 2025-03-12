#! /bin/bash

../vgr.py --echo <<EOF  || echo "FAILED"

# "Modern" style comments
    // C-style comments
    -- SQL style comments

# This file contains a single JSON object
# The Select For JSON Root <root> can be used to produce a file like this
Load test.json.obj From "in.json"
Exhibit test.json.obj
Print

# This file has a JSON array, suitable for use with Lookup()
# The Select For JSON produces this by default
Load test.json.arr From "array.json"
Exhibit test.json.arr
Print

# This file has a JSON object per row.
# The Select For JSON No Array Wrapper produces this
# The file can be used here or prefiltered by grep before being used
Load test.json.objs From "objs.txt" JSON Object Per Line
Exhibit test.json.objs
Print

# CSV is CSV...
# The lib used to load these files don't like extra spaces between
# columns and add those space (and quotes!) to the column data
# This also uses some syntactic sugar and using expressions
Set csv_file_name:="objs"
Load test.csv.arr From File csv_file_name + ".csv" CSV
Exhibit test.csv.arr
# Just a test to make sure that Printf works just like Print w/o args
Printf

# Lookup values are not super flexible...
Print test.csv.arr.Lookup("idx", 3)
Print test.csv.arr.Lookup("idx", 3.0)
# ...there has to be some level of type agreement
# This is like <int> == " 3 ", with lvalue driving the comparison type
## TODO Not working? fix?
Print test.csv.arr.Lookup("idx", " 3 ")
Print test.csv.arr.Lookup("fname", "Justin")
Print

# Order depends upon what you ask for, but unless you have a datatype error
# You will always get back an array, even if empty
Print test.csv.arr.Lookup("idx", 0, 3)
Print test.csv.arr.Lookup("idx", 3, 0)
Print test.csv.arr.Lookup("idx", [3, 0])
Print

Print test.csv.arr.Lookup("lname", "Smith")
Print test.csv.arr.Lookup("lname", "Heap")
Printf "Heap's idx={}", test.csv.arr.Lookup("lname", "Heap").FirstItem().idx

# You could use Print or Printf here, as long as Printf's
# format string doesn't reference a parameter
Printf "\nDone"

EOF