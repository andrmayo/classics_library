# module useful for working with csv representation of marc file
# draws heavily from pymarc/reader.py

import os
import sys
from pathlib import Path
from collections.abc import Iterator
from io import IOBase, StringIO
from typing import Union, Iterable, Optional
import csv

from pymarc import Field, Indicators, Leader, Record, Subfield

from htmlutils import repl_nonASCII


class Reader:
    """A base class for all iterating readers in the pymarc package."""

    def __iter__(self):
        return self


class CSVReader(Reader):
    """CSV Reader."""

    file_handle: Iterable[str]  # required type for DictReader

    def __init__(
        self,
        marc_target: Union[bytes, str, Path],
        encoding: str = "utf-8",
        marc_dest: Union[None, str, Path] = None,
        stream: bool = False,
    ) -> None:
        """Basically the argument you pass in should be raw csv in transmission format.
        A csv.DictReader object is used to handle the records."""
        # streaming is not implemented.
        self.encoding = encoding
        self.marc_dest = marc_dest
        if isinstance(marc_target, IOBase):
            self.file_handle = marc_target
        else:
            if isinstance(marc_target, str) and os.path.exists(marc_target):
                self.file_handle = open(marc_target)  # noqa: SIM115
            elif isinstance(marc_target, Path) and marc_target.exists():
                self.file_handle = open(marc_target)  # noqa: SIM115
            else:
                self.file_handle = StringIO(marc_target)  # type: ignore
        if stream:
            sys.stderr.write(
                "Streaming not yet implemented, your data will be loaded into memory\n"
            )
        self.records = [rec for rec in csv.DictReader(self.file_handle)]

    def __iter__(self) -> Iterator:  # type: ignore
        self.iter = iter(self.records)
        return self

    def __next__(self) -> Iterator:
        line = next(self.iter)
        line: dict = next(self.iter)
        return self._make_record(line)

    def _make_record(self, line):
        rec = Record()
        for field in line:
            if isinstance(field, str) and (
                field.upper() == "LDR" or field.lower() == "leader"
            ):
                rec.leader = Leader(line[field])
                continue
            line[field] = line[field].replace(chr(31), "$")
            if "$" in line[field][:3]:
                indicators, field_text = line[field].split("$", maxsplit=1)
                indicators = indicators.replace("\\", " ")
                indicators = [char for char in indicators][:2]
            else:
                indicators, field_text = (None, line[field])
            if indicators:
                subfields = (
                    [Subfield(code=s[0], value=s[1:]) for s in field_text.split("$")]
                    if field_text
                    else []
                )
                field = Field(
                    tag=field,
                    indicators=Indicators(*indicators),
                    subfields=subfields,
                )
            else:
                field = Field(
                    tag=field,
                    data=field_text,
                )
            rec.add_field(field)
        return rec

    def get_record(self, index: int) -> Record:
        """Takes in an index integer and returns relevant line of csv as Record object"""
        return self._make_record(self.records[index])

    def html_ent(self) -> None:
        """Converts all non-ASCII utf-8 characters to their ASCII-compatible entity names."""
        self.records = self.records.map(repl_nonASCII, na_action="ignore")
        self.records.to_csv(self.file_handle, index=False)

    def to_marc(self, marc_dest=None) -> None:
        if not marc_dest:
            if self.marc_dest:
                marc_dest = self.marc_dest
            else:
                if not isinstance(self.file_handle, Union[str, Path]):
                    print(
                        "Unable to generate destination for marc file from csv file handle"
                    )
                    return
                if isinstance(self.file_handle, str):
                    path = Path(self.file_handle)
                    marc_dest = path.parent / f"{path.stem}.marc"
                else:
                    marc_dest = (
                        self.file_handle.parent / f"{self.file_handle.stem}.marc"
                    )
        if not self.marc_dest:
            self.marc_dest = marc_dest
        if isinstance(self.marc_dest, str):
            Path(self.marc_dest).unlink(missing_ok=True)
        else:
            Path(self.marc_dest).unlink(missing_ok=True)

        reader = csv.DictReader(self.file_handle)
        # to_marc(self.file_handle, marc_dest)


def to_marc(filepath: Union[str, Path, StringIO], dest: Union[str, Path]) -> None:
    """
    Function to convert csv file to marc file. Assumes that csv file has the format
    output by to_csv above. Not yet tested.
    """
    with open(filepath, "r") as f:  # type: ignore
        reader = csv.DictReader(f)
        for line in reader:
            record = Record()
            for tag in line.keys():
                if tag.upper() == "LDR" or tag.lower() == "leader":
                    record.leader = Leader(line[tag])
                    print(f"leader is {record.leader}")
                    continue
                if not line[tag]:  # skip empty fields
                    continue
                # some marc files use the unit separator with unicode value 31, control picture ␟,
                # to mark beginning of a subfield, so first we replace this with $
                line[tag] = line[tag].replace(chr(31), "$")
                if "$" in line[tag][:3]:
                    indicators, field_text = line[tag].split("$", maxsplit=1)
                    indicators = indicators.replace("\\", " ")
                    indicators = [char for char in indicators][:2]
                else:
                    indicators, field_text = (None, line[tag])
                if indicators:
                    subfields = (
                        [
                            Subfield(code=s[0], value=s[1:])
                            for s in field_text.split("$")
                        ]
                        if field_text
                        else []
                    )
                    field = Field(
                        tag=tag,
                        indicators=Indicators(*indicators),
                        subfields=subfields,
                    )
                else:
                    field = Field(
                        tag=tag,
                        data=field_text,
                    )
                record.add_field(field)

            print(record.__str__())
            with open(dest, "ab") as out:
                out.write(record.as_marc())
