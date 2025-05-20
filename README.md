# MARC processing for library catalogue transfer

This code is mainly written for the specific job of cleaning up catalogue data for the library of the umich Classics Department
so that it can be transferred from [LibraryThing](https://www.librarything.com/home)
to [Library World](https://www.libraryworld.com/?gad_source=1&gad_campaignid=246226816&gclid=CjwKCAjwuIbBBhBvEiwAsNypvV_slYhKaBxVixHdfyughsF8_c2PneMv10bIzrzCXemZOxYBYRd55RoCsfUQAvD_BwE).

## Converting between marc and csv files

The script `convert_csv.py` can be used from the CLI to convert between marc and csv formats.
If the file passed on the CLI has a `marc`, `mrc`, or `dat` extension, the script will try to convert it
to csv format.
If the file has a `csv` extension, it will instead be converted to marc format.
The csv files produced here should preserve all data, including leaders, indicators, and subfields, necessary to
convert back to marc format.

I mainly wrote this to make it straightforward to handle the catalogue data with pandas.

## MARC files with base64 encoding

## Test data

A simple case, without complex subfield structures or base64 encoding, is the file `PGA-Australiana.csv` in this repo.

## Oddities of LibraryThing marc export

The export to marc option in LibraryThing purports to use utf8 encodings
exclusively. This does not always seems to be the case, however.
When I export to marc, it seems to use a LATIN1 encoding,
which can be converted to utf-8 with `iconv -f LATIN1 -t UTF-8 < librarything_UMClassics.marc > librarything_UMClassics_utf8.marc`.
I am not sure if this is consistently how it behaves.

## TODO

There's an issue with base64 decoding with some extended Latin characters,
e.g. à.
