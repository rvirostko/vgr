#! /bin/bash

cat <<< "
-- TO : {1}
-- SUBJ: {2}
-- BODY
Dear {0},

Just wanted to say hello.
-- END " >form.txt

today=`date +"%Y-%m-%d"`
subj="Hello Again!"

# NOTE!
# If you use one of the flags (--debug et al) without an arg following it
# make sure you do so AFTER any user arguments. Otherwise it will eat the
# argument folliwing it.
../vgr.py \
    "today=${today}" \
    "subj=${subj}" \
<<EOF || echo "FAILED"

-- Check prereqs
-- Is empty checks for None, an empty string, or one composed only of spaces
Assert !arg.today.IsEmpty() : "You need to pass in the date for the output file"
Assert !arg.subj.IsEmpty() : "You need to pass in the email subject"

-- Load can guess the type based on the extension
-- but no harm in explicitly defining the type
Printf "Loading template..."
Load mail_template
    With "form.txt"
    As Text
Print " done."

-- The file is actually an array of JSON objects, which is itself an object.
-- To use with Select, it has to be an array.
Printf "Loading data..."
Load People
    With "people.json"
    As Json Object
Print " done."
Printf "{} total records\n", People.Length()

Printf "Sorting..."
Sort Var People
    By Asc Key last_name, Asc Key first_name
    Unique
Print " done."

Printf "First: {0}\n", People.FirstItem().ToJsonStr()
Printf "Last : {0}\n", People.LastItem().ToJsonStr()

-- Use the passed in date for out output file. The overwrite option is the default.
Open Output File arg.today + " - mail-output.txt" Overwrite
-- Use the template as a "printf" per person
-- Positionally args are first name, email, and the email subject.
-- We exclude people with incomplete information
Select mail_template.Format(first_name, email, "Hello Again!")
    From Var People As person
    Where first_name Is Not Null
            And email Is Not Null
    For Text Unicode
Close Output

Open Output File arg.today + " - skipped.csv" Overwrite
Select _.rowid as "ROW", first_name As "FNAME", last_name As "LNAME", email as "EMAIL"
    From Var People as person
    Where first_name Is Null
            Or email Is Null
    For CSV
Close Output

Print "Done."

EOF

rm form.txt
