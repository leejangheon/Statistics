#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3
import pandas as pd
import numpy as np
import math
import itertools
import sys
from itertools import combinations



table = pd.read_csv(sys.argv[1], sep="\t", index_col=0).T
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0,dtype=str)

table.index = table.index.astype(str)
metadata.index = metadata.index.astype(str)

table = table.loc[metadata.index]



group_col = metadata.columns[0]
groups = metadata[group_col]
groups_ = metadata[group_col].astype(str).unique().tolist()
pairs = list(combinations(groups_, 2))

mean_df   = table.groupby(groups).mean().T
median_df = table.groupby(groups).median().T
std_df    = table.groupby(groups).std().T

n = table.groupby(groups).count()
se_df = (table.groupby(groups).std() / np.sqrt(n)).T


for df_ in [mean_df, median_df, std_df, se_df]:
    df_.index.name = "taxa"


def rename(df, suffix):
    df.columns = [f"{g}.{suffix}" for g in df.columns]
    return df

mean_df   = rename(mean_df, "mean")
median_df = rename(median_df, "median")
std_df    = rename(std_df, "std")
se_df     = rename(se_df, "se")

final = pd.concat([mean_df, median_df, std_df, se_df], axis=1)


group_list = sorted(groups.unique())

ordered_cols = []
for g in group_list:
    ordered_cols += [
        f"{g}.mean",
        f"{g}.median",
        f"{g}.std",
        f"{g}.se"
    ]

final = final[ordered_cols]



min_val = mean_df.replace(0, np.nan).min().min()
n_power = math.ceil(-math.log10(min_val))
pseudo_count = 10 ** (-n_power)

with open("pseudo_count.txt", "w") as f:
    f.write(f"min_val={min_val}\n")
    f.write(f"pseudo_count={pseudo_count}\n")

fc_df = pd.DataFrame(index=mean_df.index)
fc_df.index.name = "taxa"
for g1, g2 in pairs:
    col = f"{g1}_vs_{g2}.log2FC"

    fc_df[col] = np.log2(
        (mean_df[f"{g1}.mean"] + pseudo_count) /
        (mean_df[f"{g2}.mean"] + pseudo_count)
    )

final.to_csv("Arithmetic_Statistics.tsv", sep="\t")
fc_df.to_csv("Log2FC.tsv", sep="\t")
