#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# input
method = sys.argv[1]

stat = pd.read_csv("processed.txt", sep="\t")
meta = pd.read_csv("metadata.txt", sep="\t", dtype=str)

if method == "Kruskal":
    test      = pd.read_csv("kruskal_dunn_summary.tsv", sep="\t")
    header    = "kruskal_p"
    method_s  = "Kruskal-Wallis, p"

elif method == "Wilcoxon":
    test      = pd.read_csv("wilcoxon_summary.tsv", sep="\t")
    header    = "wilcoxon.pvalue"
    method_s  = "Mann–Whitney U test, p"

elif method == "Wilcoxon_pair":
    test      = pd.read_csv("wilcoxon_paired_summary.tsv", sep="\t")
    header    = "wilcoxon.pvalue"
    method_s  = "Wilcoxon signed-rank test, p"

elif method == "anova":
    test      = pd.read_csv("anova_tukey_summary.tsv", sep="\t")
    header    = "anova_p"
    method_s  = "1Way ANOVA, p"

elif method == "t_test":
    test      = pd.read_csv("ttest_summary.tsv", sep="\t")
    header    = "ttest.pvalue"
    method_s  = "t-test, p"

elif method == "paired_t":
    test      = pd.read_csv("paired_ttest_summary.tsv", sep="\t")
    header    = "paired_t.pvalue"
    method_s  = "Paired t-test, p"

else:
    raise ValueError(f"Unsupported method: {method}")

# paired analysis 여부
#paired_methods = ["Wilcoxon_pair", "paired_t"]
paired_methods=[]
is_paired = method in paired_methods

# output
os.makedirs("boxplot", exist_ok=True)

# metadata columns
sample_col = meta.columns[0]
group_col  = meta.columns[1]

if is_paired:
    pair_col = meta.columns[2]

# significant taxa only
sig_taxa = test.loc[test[header] < 0.05, "taxa"].tolist()

print(f"[INFO] Significant taxa count : {len(sig_taxa)}")

# group order
group_order = meta[group_col].drop_duplicates().tolist()

# custom palette
mycol = [
    "#84BD00", "#F5543F", "#2980b9", "#fed439ff",
    "#9e9e9e", "#f781bf", "#001e62", "#4daf4a",
    "#ff9432", "#00bfb2", "#a765c2", "#d2af81ff",
    "#e0ff99", "#f99386", "#99b8ff", "#fee99a",
    "#cccccc", "#fccfe7", "#c0def2", "#95d293",
    "#ffca99", "#99fff8", "#d6b6e2", "#e3cfb5"
]

group_colors = {
    group: mycol[i % len(mycol)]
    for i, group in enumerate(group_order)
}

for taxa in sig_taxa:

    row = stat[stat["label"] == taxa]

    if row.empty:
        print(f"[SKIP] {taxa} not found")
        continue

    values = row.iloc[0, 1:]

    plot_df = pd.DataFrame({
        sample_col: values.index,
        "Value": pd.to_numeric(values.values, errors="coerce")
    })

    # metadata merge
    if is_paired:

        plot_df = plot_df.merge(
            meta[[sample_col, group_col, pair_col]],
            on=sample_col,
            how="left"
        )

    else:

        plot_df = plot_df.merge(
            meta[[sample_col, group_col]],
            on=sample_col,
            how="left"
        )

    plot_df = plot_df.dropna(subset=["Value", group_col])

    plt.figure(figsize=(6, 5))

    # boxplot
    ax = sns.boxplot(
        data=plot_df,
        x=group_col,
        y="Value",
        hue=group_col,
        order=group_order,
        palette=group_colors,
        showcaps=True,
        showfliers=False,
        width=0.6,
        linewidth=1,
        medianprops=dict(color="black", linewidth=2),
        boxprops=dict(alpha=0.8),
        dodge=False,
        legend=False
    )
    # paired dashed line
    if is_paired:

        x_map = {g: i for i, g in enumerate(group_order)}

        for pair_id, subdf in plot_df.groupby(pair_col):

            if subdf[group_col].nunique() < 2:
                continue

            subdf = subdf.sort_values(group_col)

            x = [x_map[g] for g in subdf[group_col]]
            y = subdf["Value"].tolist()

            ax.plot(
                x,
                y,
                linestyle="--",
                color="gray",
                linewidth=1,
                alpha=0.7,
                zorder=1
            )

    # sample points
    sns.stripplot(
        data=plot_df,
        x=group_col,
        y="Value",
        order=group_order,
        color="black",
        dodge=False,
        size=5,
        jitter=0.15,
        edgecolor="black",
        linewidth=0,
        zorder=3,
        ax=ax
    )

    # legend
    legend_handles = [
        Patch(
            facecolor=group_colors[g],
            edgecolor="black",
            linewidth=1,
            label=g
        )
        for g in group_order
    ]

    ax.legend(
        handles=legend_handles,
        title=group_col,
        loc="best",
        frameon=False
    )

    # pvalue
    pval = test.loc[test["taxa"] == taxa, header].values[0]

    # title
    ax.text(
        0.0,
        1.08,
        taxa,
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        ha="left"
    )

    ax.text(
        0.0,
        1.02,
        f"{method_s} = {pval:.3e}",
        transform=ax.transAxes,
        fontsize=11,
        color="dimgray",
        ha="left"
    )

    plt.xlabel("")
    plt.ylabel(taxa)

    sns.despine()

    plt.tight_layout()

    outpng = f"boxplot/{taxa}.png"

    plt.savefig(
        outpng,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"[SAVE] {outpng}")