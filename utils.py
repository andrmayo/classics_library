from collections.abc import Generator
from typing import Optional, Union


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
    elif encoding_char == "/":
        of_64 = 63
    return of_64


def _to_byte(of_64: Union[int, str]) -> list:
    if isinstance(of_64, str):
        of_64 = int(of_64)
    assert of_64 < 64, (
        f"input to _to_byte contains invalid base64 character: {of_64}"
    )
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
        bytes = bytes[:len(bytes)-len(bytes)%8]
    val = 0
    # TODO: test/debug that adding utf8 functionality hasn't broken code for ASCII, and works for utf8
    block_len = 0 # keeps track of how many bytes encode a single utf8 char
    utf8_block = [] # contains bits in a multibyte utf8 encoding
    in_utf8_block = False
    for i in range(int(len(bytes) / 8)):
        binary_byte = bytes[i*8: (i+1)*8]
        utf8_instruct_byte = False # keeps track of whether current byte encodes how many bytes encode current char
        # handle case where currently in multibyte character encoding
        if in_utf8_block:
            for j, bit in enumerate(binary_byte):
                if j == 0:
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
                #this handles non-ASCII characters in utf-8
                utf8_instruct_byte = True
                continue
            if bit: 
                # handle regular ASCII binary encodings
                if not utf8_instruct_byte:
                    val += 2**(7-j)
                # handle utf8 instructions for how many bytes encode char
                else:
                    block_len += 1
            elif utf8_instruct_byte: # exits from receiving utf8 instructions on encountering a 0 
                utf8_instruct_byte = False
                in_utf8_block = True

        yield chr(val)
        val = 0



