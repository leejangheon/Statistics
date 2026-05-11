#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3
import pandas as pd
import numpy as np
import argparse


def clr_transform(df, pseudocount):
    df = df + pseudocount
    log_df = np.log(df)
    gm = log_df.mean(axis=1)
    clr = log_df.sub(gm, axis=0)
    return clr


def main( input_file, output_file,metadata_file, do_clr, pseudocount):

    meta = pd.read_csv(metadata_file, sep="\t",dtype=str)
    meta_ids = set(meta.iloc[:,0])
    meta_first_col = meta.columns[0]
    
   
    df = pd.read_csv(input_file, sep="\t")
    first_col = df.columns[0]
    df_indexed = df.set_index(first_col)
  
    row_match = sum(r in meta_ids for r in df_indexed.index)
    col_match = sum(c in meta_ids for c in df_indexed.columns)

    print("col match:", col_match)
    print("row match:", row_match)

 
    if col_match == 0 and row_match == 0:
        raise ValueError("FAIL: No matching SampleID")

    if col_match > row_match:
        print("OK")
        df = df_indexed
    else:
        print("Transpose table")
        df = df.set_index(first_col)
        df = df.T

 
    df = df.loc[:, df.columns.intersection(meta_ids)]

   
    
    if do_clr:
        print(f"Apply CLR transform (pseudocount={pseudocount})")
        df = clr_transform(df, pseudocount)
   
    

    if "SampleID" in df.columns:
        print("SampleID column already exists")
    else:
        df.index.name = "Variable"
        df = df.reset_index()
    
    df.to_csv(output_file, sep="\t", index=False)



def mapping(file_):
    import os
    import shutil
   
  
    src = os.path.abspath(file_)

    
    if not os.path.isfile(src):
        print(f"[ERROR] File not found: {src}")
        return False

    dst = os.path.abspath("./mapping.txt")

  
    if src == dst:
        print("[INFO] Source and destination are same file. Skip copy.")
        return True

   
    shutil.copy2(src, dst)
    print(f"[INFO] Saved -> {dst}")
    return True

  
if __name__ == "__main__":

    import sys
    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        False,
        1
    )
    if len(sys.argv) > 4:
        mapping(sys.argv[4])
    