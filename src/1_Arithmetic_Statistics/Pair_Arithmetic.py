#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3
import pandas as pd
import numpy as np
import math
import itertools
import sys

table = pd.read_csv(sys.argv[1], sep="\t", index_col=0).T
metadata = pd.read_csv(sys.argv[2], sep="\t", index_col=0,dtype=str)

# align
table = table.loc[metadata.index]

group_col = metadata.columns[0]
pair_col = metadata.columns[1]

groups = metadata[group_col]
unique_groups = metadata[group_col].unique()
g1, g2 = unique_groups[0], unique_groups[1]
pairs = metadata[pair_col]




results = []
unique_pairs = pairs.unique()

for p in unique_pairs:
    pair_indices = metadata[metadata[pair_col] == p].index
    id_a = metadata.loc[pair_indices][metadata.loc[pair_indices, group_col] == g1].index[0]
    id_b = metadata.loc[pair_indices][metadata.loc[pair_indices, group_col] == g2].index[0]


    row_a = table.loc[id_a]

    row_b = table.loc[id_b]

    for label in table.columns:
        val_a = row_a[label]
        val_b = row_b[label]
        
        diff = val_b - val_a
        status = "증가" if diff > 0 else ("감소" if diff < 0 else "-")
        
        results.append({
            'label': label,
            f'({g1}|{g2})': f"{id_a}|{id_b}",
            f'{g1}': val_a,
            f'{g2}': val_b,
            f'({g2} - {g1})': status
        })

# 3. 결과 출력
final_df = pd.DataFrame(results)
#print(final_df.to_string(index=False), sep="\t")
final_df.to_csv('pair_diff.txt', index=False, sep="\t")