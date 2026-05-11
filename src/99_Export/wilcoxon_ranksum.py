#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3

import pandas as pd
import os
import argparse
from itertools import combinations


parser = argparse.ArgumentParser()
parser.add_argument("--dunn", type=float, default=None, help="Dunn p-value cutoff (ex. 0.05)")
parser.add_argument("--header", type=str, default=None, help="header Name")
parser.add_argument("--sheet", type=str, default=None, help="sheet Name")
parser.add_argument("--type", type=str, default=None, help="input type")
parser.add_argument("--desc", type=str, default=None, help="description file (optional)")

args = parser.parse_args()

stat = pd.read_csv("Arithmetic_Statistics.tsv", sep="\t")
wd   = pd.read_csv("wilcoxon_summary.tsv", sep="\t")
fc   = pd.read_csv("Log2FC.tsv", sep="\t")
meta = pd.read_csv("metadata.txt", sep="\t",dtype=str)


groups = meta[args.header].unique().tolist()


## << 컬럼명 변경 작업  진행 >>
mean_cols = [f"{g}.mean" for g in groups]
se_cols   = [f"{g}.se"   for g in groups]
rename_stat = {}
for g in groups:
    rename_stat[f"{g}.mean"] = f"Mean___{g}"
    rename_stat[f"{g}.se"]   = f"SE___{g}"
stat2 = stat[["taxa"] + mean_cols + se_cols].rename(columns=rename_stat)

pairs = list(combinations(groups, 2))
fc_rename = {
    f"{g1}_vs_{g2}.log2FC": f"{g1}/{g2}"
    for g1, g2 in pairs
}
fc2 = fc.rename(columns=fc_rename)


wd_cols = ["taxa", "wilcoxon.pvalue", "wilcoxon.fdr", "wilcoxon.fdr_2nd"] + \
          ["wilcoxon.CI_low","wilcoxon.CI_high" ]

wd_rename = {
    "wilcoxon.pvalue": "p-value",
    "wilcoxon.fdr": "FDR",
    "wilcoxon.fdr_2nd": "FDR(2nd)",
    "wilcoxon.CI_low":"wilcoxon.CI_Lower",
    "wilcoxon.CI_high":"wilcoxon.CI_Upper" 

}

wd2 = wd[wd_cols].rename(columns=wd_rename)
df = stat2.merge(fc2, on="taxa").merge(wd2, on="taxa")

df=df.rename(columns={"taxa":"label"})



## description 존재시 추가 
if args.desc and os.path.exists(args.desc):
    desc = pd.read_csv(args.desc, sep="\t")

    if args.type =="it":
        # label랑 taxon 모두 동일하면 label만 작성
        all_match = (desc["label"] == desc["taxon"]).all()
        if (all_match):
            final_cols = ["label"]
            styles=["ws.column_dimensions[get_column_letter(1)].width = 25"]
        else:
            df = df.merge(desc, on="label", how="left")
            final_cols = ["label", "taxon"]
            styles=["ws.column_dimensions[get_column_letter(1)].width = 25","ws.column_dimensions[get_column_letter(2)].width = 30"]
    else:
    
        # desc랑 label이 모두 동일하면 label만 작성
        all_match = (desc["label"] == desc["description"]).all()
        if (all_match):
            final_cols = ["label"]
            styles=["ws.column_dimensions[get_column_letter(1)].width = 25"]
    
        else:
            df = df.merge(desc, on="label", how="left")
            final_cols = ["label", "description"]
            styles=["ws.column_dimensions[get_column_letter(1)].width = 25","ws.column_dimensions[get_column_letter(2)].width = 30"]
else:
    final_cols = ["label"]
    styles=["worksheet.set_column(0, 0, 25)"]
        #df["description"] = None



## 최종 출력 컬럼 지정 
for g in groups:
    final_cols.append(f"Mean___{g}")
for g in groups:
    final_cols.append(f"SE___{g}")
for g1, g2 in pairs:
    final_cols.append(f"{g1}/{g2}")

# Stats
final_cols += ["wilcoxon.CI_Lower","wilcoxon.CI_Upper" ,"p-value", "FDR", "FDR(2nd)"]

df = df[final_cols]

df = df.sort_values(by="p-value")
df.to_csv("final_summary.tsv", sep="\t", index=False)


## excel report 용 출력 
new_cols = []
pcol=[]

for i, col in enumerate(df.columns):
    if col == "label":
        new_cols.append(("Label", "Label"))
    
    elif col == "description":
        new_cols.append(("Description", "Description"))

    elif col == "taxon":
        new_cols.append(("Taxonomy", "Taxonomy"))

    elif "wilcoxon.CI" in col:
        prefix, suffix = col.split("_", 1)
        new_cols.append(("95% Confidence Interval", suffix))
     
    elif "___" in col:
        prefix, suffix = col.split("___", 1)
        new_cols.append((prefix, suffix))
    
    elif "/" in col:
        new_cols.append(("Log2(FoldChange)", col))
    
    elif col in ["p-value", "FDR", "FDR(2nd)"]:
        new_cols.append((col, col))
        pcol.append(i)
    
    #else:
    #    new_cols.append(("Other", col))

df.columns = pd.MultiIndex.from_tuples(new_cols)

header1 = [c[0] for c in df.columns]
header2 = [c[1] for c in df.columns]

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


with open("final.output", "w") as f:
    f.write("[sheetname]\n%s\n"%(args.sheet))
    f.write("[Title]\nWilcoxon Rank Sum Test (unpaired)\n")
    f.write(f"[SubTitle]\nmin value = {min_val:.6f}, ε={pseudo:.0e}\n")

    # header 1
    f.write("[th]\n")
    f.write("\t".join(header1) + "\n")

    # header 2
    f.write("[th]\n")
    f.write("\t".join(header2) + "\n")

    # data
    f.write("[td]\n")
    for _, row in df.iterrows():
        f.write("\t".join(map(str, row.values)) + "\n")

    # style 
    for s in styles:
        f.write("[style]\n%s\n"%(s))
    # f.write("[style]\nrange=B4:B20;data_bar=true\n")
