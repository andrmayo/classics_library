from collections.abc import Generator
from typing import Optional, Union, Tuple
from pathlib import Path
import re


def _char_to_64(encoding_char: str) -> Optional[int]:
    "helper function for decode_64."
    assert len(encoding_char) == 1
    of_64 = None
    if encoding_char.isupper():
        of_64 = ord(encoding_char) - 65
    elif encoding_char.islower():
        of_64 = ord(encoding_char) - 71
    elif encoding_char.isnumeric():
        of_64 = ord(encoding_char) + 4
    elif encoding_char == "+":
        of_64 = 62
    elif encoding_char == "-":
        of_64 = 62
    elif encoding_char == "/":
        of_64 = 63
    elif encoding_char == "_":
        of_64 = 63
    return of_64


def _to_byte(of_64: Union[int, str]) -> list:
    if isinstance(of_64, str):
        of_64 = int(of_64)
    assert of_64 < 64, f"input to _to_byte contains invalid base64 character: {of_64}"
    byte = [0, 0, 0, 0, 0, 0]
    if of_64 % 2 == 1:
        byte[5] = 1
    if of_64 % 4 > 1:
        byte[4] = 1
    if of_64 % 8 > 3:
        byte[3] = 1
    if of_64 % 16 > 7:
        byte[2] = 1
    if of_64 % 32 > 15:
        byte[1] = 1
    if of_64 % 64 > 31:
        byte[0] = 1
    return byte


def _eval_multibyte(encoding: list) -> int:
    "convert a binary encoding of any length to an integer value"
    val = 0
    exponent = len(encoding) - 1
    for bit in encoding:
        if bit:
            val += 2**exponent
        exponent -= 1
    return val


def decode_64(encoded: str) -> Generator[str]:
    """
    Function to convert base64 in utf-8 (i.e. with
    alphanumeric characters, "+", and "/") into unicode characters.
    Returns a generator that yields decoded string character by character.
    """
    bytes = []
    for char in encoded:
        # deal with padding character
        # marc files output by librarything seem to use "." as padding character, rather than "="
        if char == "=" or char == "." or char.isspace():
            continue
        of_64 = _char_to_64(char)
        assert of_64 is not None, (
            f"string:\n{encoded}\n\ncontains invalid base64 character: {char}"
        )
        byte = _to_byte(of_64)
        bytes.extend(byte)
    # discard any bits left over from taking groups of 8
    if len(bytes) % 8 != 0:
        bytes = bytes[: len(bytes) - len(bytes) % 8]
    val = 0
    # TODO: test/debug that adding utf8 functionality hasn't broken code for ASCII, and works for utf8
    block_len = 0  # keeps track of how many bytes encode a single utf8 char
    utf8_block = []  # contains bits in a multibyte utf8 encoding
    in_utf8_block = False
    for i in range(int(len(bytes) / 8)):
        binary_byte = bytes[i * 8 : (i + 1) * 8]
        utf8_instruct_byte = False  # keeps track of whether current byte encodes how many bytes encode current char
        # handle case where currently in multibyte character encoding
        if in_utf8_block:
            for j, bit in enumerate(binary_byte):
                if j < 2:
                    continue
                utf8_block.append(bit)
            block_len -= 1
            if block_len == 0:
                in_utf8_block = False
                yield chr(_eval_multibyte(utf8_block))
                utf8_block = []
            continue
        # now, handle case where we are not already in a multibyte character encoding.
        # this also handles the first byte of a multibyte encoding.
        for j, bit in enumerate(binary_byte):
            # first, check if this is the tail of the first byte in a multibyte utf8 encoding
            if in_utf8_block:
                utf8_block.append(bit)
                continue
            # handle utf-8 binary encodings, which have 1 as first bit
            if j == 0 and bit == 1:
                # this handles non-ASCII characters in utf-8
                utf8_instruct_byte = True
                continue
            if bit:
                # handle regular ASCII binary encodings
                if not utf8_instruct_byte:
                    val += 2 ** (7 - j)
                # handle utf8 instructions for how many bytes encode char
                else:
                    block_len += 1
            elif (
                utf8_instruct_byte
            ):  # exits from receiving utf8 instructions on encountering a 0
                utf8_instruct_byte = False
                in_utf8_block = True

        yield chr(val)
        val = 0


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
    # base64 encoding sometimes continues on same line as regular utf8 record
    if start > 0:
        lines.append(line[:start])
    # assume first line of base64 encoding section never has regular utf8 after base64.
    base64_buffer.append(line[start:])
    return True


def _normalize_record_spacing(records: str) -> str:
    records = records.replace("\n", "")
    pattern = r"(\x1e\x1d)(\s|\n)*(\d+)"
    records = re.sub(pattern, r"\1\3", records)
    return records


def _clean_controls(records: str) -> str:
    """deal with unnecessary control characters
    and some related issues."""
    controls = []
    for i in range(28):
        controls.append(chr(i))
    for control in controls:
        records = records.replace(control, "")
    pattern = r"(\x1e\x1d)\D*$"
    records = re.sub(pattern, r"\1", records)
    pattern = r"(\x1e\x1d)\S*$"
    records = re.sub(pattern, r"\1", records)
    pattern = r"(\x1e\x1d).*?(\d\d\d\d\d )"
    records = re.sub(pattern, r"\1\2", records)
    pattern = r"(\x1e\x1d)\S*?##"
    records = re.sub(pattern, r"\1", records)
    # some records have 'CR<LDR>, which causes issues
    pattern = r"CR(\d\d\d\d\d )"
    records = re.sub(pattern, r"\1", records)
    pattern = r"CR$"
    records = re.sub(pattern, "", records)
    pattern = r"^.(\d\d\d\d\d\s)"
    records = re.sub(pattern, "\1", records)
    return records

# more elegant would be to do this the intended way for the marc format,
# namely by reading the number of bytes in the record from the start of the record,
# but this was easier.
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
        for line in f:
            if not in_base64:
                in_base64 = _handle_base64(line, lines, base64_buffer)
                continue
                # base64 encoding sometimes continues on same line as regular utf8 record
            match = re.search(r"\d\d\d\d\d\s+\d", line)
            if match:
                start, _ = match.span()
                if start > 0:
                    base64_buffer.append(line[:start])
                for line_64 in base64_buffer:
                    base64_segment = "".join([char for char in decode_64(line_64.strip())])
                    lines.append(base64_segment)
                    print(base64_segment)
                base64_buffer = []
                in_base64 = _handle_base64(line[start:], lines, base64_buffer)
                continue
            base64_buffer.append(line)
        # deal with anything left over in base64_buffer
        for line_64 in base64_buffer:
            base64_segment = "".join([char for char in decode_64(line_64.strip())])
            print(base64_segment)
            lines.append(base64_segment)
        del base64_buffer, base64_segment
    count = 0
    for i, line in enumerate(lines):
        lines[i] = _normalize_record_spacing(line)
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


# default encoding here is ISO-8859-1, since that's what the marc exports from librarything are
# encoded in, even though base64 sections must be mapped to utf8.
def separate_mixed_marc(
    filename: Union[Path, str], encoding="ISO-8859-1"
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
        for line in f:
            if not in_base64:
                in_base64 = _handle_base64(line, lines, base64_buffer)
                continue
                # base64 encoding sometimes continues on same line as regular utf8 record
            match = re.search(r"\d\d\d\d\d\s+\d", line)
            if match:
                start, _ = match.span()
                if start > 0:
                    base64_buffer.append(line[:start])
                base64_segment = "".join(base64_buffer)
                base64_lines.append(
                    "".join([char for char in decode_64(base64_segment)])
                )
                del base64_segment
                base64_buffer = []
                in_base64 = _handle_base64(line[start:], lines, base64_buffer)
                continue
            base64_buffer.append(line.strip())
        # deal with anything left over in base64_buffer
        base64_segment = "".join(base64_buffer)
        base64_lines.append("".join([char for char in decode_64(base64_segment)]))
        del base64_segment, base64_buffer
    if encoding == "ISO-8859-1":
        enc_name = "LATIN1"
    else:
        enc_name = encoding

    for i, line in enumerate(lines):
        lines[i] = _normalize_record_spacing(line)

    count = 0
    with open(f"{enc_name}_{filename}", "w", encoding=encoding) as f:
        for line in lines:
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
            line = _clean_controls(line)
            f.write(line)
    msg = f"""
        from {filename} wrote UTF8_{filename} with {count} characters 
        in encoding format UTF8.
    """
    print(msg)
    return Path(f"{enc_name}_{filename}"), Path(f"UTF8_{filename}")
