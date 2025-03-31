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
Load mail_template
    With "form.txt"
    As Text

Print "Template loaded"

-- The file is actually an array of JSON objects, which is itself an object.
-- To use with Select, it has to be an array.
Load People
    With "people.json"
    As Json Object

Printf "{} total records\n", People.Length()

-- Use the passed in date (because we don't have date functions yet...)
-- for out output file. The overwrite option is the default.
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
Select first_name As "FNAME", last_name As "LNAME", email as "EMAIL"
    From Var People as person
    Where first_name Is Null
            Or email Is Null
    For CSV
Close Output

Print "Done."

EOF

rm form.txt
