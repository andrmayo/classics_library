import sys
from pathlib import Path

from csvconv import to_csv
from marccsv import CSVReader

if len(sys.argv) == 1:
    msg = "Must pass in two files, either marc or csv representing marc"
    sys.exit(msg)
file1 = Path(sys.argv[1])
file2 = Path(sys.argv[2])

csv_files = []

for file in (file1, file2):
    if file.suffix == ".csv":
        csv_files.append(file)
    else:
        dest = file.with_suffix(".csv")
        to_csv(file, dest)
        csv_files.append(dest)

csv1, csv2 = CSVReader(csv_files[0]), CSVReader(csv_files[1])
comp_fields = ["050", "090", "245"] # tags of field to use to compare records in either field, in order of precedence
if len(csv1.records) > len(csv2.records):
    csv1, csv2 = csv2, csv1
    file1, file2 = file2, file1

def _clean_strings(string_val):
    if not isinstance(string_val, str):
        return string_val
    return string_val.replace(" ", "")

for i, comp_field in enumerate(comp_fields):
    if comp_field not in csv1.records.columns and comp_field not in csv2.records.columns:
        del comp_fields[i]
        continue
    csv1.records[comp_field] = csv1.records[comp_field].apply(_clean_strings)
    csv2.records[comp_field] = csv2.records[comp_field].apply(_clean_strings)
# csv1 should now have fewer records than csv1, ditto for file1 and file2
# now, compare records by control number
drop_indices1 = []
drop_indices2 = []
for row in csv1.records.iterrows():
    record = row[1]
    match = None
    for comp_field in comp_fields:
        match = csv2.records[csv2.records[comp_field] == record[comp_field]]
        if not match.empty:
            break
    if match is not None and not match.empty:
        drop_indices1.append(row[0])
        drop_indices2.append(match.index[0])

csv1.records.drop(drop_indices1, inplace=True)
csv2.records.drop(drop_indices2, inplace=True)

print(f"There are {len(csv1.records)} records in {file1} not contained in {file2}")
print(f"There are {len(csv2.records)} records in {file2} not contained in {file1}")

# now all the records in csv1 are not in csv2, and vice versa
print(f"Records in {file2} and not {file1}:")
for i, row in enumerate(csv2.records.iterrows()):
    print(f"{csv2.get_record(i).as_marc().decode()}")

sys.exit()

print(f"Records in {file1} and not {file2}:")
for i, row in enumerate(csv1.records.iterrows()):
    print(f"{csv1.get_record(i).as_marc().decode()}")
