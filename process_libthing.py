# script to process librarything marc output, 
# by first converting to utf8 and then running mixedmarc.seperate_mixed_marc() on file

from os import sep
import pymarc
import sys
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

i = i if i else 0
print(f"Wrote {i+1} records to {utf8_fromMarc8} from {marc8_file}")
marc8_file.unlink()
print(f"deleted {marc8_file}")
