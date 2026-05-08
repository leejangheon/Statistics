#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import f_oneway
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import sys


def eta_squared(groups):
    all_values = np.concatenate(groups)
    grand_mean = np.mean(all_values)

    ss_between = sum([
        len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups
    ])

    ss_total = sum([
        (x - grand_mean) ** 2 for x in all_values
    ])

    return ss_between / ss_total if ss_total != 0 else np.nan


table = pd.read_csv(sys.argv[1], sep="\t", index_col=0)
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
groups = metadata[group_col]

results = []

for taxa in table.columns:

    df = pd.DataFrame({
        "value": table[taxa],
        "group": groups
    })

    grouped = df.groupby("group")
    group_values = [g["value"].values for _, g in grouped]

    # ANOVA
    stat, p = f_oneway(*group_values)

    # effect size
    eta2 = eta_squared(group_values)

    row = {
        "taxa": taxa,
        "anova_F": stat,
        "anova_p": p,
        "anova_eta2": eta2
    }

    # Tukey HSD
    tukey = pairwise_tukeyhsd(
        endog=df["value"],
        groups=df["group"],
        alpha=0.05
    )

    tukey_df = pd.DataFrame(
        data=tukey._results_table.data[1:],
        columns=tukey._results_table.data[0]
    )

    for _, r in tukey_df.iterrows():
        g1 = str(r["group1"])
        g2 = str(r["group2"])
        key = f"tukey_{g1}_vs_{g2}"

        row[f"{key}_meandiff"] = r["meandiff"]
        row[f"{key}_p"] = r["p-adj"]
        row[f"{key}_reject"] = r["reject"]

    results.append(row)

result_df = pd.DataFrame(results)


# ANOVA FDR correction
result_df["anova_fdr"] = multipletests(
    result_df["anova_p"],
    method="fdr_bh"
)[1]


# 2nd FDR
sig = result_df["anova_p"] < 0.05
result_df["anova_fdr_2nd"] = "."

if sig.sum() > 0:
    result_df.loc[sig, "anova_fdr_2nd"] = multipletests(
        result_df.loc[sig, "anova_p"],
        method="fdr_bh"
    )[1]


result_df.to_csv("anova_tukey_summary.tsv", sep="\t", index=False)