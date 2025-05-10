from collections.abc import Generator

def decode_64(encoded: str) -> Generator[str]:
    for char in encoded:
        of_64 = None
        if char.isupper():
            of_64 = ord(char) - 65
        elif char.islower():
            of_64 = ord(char) - 71
        elif char.isnumeric():
            of_64 = ord(char) + 4
        elif char == "+":
            of_64 = 62
        elif char == "/":
            of_64 = 63
        assert of_64 is not None, f"string:\n{encoded}\n\ncontains invalid base64 character {char}" 
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
    
