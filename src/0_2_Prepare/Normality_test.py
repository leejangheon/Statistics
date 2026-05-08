import pandas as pd
from scipy.stats import shapiro

df = pd.read_csv("table.tsv", sep="\t")

results = {}

for col in df.columns[1:]:
    stat, p = shapiro(df[col])
    results[col] = p

print(results)