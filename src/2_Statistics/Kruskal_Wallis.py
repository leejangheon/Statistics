#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import numpy as np
from scipy.stats import kruskal
import scikit_posthocs as sp
from statsmodels.stats.multitest import multipletests
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
pairs = list(combinations(groups, 2))
results = []

total_taxa = len(table.columns)

for idx, taxa in enumerate(table.columns, start=1):

    df = pd.DataFrame({
        "value": table[taxa],
        "group": groups
    })

    group_values = [g["value"].values for _, g in df.groupby("group")]
    stat, p = kruskal(*group_values)

    row = {
        "taxa": taxa,
        "kruskal_H": stat,
        "kruskal_p": p
    }

    # Dunn test
    dunn_raw = sp.posthoc_dunn(
        df,
        val_col="value",
        group_col="group",
        p_adjust=None
    )

    dunn_adj = sp.posthoc_dunn(
        df,
        val_col="value",
        group_col="group",
        p_adjust="fdr_bh" 
    )
    for g1, g2 in pairs:
        row[f"dunn_{g1}_vs_{g2}"] = dunn_raw.loc[g1, g2]
        row[f"dunn_{g1}_vs_{g2}_fdr"] = dunn_adj.loc[g1, g2]
 
    results.append(row)
    progress = (idx / total_taxa) * 100
    print(
        f"\rStatistics Processing: {idx}/{total_taxa} "
        f"({progress:.2f}%)",
        end="",
        flush=True
    )
result_df = pd.DataFrame(results)


# Kruskal 1st FDR correction
result_df["kruskal_fdr"] = multipletests(
    result_df["kruskal_p"],
    method="fdr_bh"
)[1]


# Kruskal 2nd FDR correction
sig = result_df["kruskal_p"] < 0.05
result_df["kruskal_fdr_2nd"] = "."
if sig.sum() > 0:
    result_df.loc[sig, "kruskal_fdr_2nd"] = multipletests(
        result_df.loc[sig, "kruskal_p"],
        method="fdr_bh"
    )[1]



result_df.to_csv("kruskal_dunn_summary.tsv", sep="\t", index=False)
