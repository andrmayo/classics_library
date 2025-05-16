# script to convert between csv and marc formats

import csv
import sys
from pathlib import Path
from typing import Union

from pymarc import MARCReader
from pymarc import exceptions as exc
from pymarc import Record, Field, Subfield, Indicators, Leader


from utils import flatten_mixed_marc


def to_csv(
    filepath: Union[str, Path], dest: Union[str, Path], include_indicator=True
) -> None:
    """function to convert marc file to csv file.
    To include indicators in format <indicators>$<field>, pass include_indicator=True,
    this is mainly to facilitate converting back to marc format.
    """

    # create and get name of new file with all base64 converted to regular utf8
    filepath = flatten_mixed_marc(filepath)
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
                    # deal with indicators, if applicable
                    if include_indicator:
                        indicator1 = (
                            marc_field.indicator1
                            if marc_field.indicator1 != " "
                            else "\\"
                        )
                        indicator2 = (
                            marc_field.indicator2
                            if marc_field.indicator2 != " "
                            else "\\"
                        )
                        if not indicator1:
                            indicator1 = "\\"
                        if not indicator2:
                            indicator2 = "\\"
                        csv_record[marc_field.tag] = (
                            f"{indicator1}{indicator2}{' '.join([f'${s.code}{s.value}' for s in marc_field.subfields])}"
                        )
                    else:
                        csv_record[marc_field.tag] = " ".join(
                            [f"${s.code}{s.value}" for s in marc_field.subfields]
                        )

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


def to_marc(filepath: Union[str, Path], dest: Union[str, Path]) -> None:
    """
    Function to convert csv file to marc file. Assumes that csv file has the format
    output by to_csv above. Not yet tested.
    """
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for line in reader:
            record = Record()
            for tag in line.keys():
                if tag.upper() == "LDR" or tag.lower() == "leader":
                    record.leader = Leader(line[tag])
                    continue
                # some marc files use the unit separator with unicode value 31, control picture ␟,
                # to mark beginning of a subfield, so first we replace this with $
                line[tag] = line[tag].replace(chr(31), "$")
                if "$" in line[tag][:3]:
                    indicators, field_text = line[tag].split("$", maxsplit=1)
                    indicators = indicators.replace(" ", "\\")
                    indicators = [char for char in indicators][:2]
                else:
                    indicators, field_text = (["\\", "\\"], line[tag])
                field_text = field_text.strip()
                subfields = (
                    [Subfield(code=s[0], value=s[1:]) for s in field_text.split("$")]
                    if field_text
                    else []
                )
                field = Field(
                    tag=tag,
                    indicators=Indicators(*indicators),
                    subfields=subfields,
                )
                record.add_field(field)

                print(record.__str__())
                with open(dest, "ab") as out:
                    out.write(record.as_marc())


if __name__ == "__main__":
    if len(sys.argv) == 0:
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

    # first, handle marc to csv conversion

    if ext == "csv":
        dest = filepath.parent / f"{filepath.name.split('.')[0]}.{ext}"
        print(f"dest is {dest}")
        to_csv(filepath, dest, include_indicator=True)
        sys.exit()
    # this refers to the extension for the file to write, i.e. to convert to

    # now, handle csv to marc conversion: here, ext is marc, mrc, dat, etc.
    dest = filepath.parent / f"{filepath.name.split('.')[0]}_fromCSV.{ext}"
    print(f"dest is {dest}")
    to_marc(filepath, dest)
