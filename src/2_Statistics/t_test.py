#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests
import sys


def mean_ci(v1, v2, alpha=0.05):

    v1 = np.asarray(v1, dtype=float)
    v2 = np.asarray(v2, dtype=float)

    v1 = v1[~np.isnan(v1)]
    v2 = v2[~np.isnan(v2)]

    mean_diff = np.mean(v2) - np.mean(v1)

    n1 = len(v1)
    n2 = len(v2)

    s1 = np.var(v1, ddof=1)
    s2 = np.var(v2, ddof=1)

    
    se = np.sqrt((s1 / n1) + (s2 / n2))

    
    df = (
        ((s1 / n1) + (s2 / n2)) ** 2
    ) / (
        ((s1 / n1) ** 2) / (n1 - 1)
        + ((s2 / n2) ** 2) / (n2 - 1)
    )

    from scipy.stats import t

    t_crit = t.ppf(1 - alpha / 2, df)

    ci_low = mean_diff - (t_crit * se)
    ci_high = mean_diff + (t_crit * se)

    return ci_low, ci_high


table = pd.read_csv(
    sys.argv[1],
    sep="\t",
    index_col=0
).T

metadata = pd.read_csv(
    sys.argv[2],
    sep="\t",
    index_col=0,
    dtype=str
)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
groups = metadata[group_col]

unique_groups = groups.astype(str).unique()

if len(unique_groups) != 2:
    raise ValueError(
        f"Expected exactly 2 groups, but got {len(unique_groups)}"
    )

g1, g2 = unique_groups

results = []
pvals = []

total_taxa = len(table.columns)

for idx, taxa in enumerate(table.columns, start=1):

    df = pd.DataFrame({
        "value": table[taxa],
        "group": groups
    })

    v1 = pd.to_numeric(
        df[df["group"] == g1]["value"],
        errors="coerce"
    ).dropna().values

    v2 = pd.to_numeric(
        df[df["group"] == g2]["value"],
        errors="coerce"
    ).dropna().values

    # Welch t-test
    stat, p = ttest_ind(
        v1,
        v2,
        equal_var=False,
        nan_policy="omit"
    )

    # mean difference + 95% CI
    #mean_diff, ci_low, ci_high = mean_ci(v1, v2)

    row = {
        "taxa": taxa,
        "ttest.pvalue": p,
        #"ttest.mean_diff": mean_diff,
        "ttest.CI_low": ci_low,
        "ttest.CI_high": ci_high
    }

    results.append(row)
    pvals.append(p)

    progress = (idx / total_taxa) * 100

    print(
        f"\rStatistics Processing: "
        f"{idx}/{total_taxa} "
        f"({progress:.2f}%)",
        end="",
        flush=True
    )

print("\nDone")

result_df = pd.DataFrame(results)

# FDR
result_df["ttest.fdr"] = multipletests(
    pvals,
    method="fdr_bh"
)[1]

# second FDR
sig = result_df["ttest.pvalue"] < 0.05

result_df["ttest.fdr_2nd"] = "."

if sig.sum() > 0:

    result_df.loc[sig, "ttest.fdr_2nd"] = multipletests(
        result_df.loc[sig, "ttest.pvalue"],
        method="fdr_bh"
    )[1]

result_df.to_csv(
    "ttest_summary.tsv",
    sep="\t",
    index=False
)