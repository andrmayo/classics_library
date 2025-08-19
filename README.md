# MARC processing for library catalogue transfer

This code is mainly written for the specific job of cleaning up catalogue data for the library of the umich Classics Department
so that it can be transferred from [LibraryThing](https://www.librarything.com/home)
to [Library World](https://www.libraryworld.com/?gad_source=1&gad_campaignid=246226816&gclid=CjwKCAjwuIbBBhBvEiwAsNypvV_slYhKaBxVixHdfyughsF8_c2PneMv10bIzrzCXemZOxYBYRd55RoCsfUQAvD_BwE).
The main reasons this proved somewhat challenging is that LibraryThing exported marc records in marc8 encoding.
Further, the export file (`librarything_UMClassics.marc`) is a mix of records simply encoded in marc8, and marc8 encoding
base64 representations of marc records in utf-8.

## Converting between marc and csv files

The script `csvconv.py` can be used from the CLI to convert between marc and csv formats.
If the file passed on the CLI has a `marc`, `mrc`, or `dat` extension, the script will try to convert it
to csv format.
If the file has a `csv` extension, it will instead be converted to marc format.
The csv files produced here should preserve all data, including leaders, indicators, and subfields, necessary to
convert back to marc format.
Code for working with this csv representation of marc records can be found in `marccsv.py`.

I mainly wrote this to make it straightforward to handle the catalogue data with pandas or simply as a spreadsheet,
which is handy when working alongside people unfamiliar with XML and JSON. Otherwise, the `Pymarc` JSON serialization could
easily be used here.

## MARC files with base64 encoding

The code to deal with disentangling records in a mix of a one-byte encoding like marc8 or Latin1 and base64 representation of utf-8
is in `mixedmarc.py` and `base64utils.py`. As an exercise, I implemented the base64 decoding myself, but really it would make sense to use the Python `base64` module.

## non-ASCII characters and Library World

Because Library World uses Latin1 for import, simply converting everything to utf-8 doesn't work. However, this can be solved by editing the marc
records such that all non-ASCII characters are replaced by their html representations. The code to do so is contained in
`htmlutils.py` and `marccsv.py`.

## Prepping LibraryThing export for Library World import

The process of disentangling the different record encodings, converting them to a csv serialization with utf-8 encoding, replacing all
non-ASCII characters with html entity representations, and converting back to marc format is done by `process_libthing.py`.

The final output file in marc format is `librarything_UMClassics_all.marc`.

## Test data

A simple case, without complex subfield structures or base64 encoding, is the file `PGA-Australiana.csv` in this repo,
which is set up to be usable with `pytest` in the `testing` directory.
