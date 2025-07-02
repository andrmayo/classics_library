import sys
from pathlib import Path
from pymarc import MARCReader

if len(sys.argv) == 1:
    print("Please provide path to file containing marc records.")
    sys.exit()
filepath = Path(sys.argv[1])
if not filepath.exists():
    print(f"File {filepath} not found")
    sys.exit()
with open(filepath, "rb") as f:
    reader = MARCReader(f, force_utf8=True)
    count = 0
    for record in reader:
        count += 1
print(f"File {filepath} contains {count} marc records")



