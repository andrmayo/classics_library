from pathlib import Path
from typing import Union, Tuple
import re
from base64utils import decode_64

# regex pattern for finding start of marc recordr"\d{5}(\s|[A-Za-z]){3}[A-Za-z\s#]{2}[012]"
RECORD_START = r"^\d{5}(\s|[A-Za-z]){3}[A-Za-z\s#]{2}[012]"


def _check_base64(line: str) -> Tuple[bool, int, int]:
    "This detects first line in base64 in marc file."
    if "MDA" not in line and "MDE" not in line:
        return False, -1, -1
    match = re.search(r"(\n|\x1c|\x1d|\x1e\x1f)MD[AE]", line)
    if match:
        start, end = match.span()
        start = start + 1  # we don't want index of record delimiter
    else:
        match = re.search(r"^MD", line)
        if match:
            start, end = match.span()
    if match:
        start, end = match.span()
        return True, start, end
    return False, -1, -1


def _handle_base64(line: str, lines: list, base64_buffer: list) -> bool:
    is_match, start, _ = _check_base64(line)
    if not is_match:
        lines.append(line)
        return False
    start += 1
    # base64 encoding sometimes continues on same line as regular utf8 record
    if start > 0:
        lines.append(line[:start])
    # assume first line of base64 encoding section never has regular utf8 after base64.
    base64_buffer.append(line[start:])
    return True


def _normalize_record_spacing(records: str) -> str:
    records = records.replace("\n", " ")
    pattern = r"(\x1e\x1d)(\s|\n)*(\d+)"
    records = re.sub(pattern, r"\1\3", records)
    return records


def _get_records_64(records: list[str]) -> list[str]:
    """Function to take in a list of lines in base64 read from a marc file
    and return a new list in which each item is a string encoding a single records.
    This assumes a new record will always start on a new line/element."""
    # take first 18 characters of line, and decode
    by_record = []
    cur_buffer = []
    for line in records:
        line = line.strip()
        incipit = line[:18]
        incipit = "".join([char for char in decode_64(incipit)])
        if re.search(RECORD_START, incipit):
            by_record.append("".join(cur_buffer))
            cur_buffer = [line]
        else:
            cur_buffer.append(line)
    # deal with leftovers in cur_buffer
    by_record.append("".join(cur_buffer))
    return by_record


# more elegant would be to do this the intended way for the marc format,
# namely by reading the number of bytes in the record from the start of the record,
# but this was easier.
# default encoding here is utf8.
# to work with marc8 files, can pass in encoding="ISO-8859-1" as a workaround, since this is 
# also a one byte encoding.
def flatten_mixed_marc(filename: Union[Path, str], encoding="utf8") -> Path:
    """Take path to marc file containing mix of regular utf8 and base64 utf8,
    and rewrites it to only include regular utf8, i.e. binary encodings of
    the final characters themselves in utf8. This relies on
    base64 encoding strings beginning with MDA and plain utf8 strsing beginning with 00###.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} not found.")
    lines = []
    base64_buffer = []
    with open(str(filename), "r", encoding=encoding) as f:
        in_base64 = False
        base64_segment = ""
        base64_records = []
        for line in f:
            if not in_base64:
                in_base64 = _handle_base64(line, lines, base64_buffer)
                continue
                # base64 encoding sometimes continues on same line as regular utf8 record
            match = re.search(RECORD_START, line)
            if match:
                start, _ = match.span()
                if start > 0:
                    base64_buffer.append(line[:start])
                base64_records = _get_records_64(base64_buffer)
                for line_64 in base64_records:
                    base64_segment = "".join([char for char in decode_64(line_64)])
                    lines.append(base64_segment)
                base64_buffer = []
                in_base64 = _handle_base64(line[start:], lines, base64_buffer)
                continue
            base64_buffer.append(line)
        # deal with anything left over in base64_buffer
        base64_records = _get_records_64(base64_buffer)
        for line_64 in base64_records:
            base64_segment = "".join([char for char in decode_64(line_64)])
            lines.append(base64_segment)
        del base64_buffer, base64_segment, base64_records
    count = 0
    for i, line in enumerate(lines):
        lines[i] = _normalize_record_spacing(line)
        # deal with random null characters
        lines[i] = line.replace("\x00", "")
    with open(f"flattened_{filename}", "w", encoding="utf8") as f:
        for line in lines:
            count += 1
            f.write(line)
    msg = f"""
        Converted base64 in marc file {filename} to standard utf8
        and wrote {count} lines to flattened_{filename}.
    """
    print(msg)
    return Path(f"flattened_{filename}")


# default encoding here is utf8.
# to work with marc8 files, can pass in encoding="ISO-8859-1" as a workaround, since this is 
# also a one byte encoding.
def separate_mixed_marc(
    filename: Union[Path, str], encoding="utf-8"
) -> Tuple[Path, Path]:
    """Take path to marc file containing mix of regular utf8 and base64 utf8,
    and rewrites it to only include regular utf8, i.e. binary encodings of
    the final characters themselves in utf8. This relies on
    base64 encoding strings beginning with MDA and plain utf8 strsing beginning with 00###.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    if not filename.exists():
        raise FileNotFoundError(f"File {filename} not found.")
    lines = []
    base64_lines = []
    base64_buffer = []
    with open(str(filename), "r", encoding=encoding) as f:
        in_base64 = False
        base64_segment = ""
        for line in f:
            if not in_base64:
                in_base64 = _handle_base64(line, lines, base64_buffer)
                continue
                # base64 encoding sometimes continues on same line as regular utf8 record
            match = re.search(RECORD_START, line)
            if match:
                start, _ = match.span()
                if start > 0:
                    base64_buffer.append(line[:start])
                base64_records = _get_records_64(base64_buffer)
                for line_64 in base64_records:
                    base64_segment = "".join([char for char in decode_64(line_64)])
                    base64_lines.append(base64_segment)
                base64_buffer = []
                in_base64 = _handle_base64(line[start:], lines, base64_buffer)
                continue
            base64_buffer.append(line)
        # deal with anything left over in base64_buffer
        base64_records = _get_records_64(base64_buffer)
        for line_64 in base64_records:
            base64_segment = "".join([char for char in decode_64(line_64)])
            base64_lines.append(base64_segment)
        del base64_segment, base64_buffer, base64_records
    if encoding == "ISO-8859-1":
        enc_name = "LATIN1"
    else:
        enc_name = encoding

    count = 0
    with open(f"{enc_name}_{filename}", "w", encoding=encoding) as f:
        for line in lines:
            line = _normalize_record_spacing(line)
            count += len(line)
            f.write(line)
    msg = f"""
        from {filename} wrote {enc_name}_{filename} with {count} characters 
        in encoding format {encoding}.
    """
    print(msg)

    count = 0
    with open(f"UTF8_{filename}", "w", encoding="utf8") as f:
        for line in base64_lines:
            count += len(line)
            line = _normalize_record_spacing(line)
            # deal with random null characters
            line = line.replace("\x00", "")
            line = line.strip("\n")
            f.write(line)
    msg = f"""
        from {filename} wrote UTF8_{filename} with {count} characters 
        in encoding format UTF8.
    """
    print(msg)
    return Path(f"{enc_name}_{filename}"), Path(f"UTF8_{filename}")
