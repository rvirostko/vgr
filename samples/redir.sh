#! /bin/bash

temp_file=$(mktemp --dry-run ./tmpfile.XXXXXX)

printf "temp_file=%s\n" "${temp_file}"
export temp_file

# Test that we can create the file and it contains what we expect
../vgr.py <<EOF || echo "FAILED"
Print "\n--Output Overwrite Test"

Echo True
Exhibit env.temp_file
Open Output env.temp_file
Printf "{}", env.temp_file
Close Output
Load arg.output From env.temp_file
Exhibit arg.output
Assert arg.output == env.temp_file
EOF

# Make sure overwrite protection is working
../vgr.py \
    -e 'Print "\n--Output No Overwrite Test"' \
    -e 'Echo True' \
    -e 'Open Output env.temp_file No Overwrite' \
    && echo "Overwrite protected FAILED"

# Test out appending
../vgr.py <<EOF || echo "FAILED"
Print "\n--Output Append Test"
Echo True
Exhibit env.temp_file
Open Output env.temp_file Append
Printf "{}", env.temp_file
Close Output
Load arg.output From env.temp_file
Exhibit arg.output
# One copy from our first test, another from this one
Assert arg.output == (env.temp_file * 2)
EOF

# Make sure only relative paths can be used
../vgr.py \
    -e 'Print "\n--Non-relative Path Test"' \
    -e 'Echo True; Verbose True;' \
    -e 'Open Output "../must-fail.txt"' \
    && echo "Overwrite protected FAILED"

rm -rf "$temp_file"

# Test mkdir -p like functionality
../vgr.py \
    -e 'Print "\n--Create subdirs Test"; Open Output env.temp_file + "/sub1/sub2/out.txt"' \
    || echo "Subdir creating FAILED"

ls -lR "$temp_file"

rm -rf "$temp_file"
mkdir "$temp_file"
touch "$temp_file/sub1"
ls -lR "$temp_file"

# Test file blocking dir creation
../vgr.py \
    -e 'Print "\n--Blocking Test"; Open Output env.temp_file + "/sub1/sub2/out.txt"' \
    && echo "Blocking File FAILED"

rm -rf "$temp_file"
