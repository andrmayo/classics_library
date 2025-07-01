# script to process librarything marc output, 
# by first converting to utf8 and then running mixedmarc.seperate_mixed_marc() on file

import pymarc
from pathlib import Path
from mixedmarc import separate_mixed_marc

src_file = Path("librarything_UMClassics.marc")
marc8_file, utf8_from64 = separate_mixed_marc(src_file, encoding="ISO-8859-1")

utf8_fromMarc8 = "from_marc8.marc"

with open(marc8_file, 'rb') as fh:
    reader = pymarc.MARCReader(fh, to_unicode=True, force_utf8=True, utf8_handling='ignore')

    with open(utf8_fromMarc8, 'wb') as outfile:
        writer = pymarc.MARCWriter(outfile)
        i = None
        for i, record in enumerate(reader):
            if record:
                writer.write(record)
            else:
                print(f"Skipped record {i}.")

        writer.close()

i = i + 1 if i else 0
print(f"Wrote {i} records to {utf8_fromMarc8} from {marc8_file}")
marc8_file.unlink()
utf8_comb = Path("librarything_UMClassics_all.marc")
utf8_comb.unlink(missing_ok=True)
print(f"deleted {marc8_file}. Combining records and writing to {utf8_comb}")
with open(utf8_from64, "r") as f1, open(utf8_comb, "a") as f2:
    for line in f1:
        f2.write(line)
with open(utf8_fromMarc8, "r") as f1, open(utf8_comb, "a") as f2:
    for line in f1:
        f2.write(line)

