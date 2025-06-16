from pathlib import Path
from pymarc import MARCReader
from csv_converter import to_csv, to_marc

# using PGA-Australiana.mrc test ability to convert to csv, and backconvert to the exact same marc file.
src_path = Path("./PGA-Australiana.mrc")
dest = src_path.parent / f"{src_path.name.split('.')[0]}.csv"

def test_2csv():
    to_csv(src_path, dest)
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

    
