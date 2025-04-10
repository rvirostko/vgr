#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

set filename = "people.json"
set limit = 10

Printf "Reading from {}...", filename
Load people From File filename
Printf "{} records.\n", people.Length()

Printf "\nOriginal, first {}-\n", limit
Select age As "Age", last_name As "Last Name", first_name As "First Name"
    From Variable people As person
    Limit limit
    For Batch Template

Sort Variable people On age Into Variable people_by_age
Printf "\nBy Age, first {}-\n", limit
Select age As "Age", last_name As "Last Name", first_name As "First Name"
    From Variable people_by_age As person
    Where age Is Not None
    Limit limit
    For Batch Template

Sort Variable people On last_name, first_name Into Variable people_by_names
Printf "\nBy Name, first {}-\n", limit
Select last_name As "Last Name", first_name As "First Name", age As "Age"
    From Variable people_by_names As person
    Where last_name Is Not None
    Limit limit
    For Batch Template

Sort Variable people On age Unique On age Into Variable by_age

Set ages = []
ForEach item In by_age:
    Set age = item.age
    If age Is Not None:
        Set ages += [age]
    End
End
Print "\nAll ages from Sort/Unique on Age"
Print ages

Set ages = []
ForEach item In people:
    Set age = item.age
    If age Is Not None:
        Set ages += [age]
    End
End
Print "\nAll ages from raw data"
Print ages

Print "\nAll ages from raw data, sort/unique"
// <collection>.sort([<unique>[, <reverse>]])
Print ages.sort(True)

Print

EOF
