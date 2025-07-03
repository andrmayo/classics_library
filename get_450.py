import pandas as pd
from csvconv import to_marc

df = pd.read_csv("librarything_UMClassics_all.csv")
df = df.iloc[0:450]
df.to_csv("450_records.csv", index=False)
to_marc("450_records.csv", "450_records.marc")
