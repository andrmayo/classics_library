# module useful for working with csv representation of marc file
# draws heavily from pymarc/reader.py


import os
import sys
from pathlib import Path
from collections.abc import Iterator
from io import BytesIO, StringIO
from typing import Union
import pandas as pd

from pymarc import Field, Indicators, Leader, Record, Subfield

from csvconv import to_marc
from htmlutils import repl_nonASCII

class Reader:
    """A base class for all iterating readers in the pymarc package."""

    def __iter__(self):
        return self

class CSVReader:
    """CSV Reader."""
    records: pd.DataFrame
    def __init__(
        self,
        marc_target: Union[bytes, str, Path],
        encoding: str = "utf-8",
        marc_dest: Union[None, str, Path] = None,
        stream: bool = False,
    ) -> None:
        """Basically the argument you pass in should be raw csv in transmission format or
            an object that responds to read()."""
        # streaming is not implemented. 
        # Note that unlike the JSONReader this does not accept any IOBase object.
        self.encoding = encoding
        self.marc_dest = marc_dest
        if isinstance(marc_target, str) and os.path.exists(marc_target):
            self.file_handle = marc_target
        elif isinstance(marc_target, Path) and marc_target.exists():
            self.file_handle = marc_target
        elif isinstance(marc_target, str):
            # case where marc_target is the csv content itself as a string
            self.file_handle = StringIO(marc_target) # type: ignore
        else:
            self.file_handle = BytesIO(marc_target) # type: ignore

        if stream:
            sys.stderr.write(
                "Streaming not yet implemented, your data will be loaded into memory\n"
            )
        self.records = pd.read_csv(self.file_handle, encoding=encoding)

    def __iter__(self) -> Iterator:
        self.iter = iter(self.records.iterrows())
        return self

    def __next__(self) -> Iterator:
        line: pd.Series = next(self.iter)[1]
        rec = Record()
        for field in line[line.notnull()].keys():
            if isinstance(field, str) and (field.upper() == "LDR" or field.lower() == "leader"):
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
                    tag = field,
                    data = field_text,
                )
            rec.add_field(field)
        return rec

    def get_record(self, index: int, by_loc: bool=False) -> Record:
        """Takes in an index integer and returns relevant line of csv as Record object"""
        record = Record()
        if not by_loc:
            for col in self.records.columns:
                if isinstance(col, str) and (col.lower() == "leader" or col.lower() == "ldr"):
                    record.leader = Leader(self.records.iloc[index][col])
                    record.leader = Leader(self.records.iloc[index][col])
                    continue
                if pd.isna(self.records.iloc[index][col]):
                    continue
                field_tag = col if isinstance(col, str) else str(col)
                if isinstance(self.records.iloc[index][col], str):
                    field_text = self.records.iloc[index][col]
                else:
                    field_text = str(self.records.iloc[index][col])
                # this requires that subfields be demarcated with '$'
                if "$" in field_text[:3]:
                    indicators, field_text = field_text.split("$", maxsplit=1)
                    indicators = indicators.replace("\\", " ")
                    indicators = [char for char in indicators][:2]
                    subfields = [Subfield(code=s[0], value=s[1:]) for s in field_text.split("$")]
                    field = Field(tag = field_tag, indicators=Indicators(*indicators), subfields = subfields)
                else:
                    field = Field(tag = field_tag, data=field_text)
                record.add_field(field)
            return record

        for col in self.records.columns:
            if isinstance(col, str) and (col.lower() == "leader" or col.lower() == "ldr"):
                record.leader = Leader(self.records.iloc[index][col])
                record.leader = Leader(self.records.iloc[index][col])
                continue
            if pd.isna(self.records.iloc[index][col]):
                continue
            field_tag = col if isinstance(col, str) else str(col)
            if isinstance(self.records.iloc[index][col], str):
                field_text = self.records.iloc[index][col]
            else:
                field_text = str(self.records.iloc[index][col])
            # this requires that subfields be demarcated with '$'
            if "$" in field_text[:3]:
                indicators, field_text = field_text.split("$", maxsplit=1)
                indicators = indicators.replace("\\", " ")
                indicators = [char for char in indicators][:2]
                subfields = [Subfield(code=s[0], value=s[1:]) for s in field_text.split("$")]
                field = Field(tag = field_tag, indicators=Indicators(*indicators), subfields = subfields)
            else:
                field = Field(tag = field_tag, data=field_text)
            record.add_field(field)
        return record

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
                    print("Unable to generate destination for marc file from csv file handle")
                    return
                if isinstance(self.file_handle, str):
                    path = Path(self.file_handle)
                    marc_dest = path.parent / f"{path.stem}.marc"
                else:
                    marc_dest = self.file_handle.parent / f"{self.file_handle.stem}.marc"
        if not self.marc_dest:
            self.marc_dest = marc_dest
        if isinstance(self.marc_dest, str):
            Path(self.marc_dest).unlink(missing_ok=True)
        else:
            Path(self.marc_dest).unlink(missing_ok=True)
        to_marc(self.file_handle, marc_dest)
