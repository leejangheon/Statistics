#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import ttest_rel
from statsmodels.stats.multitest import multipletests
import sys

import warnings
warnings.filterwarnings("ignore")

table = pd.read_csv(sys.argv[1], sep="\t", index_col=0).T
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0,dtype=str)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
pair_col = metadata.columns[1]

groups = metadata[group_col]
pairs = metadata[pair_col]

unique_groups = groups.unique()

if len(unique_groups) != 2:
    raise ValueError(f"Expected exactly 2 groups, but got {len(unique_groups)}")

g1, g2 = unique_groups

results = []
pvals = []

total_taxa = len(table.columns)

for idx, taxa in enumerate(table.columns, start=1):

    df = pd.DataFrame({
        "value": pd.to_numeric(table[taxa], errors="coerce"),
        "group": groups,
        "pair": pairs
    })

    pivot = df.pivot_table(
        index="pair",
        columns="group",
        values="value"
    )

    pivot = pivot.dropna()

    if g1 not in pivot.columns or g2 not in pivot.columns:
        continue

    v1 = pivot[g1].values
    v2 = pivot[g2].values

    # paired t-test 는 최소 2쌍 필요
    if len(v1) < 2:
        continue

    # paired t-test
    stat, p = ttest_rel(v1, v2, nan_policy="omit")

    row = {
        "taxa": taxa,
        "paired_t.statistic": stat,
        "paired_t.pvalue": p,
        "paired_t.mean_diff": np.mean(v1 - v2),
        "n_pairs": len(v1)
    }

    results.append(row)
    pvals.append(p)

    progress = (idx / total_taxa) * 100

    print(
        f"\rStatistics Processing: {idx}/{total_taxa} "
        f"({progress:.2f}%)",
        end="",
        flush=True
    )

print()

result_df = pd.DataFrame(results)

# FDR
result_df["paired_t.fdr"] = multipletests(
    pvals,
    method="fdr_bh"
)[1]

# 2nd FDR
sig = result_df["paired_t.pvalue"] < 0.05

result_df["paired_t.fdr_2nd"] = "."

if sig.sum() > 0:

    result_df.loc[sig, "paired_t.fdr_2nd"] = multipletests(
        result_df.loc[sig, "paired_t.pvalue"],
        method="fdr_bh"
    )[1]

result_df.to_csv(
    "paired_ttest_summary.tsv",
    sep="\t",
    index=False
)