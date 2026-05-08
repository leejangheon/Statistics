#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests
import sys


def hodges_lehmann_ci(x, y, alpha=0.05):
    diffs = []

    for xi in x:
        for yi in y:
            diffs.append(yi - xi)

    diffs = np.array(diffs)
    diffs_sorted = np.sort(diffs)

  
    hl = np.median(diffs_sorted)


    lower = np.percentile(diffs_sorted, 100 * (alpha / 2))
    upper = np.percentile(diffs_sorted, 100 * (1 - alpha / 2))

    return hl, lower, upper

def wilcox_ci(x, y, alpha=0.05, grid_size=400):

    x = np.asarray(x)
    y = np.asarray(y)

    # clean NA
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]

    # Hodges–Lehmann estimator (R 동일 개념)
    diffs = np.subtract.outer(y, x).ravel()
    hl = np.median(diffs)

    # CI inversion grid
    grid = np.linspace(diffs.min(), diffs.max(), grid_size)

    pvals = np.empty(len(grid))

    for i, d in enumerate(grid):
        _, p = mannwhitneyu(
            x,
            y - d,
            alternative="two-sided",
            method="asymptotic"   
        )
        pvals[i] = p

    valid = grid[pvals > alpha]

    if len(valid) == 0:
        return hl, np.nan, np.nan

    return hl, valid.min(), valid.max()


table = pd.read_csv(sys.argv[1], sep="\t", index_col=0).T
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0,dtype=str)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
groups = metadata[group_col]

unique_groups = groups.astype(str).unique()
if len(unique_groups) != 2:
    raise ValueError(f"Expected exactly 2 groups, but got {len(unique_groups)}")

g1, g2 = unique_groups

results = []
pvals = []

for taxa in table.columns:

    df = pd.DataFrame({
        "value": table[taxa],
        "group": groups
    })

    v1 = df[df["group"] == g1]["value"].values
    v2 = df[df["group"] == g2]["value"].values

    # Wilcoxon rank-sum
    stat, p = mannwhitneyu(v1, v2, alternative="two-sided")

    #  95% CI
    hl, ci_low, ci_high = wilcox_ci(v2, v1)

    row = {
        "taxa": taxa,
        "wilcoxon.pvalue": p,
        "wilcoxon.CI_HL": hl,
        "wilcoxon.CI_low": ci_low,
        "wilcoxon.CI_high": ci_high
    }

    results.append(row)
    pvals.append(p)

result_df = pd.DataFrame(results)

# FDR
result_df["wilcoxon.fdr"] = multipletests(
    pvals,
    method="fdr_bh"
)[1]


sig = result_df["wilcoxon.pvalue"] < 0.05
result_df["wilcoxon.fdr_2nd"] = "."

if sig.sum() > 0:
    result_df.loc[sig, "wilcoxon.fdr_2nd"] = multipletests(
        result_df.loc[sig, "wilcoxon.pvalue"],
        method="fdr_bh"
    )[1]



result_df.to_csv("wilcoxon_summary.tsv", sep="\t", index=False)