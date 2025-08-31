import csv
from io import StringIO
from typing import List, Set, Union, IO, Iterable
from warnings import warn

import pymarc
from pymarc import Record, WriteNeedsRecord


class Writer:
    """Base Writer object."""

    def __init__(self, file_handle: IO) -> None:
        """Init."""
        self.file_handle = file_handle

    def write(self, record: Record) -> None:
        """Write."""
        if not isinstance(record, Record):
            raise WriteNeedsRecord

    def close(self, close_fh: bool = True) -> None:
        """Closes the writer.

        If close_fh is False close will also close the underlying file handle
        that was passed in to the constructor. The default is True.
        """
        if close_fh:
            self.file_handle.close()
        self.file_handle = None  # type: ignore


class CSVWriter(Writer):
    """A class for writing records as an array of MARC-in-CSV objects.

    IMPORTANT: You must close a CSVWriter,
    otherwise you will not get valid CSV.

    Simple usage::

    .. code-block:: python

        from pymarc import CSVWriter

        # writing individual records to a file (not recommended)
        writer = CSVWriter(open('file.csv','wt'))
        writer.add_tags(['001', '003', '264', '300']
        writer.write(record1)
        writer.write(record2)
        writer.close()  # Important!

        #writing multiple records (as list) to a file (recommended)
        writer = CSVWriter(open('file.csv','wt'))
        writer.write_all(records)
        writer.close()  # Important!

        # writing to a string
        string = StringIO()
        writer = CSVWriter(string)
        writer.write(records)
        writer.close(close_fh=False)  # Important!
        print(string)
    """

    def __init__(self, file_handle: IO) -> None:
        super().__init__(file_handle)
        self.write_count = 0
        self.marc_tags: set = {"LDR"}
        self.csv_dict_writer = None

    def write(self, record):
        """Writes record.
        Note that for writing single records to a CSV file, if record contains
        a tag that hasn't been defined (explicitly with `CSVWriter.add_tags`
        or implicitly with `write_all`), the corresponding field will simply be skipped.
        So `CSVWriter.add_tags` or `CSVWriter.write_all` should always be called beforehand."""
        Writer.write(self, record)
        leader = record.leader.leader
        csv_record = {}
        csv_record["LDR"] = leader
        for marc_field in record.get_fields():
            if marc_field.tag not in self.marc_tags:
                print(f"skipping marc tag: {marc_field.tag}")
                continue
            indicator1 = marc_field.indicator1 if marc_field.indicator1 != " " else "\\"
            indicator2 = marc_field.indicator2 if marc_field.indicator2 != " " else "\\"
            if not indicator1:
                indicator1 = "\\"
            if not indicator2:
                indicator2 = "\\"
            if marc_field.subfields:
                csv_record[marc_field.tag] = (
                    f"{indicator1}{indicator2}{''.join([f'${s.code}{s.value}' for s in marc_field.subfields])}"
                )
            else:
                csv_record[marc_field.tag] = marc_field.data

        if not self.csv_dict_writer:
            self.csv_dict_writer = csv.DictWriter(
                self.file_handle,  # type: ignore
                sorted(self.marc_tags),
            )
            self.csv_dict_writer.writeheader()

        if len(self.marc_tags) <= 1:
            warn(
                "No marc tags have been added, so CSV will be missing fields. Call add_tags or write_all before write."
            )

        self.csv_dict_writer.writerow(csv_record)

    def add_tags(self, tags: Iterable) -> Set:
        """Add CSV columns for fields in marc records.
        Only necessary if calling `CSVWriter.write`
        without previously calling `CSVWriter.write_all`."""
        self.marc_tags.update(tags)
        return self.marc_tags

    def write_all(self, records: List) -> None:
        """Writes records.
        Infers the columns for CSV from tags in records,
        so there's no need to call `CSVWriter.add_tags`."""
        csv_records = []
        for record in records:
            Writer.write(self, record)
            csv_record = {}
            if record:
                leader = record.leader.leader
                csv_record["LDR"] = leader
                for marc_field in record.get_fields():
                    if marc_field.tag not in self.marc_tags:
                        self.marc_tags.add(marc_field.tag)
                    # deal with indicators
                    indicator1 = (
                        marc_field.indicator1 if marc_field.indicator1 != " " else "\\"
                    )
                    indicator2 = (
                        marc_field.indicator2 if marc_field.indicator2 != " " else "\\"
                    )
                    if not indicator1:
                        indicator1 = "\\"
                    if not indicator2:
                        indicator2 = "\\"
                    # note that some fields may have no subfields (as with control fields).
                    # in this case, marc_field.subfields returns and empty list.
                    if marc_field.subfields:
                        csv_record[marc_field.tag] = (
                            f"{indicator1}{indicator2}{''.join([f'${s.code}{s.value}' for s in marc_field.subfields])}"
                        )
                    # handle field without subfields. These should be control fields.
                    else:
                        csv_record[marc_field.tag] = marc_field.data

                csv_records.append(csv_record)

        if not self.csv_dict_writer:
            self.csv_dict_writer = csv.DictWriter(
                self.file_handle,  # type: ignore
                sorted(self.marc_tags),
            )
            self.csv_dict_writer.writeheader()

        self.csv_dict_writer.writerows(csv_records)

    def close(self, close_fh: bool = True) -> None:
        """Closes the writer.

        If close_fh is False close will also close the underlying file
        handle that was passed in to the constructor. The default is True.
        """
        Writer.close(self, close_fh)
