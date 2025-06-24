from pathlib import Path
from pymarc import MARCReader
from csv_converter import to_csv, to_marc

# using PGA-Australiana.mrc test ability to convert to csv, and backconvert to the exact same marc file.
src_path = Path("./testing/PGA-Australiana.mrc")
dest = src_path.parent / f"{src_path.stem}.csv"
dest.unlink(missing_ok=True)
to_csv(src_path, dest)
newmarc_dest = dest.parent / f"{dest.stem}_fromMARC.mrc"
newmarc_dest.unlink(missing_ok=True)
to_marc(dest, newmarc_dest)

def test_2csv():
    # check that csv file has the right numer of lines
    record_count = 0
    with open(src_path, "rb") as f:
        reader = MARCReader(f)
        for record in reader:
            record_count += 1
    csv_count = 0
    with open(dest, "r") as f:
        for line in f:
            csv_count += 1
    # note that csv file should have one more line than marc file has records, because of header line
    assert csv_count == record_count + 1, f"csv_count is {csv_count} and record_count is {record_count}"

def test_2marc():
    with open(src_path, "rb") as f1, open(newmarc_dest, "rb") as f2:
        reader1 = MARCReader(f1)
        reader2 = MARCReader(f2)
        for line1, line2 in zip(reader1, reader2):
            if line1 or line2: 
                assert line1 and line2
                dict1 = line1.as_dict()
                dict2 = line2.as_dict()
                for key in dict1:
                    if key == "leader":
                        dict1[key] = dict1[key][:9] + dict2[key][9] + dict1[key][10:]
                    assert dict1[key] == dict2[key], f"line1 is{line1}; \n line2 is {line2}"
