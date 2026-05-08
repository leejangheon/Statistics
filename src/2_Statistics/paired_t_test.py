#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, t
from statsmodels.stats.multitest import multipletests
import sys


def paired_cohens_d(x, y):
    diff = y - x
    return np.mean(diff) / np.std(diff, ddof=1)


def mean_diff_ci_paired(x, y, alpha=0.05):
    diff = y - x
    n = len(diff)

    mean_diff = np.mean(diff)
    se = np.std(diff, ddof=1) / np.sqrt(n)

    t_crit = t.ppf(1 - alpha / 2, df=n - 1)

    lower = mean_diff - t_crit * se
    upper = mean_diff + t_crit * se

    return mean_diff, lower, upper


table = pd.read_csv(sys.argv[1], sep="\t", index_col=0)
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0)

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

for taxa in table.columns:

    df = pd.DataFrame({
        "value": table[taxa],
        "group": groups,
        "pair": pairs
    })

    # pivot to paired format
    pivot = df.pivot_table(
        index="pair",
        columns="group",
        values="value"
    )

    # drop incomplete pairs
    pivot = pivot.dropna()

    if g1 not in pivot.columns or g2 not in pivot.columns:
        continue

    v1 = pivot[g1].values
    v2 = pivot[g2].values

    if len(v1) < 2:
        continue

    # paired t-test
    stat, p = ttest_rel(v1, v2)

    # mean diff + CI
    mean_diff, ci_low, ci_high = mean_diff_ci_paired(v1, v2)

    # effect size
    d = paired_cohens_d(v1, v2)

    row = {
        "taxa": taxa,
        "ttest.statistic": stat,
        "ttest.pvalue": p,
        "ttest.mean_diff": mean_diff,
        "ttest.CI_low": ci_low,
        "ttest.CI_high": ci_high,
        "ttest.cohens_d": d,
        "n_pairs": len(v1)
    }

    results.append(row)
    pvals.append(p)

result_df = pd.DataFrame(results)

# FDR
result_df["ttest.fdr"] = multipletests(
    pvals,
    method="fdr_bh"
)[1]


sig = result_df["ttest.pvalue"] < 0.05
result_df["ttest.fdr_2nd"] = "."

if sig.sum() > 0:
    result_df.loc[sig, "ttest.fdr_2nd"] = multipletests(
        result_df.loc[sig, "ttest.pvalue"],
        method="fdr_bh"
    )[1]

result_df.to_csv("paired_ttest_summary.tsv", sep="\t", index=False)