#! /bin/bash

temp_file=$(mktemp --dry-run ./tmpfile.XXXXXX)

printf "temp_file=%s\n" "${temp_file}"

# Test that we can create the file and it contains what we expect
../vgr.py "temp.file=${temp_file}" <<EOF || echo "FAILED"
Print "\n--Output Overwrite Test"
Echo True
Exhibit arg.temp.file
Open Output arg.temp.file
Printf "{}", arg.temp.file
Close Output
Load arg.output From arg.temp.file
Exhibit arg.output
Assert arg.output == arg.temp.file
EOF

# Make sure overwrite protection is working
../vgr.py "temp.file=${temp_file}" \
    -e 'Print "\n--Output No Overwrite Test"' \
    -e 'Echo True' \
    -e 'Open Output arg.temp.file No Overwrite' \
    && echo "Overwrite protected FAILED"

# Test out appending
../vgr.py "temp.file=${temp_file}" <<EOF || echo "FAILED"
Print "\n--Output Append Test"
Echo True
Exhibit arg.temp.file
Open Output arg.temp.file Append
Printf "{}", arg.temp.file
Close Output
Load arg.output From arg.temp.file
Exhibit arg.output
# One copy from our first test, another from this one
Assert arg.output == (arg.temp.file * 2)
EOF

# Make sure only relative paths can be used
../vgr.py \
    -e 'Print "\n--Non-relative Path Test"' \
    -e 'Echo True; Verbose True;' \
    -e 'Open Output "../must-fail.txt"' \
    && echo "Overwrite protected FAILED"

rm -rf "$temp_file"

# Test mkdir -p like functionality
../vgr.py "temp.file=${temp_file}" \
    -e 'Print "\n--Create subdirs Test"; Open Output arg.temp.file + "/sub1/sub2/out.txt"' \
    || echo "Subdir creating FAILED"

ls -lR "$temp_file"

rm -rf "$temp_file"
mkdir "$temp_file"
touch "$temp_file/sub1"
ls -lR "$temp_file"

# Test file blocking dir creation
../vgr.py "temp.file=${temp_file}" \
    -e 'Print "\n--Blocking Test"; Open Output arg.temp.file + "/sub1/sub2/out.txt"' \
    && echo "Blocking File FAILED"

rm -rf "$temp_file"
