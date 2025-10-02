#! /bin/sh

# Example of passing in values via the command line
today=`date +"%Y-%m-%d"`
subj="Hello Again!"

python3 -m vgr \
    "today=${today}" \
    "subj=${subj}" \
<<EOF || echo "FAILED"

Set data_file To "people.json"
Assert data_file.FileExists() :
    "Please run from the same directory where {} is stored", data_file

Set form_file To "form.txt"
Open Output File form_file
Print """
-- TO : {1}
-- SUBJ: {2}
-- BODY
Dear {0},

Just wanted to say hello.
-- END
"""
Close Output

-- Check prereqs
-- Is empty checks for None, an empty string, or one composed only of spaces
Assert arg.today.IsNotEmpty() : "You need to pass in the date for the output file"
Assert arg.subj.IsNotEmpty() : "You need to pass in the email subject"

-- Load can guess the type based on the extension
-- but no harm in explicitly defining the type
Printf "Loading template..."
Load mail_template
    With form_file
    As Text
Set mail_template = mail_template.Strip()
Print " done."

-- The file is actually an array of JSON objects, which is itself an object.
-- To use with Select, it has to be an array.
Printf "Loading data..."
Load People
    With data_file
    As Json Object
Print " done."
Printf "{} total records\n", People.Length()

Printf "Sorting..."
Sort People
    By Asc Key last_name,
       Asc Key first_name
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
    From People As person
    Where first_name Is Not Null
           And email Is Not Null
    For Text Unicode
Close Output

Open Output File arg.today + " - skipped.csv" Overwrite
Select \$rowid as "ROW", first_name As "FNAME", last_name As "LNAME", email as "EMAIL"
    From People as person
    Where first_name Is Null
            Or email Is Null
    For CSV
Close Output

Assert form_file.RemoveFile().FirstItem() : "Could not delete {}", form_file

Print "Done."

EOF
