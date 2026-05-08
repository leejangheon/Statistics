#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests
import sys


def cohens_d(x, y):
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2

    pooled_std = np.sqrt(
        ((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / dof
    )

    return (np.mean(y) - np.mean(x)) / pooled_std


def mean_diff_ci(x, y, alpha=0.05):
    nx = len(x)
    ny = len(y)

    mean_diff = np.mean(y) - np.mean(x)

    var_x = np.var(x, ddof=1)
    var_y = np.var(y, ddof=1)

    se = np.sqrt(var_x / nx + var_y / ny)

    # Welch-Satterthwaite df
    df = (var_x / nx + var_y / ny) ** 2 / (
        (var_x**2) / (nx**2 * (nx - 1)) +
        (var_y**2) / (ny**2 * (ny - 1))
    )

    from scipy.stats import t
    t_crit = t.ppf(1 - alpha / 2, df)

    lower = mean_diff - t_crit * se
    upper = mean_diff + t_crit * se

    return mean_diff, lower, upper


table = pd.read_csv(sys.argv[1], sep="\t", index_col=0)
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
groups = metadata[group_col]

unique_groups = groups.unique()
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

    # Welch t-test
    stat, p = ttest_ind(v1, v2, equal_var=False)

    # mean difference + CI
    mean_diff, ci_low, ci_high = mean_diff_ci(v1, v2)

    # effect size
    d = cohens_d(v1, v2)

    row = {
        "taxa": taxa,
        "ttest.statistic": stat,
        "ttest.pvalue": p,
        "ttest.mean_diff": mean_diff,
        "ttest.CI_low": ci_low,
        "ttest.CI_high": ci_high,
        "ttest.cohens_d": d
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

result_df.to_csv("ttest_summary.tsv", sep="\t", index=False)