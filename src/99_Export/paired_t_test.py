#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import os
import argparse
from itertools import combinations

parser = argparse.ArgumentParser()

parser.add_argument("--dunn", type=float, default=None, help="paired t-test p-value cutoff (ex. 0.05)")
parser.add_argument("--header", type=str, default=None, help="header Name")
parser.add_argument("--sheet", type=str, default=None, help="sheet Name")
parser.add_argument("--type", type=str, default=None, help="input type")
parser.add_argument("--desc", type=str, default=None, help="description file (optional)")

args = parser.parse_args()

stat = pd.read_csv("Arithmetic_Statistics.tsv", sep="\t")
tt   = pd.read_csv("paired_ttest_summary.tsv", sep="\t")
fc   = pd.read_csv("Log2FC.tsv", sep="\t")
meta = pd.read_csv("metadata.txt", sep="\t",dtype=str)
pair_diff = pd.read_csv("pair_diff.txt", sep="\t")

groups = meta[args.header].unique().tolist()

g1 = groups[0]
g2 = groups[1]

mean_cols = [f"{g}.mean" for g in groups]
se_cols   = [f"{g}.se" for g in groups]

rename_stat = {}

for g in groups:
    rename_stat[f"{g}.mean"] = f"Mean___{g}"
    rename_stat[f"{g}.se"] = f"SE___{g}"

stat2 = stat[["taxa"] + mean_cols + se_cols].rename(columns=rename_stat)

pairs = list(combinations(groups, 2))

fc_rename = {
    f"{g1}_vs_{g2}.log2FC": f"{g1}/{g2}"
    for g1, g2 in pairs
}

fc2 = fc.rename(columns=fc_rename)

tt_cols = [
    "taxa",
    "paired_t.statistic",
    "paired_t.mean_diff",
    "paired_t.pvalue",
    "paired_t.fdr",
    "paired_t.fdr_2nd",
    "n_pairs"
]

tt_rename = {
    "paired_t.statistic": "paired_t.statistic",
    "paired_t.mean_diff": "paired_t.mean_diff",
    "paired_t.pvalue": "p-value",
    "paired_t.fdr": "FDR",
    "paired_t.fdr_2nd": "FDR(2nd)",
    "n_pairs": "n_pairs"
}

tt2 = tt[tt_cols].rename(columns=tt_rename)

df = tt2

df = df.rename(columns={"taxa":"label"})

# pair_diff rename
if args.type == 'it':

    pair_diff_rename = {
        f'({g1}|{g2})':f'Sample ID___({g1}|{g2})',
        f'{g1}': f'Relative abundance (%)___{g1}',
        f'{g2}': f'Relative abundance (%)___{g2}',
        f'({g2} - {g1})': f'증감___({g2} - {g1})'
    }

else:

    pair_diff_rename = {
        f'({g1}|{g2})':f'Sample ID___({g1}|{g2})',
        f'{g1}': f'Abundance___{g1}',
        f'{g2}': f'Abundance___{g2}',
        f'({g2} - {g1})': f'증감___({g2} - {g1})'
    }

pair_diff = pair_diff.rename(columns=pair_diff_rename)

## description 존재시 추가
if args.desc and os.path.exists(args.desc):

    desc = pd.read_csv(args.desc, sep="\t")

    if args.type =="it":

        all_match = (desc["label"] == desc["taxon"]).all()

        if all_match:

            final_cols = ["label"]

            styles = [
                "ws.column_dimensions[get_column_letter(1)].width = 25"
            ]

        else:

            df = df.merge(desc, on="label", how="left")

            final_cols = ["label", "taxon"]

            styles = [
                "ws.column_dimensions[get_column_letter(1)].width = 25",
                "ws.column_dimensions[get_column_letter(2)].width = 30"
            ]

    else:

        all_match = (desc["label"] == desc["description"]).all()

        if all_match:

            final_cols = ["label"]

            styles = [
                "ws.column_dimensions[get_column_letter(1)].width = 25"
            ]

        else:

            df = df.merge(desc, on="label", how="left")

            final_cols = ["label", "description"]

            styles = [
                "ws.column_dimensions[get_column_letter(1)].width = 25",
                "ws.column_dimensions[get_column_letter(2)].width = 30"
            ]

else:

    final_cols = ["label"]

    styles = [
        "worksheet.set_column(0, 0, 25)"
    ]

## 최종 출력 컬럼 지정
final_cols += [
    "paired_t.statistic",
    "paired_t.mean_diff",
    "n_pairs",
    "p-value",
    "FDR",
    "FDR(2nd)"
]

df = df[final_cols]

df = df.sort_values(by="p-value")

df.to_csv("final_summary.tsv", sep="\t", index=False)

sig_labels = df.loc[df["p-value"] < 0.05, "label"]

if len(sig_labels) > 0:

    rows = []

    for label in sig_labels:

        sub = pair_diff[pair_diff["label"] == label].copy()

        pval = df.loc[df["label"] == label, "p-value"].iloc[0]

        sub["Paired t-test___p-value"] = pval

        rows.append(sub)

    df2 = pd.concat(rows, ignore_index=True)

    df2.to_csv("final_diff_summary.tsv", sep="\t", index=False)

    # 최대 row 수
    max_rows = max(len(df), len(df2))

    merged_rows = []

    for i in range(max_rows):

        # df row
        if i < len(df):
            a_row = df.iloc[i].tolist()
        else:
            a_row = [""] * df.shape[1]

        # df2 row
        if i < len(df2):
            b_row = df2.iloc[i].tolist()
        else:
            b_row = [""] * df2.shape[1]

        merged_rows.append(a_row + [""] + b_row)

    # header
    columns = (
        df.columns.tolist()
        + [""]
        + df2.columns.tolist()
    )

    result = pd.DataFrame(merged_rows, columns=columns)

else:

    result = df

## excel report 용 출력
new_cols = []

pcol = []

for i, col in enumerate(result.columns):

    if col == "label":

        new_cols.append(("Label", "Label"))

    elif col == "description":

        new_cols.append(("Description", "Description"))

    elif col == "taxon":

        new_cols.append(("Taxonomy", "Taxonomy"))

    elif "___" in col:

        prefix, suffix = col.split("___", 1)

        new_cols.append((prefix, suffix))

    elif "/" in col:

        new_cols.append(("Log2(FoldChange)", col))

    elif col in [
        "paired_t.statistic",
        "paired_t.mean_diff",
        "n_pairs"
    ]:

        new_cols.append(("Paired t-test", col))

    elif col in ["p-value", "FDR", "FDR(2nd)"]:

        new_cols.append((col, col))

        pcol.append(i)

    elif col == "":

        new_cols.append(("", ""))

result.columns = pd.MultiIndex.from_tuples(new_cols)

header1 = [c[0] for c in result.columns]
header2 = [c[1] for c in result.columns]

min_val = None
pseudo = None

with open("pseudo_count.txt") as f:

    for line in f:

        key, val = line.strip().split("=")

        if key == "min_val":
            min_val = float(val)

        elif key == "pseudo_count":
            pseudo = float(val)

with open("pvalue.columns","w") as fw:
    fw.write(",".join(map(str, pcol)))

styles += [
    "ws.column_dimensions[get_column_letter(7)].width = 25",
    "ws.column_dimensions[get_column_letter(8)].width = 10",
    "ws.column_dimensions[get_column_letter(9)].width = 15",
    "ws.column_dimensions[get_column_letter(10)].width = 15",
    "ws.column_dimensions[get_column_letter(11)].width = 10"
]

with open("final.output", "w") as f:

    f.write("[sheetname]\n%s\n"%(args.sheet))

    f.write("[Title]\nPaired t-test\n")

    f.write(
        f"[SubTitle]\nmin value = {min_val:.6f}, ε={pseudo:.0e}\n"
    )

    # header 1
    f.write("[th]\n")
    f.write("\t".join(header1) + "\n")

    # header 2
    f.write("[th]\n")
    f.write("\t".join(header2) + "\n")

    # data
    f.write("[td]\n")

    for _, row in result.iterrows():
        f.write("\t".join(map(str, row.values)) + "\n")

    # style
    for s in styles:
        f.write("[style]\n%s\n"%(s))