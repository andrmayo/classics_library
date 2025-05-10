# script to convert between csv and marc formats

import csv
import sys
from pathlib import Path
from typing import Union

from pymarc import MARCReader
from pymarc import exceptions as exc

from utils import decode_64


def to_csv(filepath: Union[str, Path], dest: Union[str, Path]) -> None:
    with open(filepath, "rb") as f:
        reader = MARCReader(f)

        csv_records = []
        # every entry should have a leader as first line,
        # and leader is not include in marc_record.get_fields, so handled separately
        marc_tags = ["LDR"]

        for i, marc_record in enumerate(reader):
            csv_record = {}
            if not marc_record:
                print(f"warning: record {i} skipped")
            if marc_record:
                leader = marc_record.leader.leader
                csv_record["LDR"] = leader
                for marc_field in marc_record.get_fields():
                    if marc_field.tag not in marc_tags:
                        marc_tags.append(marc_field.tag)
                    csv_record[marc_field.tag] = marc_field.value()
                csv_records.append(csv_record)
            elif isinstance(reader.current_exception, exc.FatalReaderError):
                # data file format error
                # reader will raise StopIteration
                print(reader.current_exception)
                print(reader.current_chunk)
            else:
                # fix the record data, skip or stop reading:
                print(reader.current_exception)
                print(reader.current_chunk)
                # break/continue/raise

    marc_tags.sort()

    print(",".join(['"%s"' % tag for tag in marc_tags]))
    writer = csv.DictWriter(sys.stdout, marc_tags)
    writer.writerows(csv_records)

    with open(dest, "w") as f:
        file_writer = csv.DictWriter(f, marc_tags)
        file_writer.writeheader()
        file_writer.writerows(csv_records)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        msg = """
        "Please provide the filename or path of the marc or csv file you want to convert."
        """
        raise ValueError(msg)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        msg = "File does not exists."
        raise ValueError(msg)

    if (
        filepath.name.split(".")[1] == "marc"
        or filepath.name.split(".")[1] == "mrc"
        or filepath.name.split(".")[1] == "dat"
    ):
        ext = "csv"

    elif filepath.name.split(".")[1] == "csv":
        ext = "mrc"

    else:
        msg = "File must have mrc, marc, dat, or csv extension"
        raise ValueError(msg)

    dest = filepath.parent / f"{filepath.name.split('.')[0]}.{ext}"

    print(f"dest is {dest}")
    # first, handle marc to csv conversion

    if ext == "csv":
        to_csv(filepath, dest)
    # this refers to the extension for the file to write, i.e. to convert to

    # now, handle csv to marc conversion
