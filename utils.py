from collections.abc import Generator
from typing import Optional


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


def decode_64(encoded: str) -> Generator[str]:
    """
    Function to convert base64 in utf-8 (i.e. with
    alphanumeric characters, "+", and "/") into ASCII characters.
    """
    for char in encoded:
        of_64 = _char_to_64(char)
        assert of_64 is not None, (
            f"string:\n{encoded}\n\ncontains invalid base64 character {char}"
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
        print(" ".join([str(num) for num in byte]))
        val = 0
        for i in range(len(byte)):
            val += byte[-(i)] * (2**i)
        yield chr(val)
