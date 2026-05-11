#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import f_oneway
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import sys

from itertools import combinations

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

table.index = table.index.astype(str)
metadata.index = metadata.index.astype(str)

table = table.loc[metadata.index]

group_col = metadata.columns[0]

groups = metadata[group_col]

groups_ = metadata[group_col].astype(str).unique().tolist()

pairs = list(combinations(groups_, 2))

results = []

total_taxa = len(table.columns)

for idx, taxa in enumerate(table.columns, start=1):

    df = pd.DataFrame({
        "value": pd.to_numeric(
            table[taxa],
            errors="coerce"
        ),
        "group": groups
    }).dropna()

    # group별 값 추출
    group_values = [
        g["value"].values
        for _, g in df.groupby("group")
    ]

    # One-way ANOVA
    stat, p = f_oneway(*group_values)

    row = {
        "taxa": taxa,
        "anova_F": stat,
        "anova_p": p
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

    # pair 결과 저장
    for g1, g2 in pairs:

        match = tukey_df[
            (
                (tukey_df["group1"] == g1)
                & (tukey_df["group2"] == g2)
            )
            |
            (
                (tukey_df["group1"] == g2)
                & (tukey_df["group2"] == g1)
            )
        ]

        if len(match) > 0:

            row[f"tukey_{g1}_vs_{g2}"] = (
                match["p-adj"].values[0]
            )

            row[f"tukey_{g1}_vs_{g2}_reject"] = (
                match["reject"].values[0]
            )

        else:

            row[f"tukey_{g1}_vs_{g2}"] = np.nan

            row[f"tukey_{g1}_vs_{g2}_reject"] = np.nan

    results.append(row)

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

# ANOVA 1st FDR correction
result_df["anova_fdr"] = multipletests(
    result_df["anova_p"],
    method="fdr_bh"
)[1]

# ANOVA 2nd FDR correction
sig = result_df["anova_p"] < 0.05

result_df["anova_fdr_2nd"] = "."

if sig.sum() > 0:

    result_df.loc[sig, "anova_fdr_2nd"] = multipletests(
        result_df.loc[sig, "anova_p"],
        method="fdr_bh"
    )[1]

result_df.to_csv(
    "anova_tukey_summary.tsv",
    sep="\t",
    index=False
)