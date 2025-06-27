import os 
import sys

# make imports work when this is run as a script, rather than with Pytest
if not "PYTEST_CURRENT_TEST" in os.environ:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(parent_dir)

from utils import decode_64, _eval_multibyte

def test_base64():
    msg = """
        MDA4MzEgICAgIDIyMDAxOTMgaSA0NTAwMDAxMDAwOTAwMDAwMDAzMDAwNzAwMDA5MDA1MDAxNzAw
        MDE2MDIwMDAxNTAwMDMzMDQwMDAyNDAwMDQ4MDkwMDAzMDAwMDcyMDkyMDAxMTAwMTAyMTAwMDAy
        NDAwMTEzMjQ1MDE3NjAwMTM3MjY0MDA4MzAwMzEzMzAwMDAxMjAwMzk2NTIwMDIwMzAwNDA4OTIw
        MDAwOTAwNjExOTIzMDAxNzAwNjIwHjY1Mjc3NDAyHk1lUG9MVB4yMDI1MDUwOTE4MjE0MS4wHiAg
        H2EwNjc0OTkzMTQ0HiAgH2FNZVBvTFQfY01lUG9MVB9lcmRhHiA0H2FMT0VCLVBBIDYxMjEgLkE0
        IDE5MzUgdi4xHiA0H2E4NzEuMDEeMSAfYVBvZXRzLCBNaW5vciBMYXRpbi4eMTAfYU1pbm9yIExh
        dGluIFBvZXRzLCBWb2x1bWUgSSwgUHVibGlsaXVzIFN5cnVzLiBFbGVnaWVzIG9uIE1hZWNlbmFz
        LiBHcmF0dGl1cy4gQ2FscHVybml1cyBTaWN1bHVzLiBMYXVzIFBpc29uaXMuIEVpbnNpZWRlbG4g
        RWNsb2d1ZXMuIEFldG5hIChMb2ViIENsYXNzaWNhbCBMaWJyYXJ5IE5vLiAyODQpLh4gMR9hTG9l
        YiBDbGFzc2ljYWwgTGlicmFyeSAoMTkzNCksIEVkaXRpb24fYiBSZXZpc2VkLCBIYXJkY292ZXIs
        IDQzMiBwYWdlcywfYzE5MzQuHiAgH2E0MzIgIHAuHiAgH2FNaW5vciBMYXRpbiBQb2V0cywgVm9s
        dW1lIEksIFB1YmxpbGl1cyBTeXJ1cy4gRWxlZ2llcyBvbiBNYWVjZW5hcy4gR3JhdHRpdXMuIENh
        bHB1cm5pdXMgU2ljdWx1cy4gTGF1cyBQaXNvbmlzLiBFaW5zaWVkZWxuIEVjbG9ndWVzLiBBZXRu
        YSAoTG9lYiBDbGFzc2ljYWwgTGlicmFyeSBOby4gMjg0KSBieSBNaW5vciBMYXRpbiBQb2V0cyAo
        MTkzNCkeICAfYUxvZWIeICAfYVlvdXIgbGlicmFyeR4d
    """
    print("Testing with chunk of base64 from librarything marc file:")
    for char in decode_64(msg):
        print(char, end="")
    decoded = "".join([char for char in decode_64(msg)])
    target = "00831     2200193 i 450000100090000000300070000900500170001602000150003304000240004809000300007209200110010210000240011324501760013726400830031330000120039652002030040892000090061192300170062065277402MePoLT20250509182141.0  a0674993144  aMePoLTcMePoLTerda 4aLOEB-PA 6121 .A4 1935 v.1 4a871.011 aPoets, Minor Latin.10aMinor Latin Poets, Volume I, Publilius Syrus. Elegies on Maecenas. Grattius. Calpurnius Siculus. Laus Pisonis. Einsiedeln Eclogues. Aetna (Loeb Classical Library No. 284). 1aLoeb Classical Library (1934), Editionb Revised, Hardcover, 432 pages,c1934.  a432  p.  aMinor Latin Poets, Volume I, Publilius Syrus. Elegies on Maecenas. Grattius. Calpurnius Siculus. Laus Pisonis. Einsiedeln Eclogues. Aetna (Loeb Classical Library No. 284) by Minor Latin Poets (1934)  aLoeb  aYour library"
    assert  decoded == target, f"base64 decodes to\n{decoded}\nShould be:\n{target}\n"

def test_decode_utf8_bin():
    print("\nTesting utf8 decoding from binary. Desired string is 'hello':")
    bin_list = [
        int(char)
        for char in "01101000 01100101 01101100 01101100  01101111"
        if char in {"0", "1"}
    ]
    out = ""
    for i in range(0, 5):
        char = _eval_multibyte(bin_list[i * 8 : (i + 1) * 8])
        print(chr(char), end="")
        out += chr(char)
    assert out == "hello"

    print(
        "\nTesting utf8 decoding from binary with multibyte encoding. Desired string is 'αλφα'."
    )
    encodings = [
        [1, 1, 1, 0, 1, 1, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 1, 1, 0, 1, 1],
        [1, 1, 1, 1, 0, 0, 0, 1, 1, 0],
        [1, 1, 1, 0, 1, 1, 0, 0, 0, 1],
    ]
    out = ""
    for encoding in encodings:
        char = _eval_multibyte(encoding)
        print(chr(char), end="")
        out += chr(char)
    assert out == "αλφα"


    msg = "zrHOu8+GzrEgYWxwaGE="  # encoding for "αλφα alpha"
    print(
        "\nTesting with a chunck of base64 known to contain utf8 multibyte encodings, should decode to 'αλφα alpha'"
    )
    out = ""
    for char in decode_64(msg):
        print(char, end="")
        out += char
    print("\n")
    assert out == "αλφα alpha"

if __name__ == "__main__":
    test_base64()
    test_decode_utf8_bin()
