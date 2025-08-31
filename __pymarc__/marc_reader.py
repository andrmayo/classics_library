# module useful for working with csv representation of marc file
# draws heavily from pymarc/reader.py

import os
import sys
from pathlib import Path
from collections.abc import Iterator
from io import IOBase, StringIO
from typing import Union, Iterable
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
        stream: bool = False,
    ) -> None:
        """Basically the argument you pass in should be raw csv in transmission format.
        A csv.DictReader object is used to handle the records."""
        # streaming is not implemented.
        self.encoding = encoding
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
