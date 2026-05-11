#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3
import pandas as pd
import numpy as np
import argparse

from scipy.stats import shapiro

def normality_test_by_row(df_numeric):
   

    results = []

    for idx, row in df_numeric.iterrows():

       
        values = pd.to_numeric(row, errors="coerce").dropna()

        
        if len(values) < 3:
            pvalue = np.nan
            stat = np.nan
            note = "less_than_3_samples"

      
        elif values.nunique() == 1:
            pvalue = np.nan
            stat = np.nan
            note = "all_values_identical"

        else:
            try:
                stat, pvalue = shapiro(values)
                note = "OK"

            except Exception as e:
                stat = np.nan
                pvalue = np.nan
                note = str(e)

        results.append([
            idx,
            stat,
            pvalue,
            len(values),
            note
        ])

    result_df = pd.DataFrame(
        results,
        columns=[
            "Variable",
            "Shapiro_W",
            "Pvalue",
            "N",
            "Status"
        ]
    )

    return result_df


def main( input_file,metadata_file):

    meta = pd.read_csv(metadata_file, sep="\t",dtype=str)
    meta_ids = set(meta.iloc[:,0])
    meta_first_col = meta.columns[0]
    
   
    df = pd.read_csv(input_file, sep="\t")
    first_col = df.columns[0]
    df_indexed = df.set_index(first_col)
  
    row_match = sum(r in meta_ids for r in df_indexed.index)
    col_match = sum(c in meta_ids for c in df_indexed.columns)

    #print("col match:", col_match)
    #print("row match:", row_match)

 
    if col_match == 0 and row_match == 0:
        raise ValueError("FAIL: No matching SampleID")

    if col_match > row_match:
        #print("OK")
        df = df_indexed
    else:
        #print("Transpose table")
        df = df.set_index(first_col)
        df = df.T

 
    df = df.loc[:, df.columns.intersection(meta_ids)]

   
    

   
    df.index.name = "Variable"
    
    
    #df.to_csv(output_file, sep="\t", index=False)
    df_numeric = df.apply(pd.to_numeric, errors="coerce")
    normality_result = normality_test_by_row(df_numeric)
    normality_result["Normality"] = np.where(normality_result["Pvalue"] > 0.05,"PASS","FAIL")
    normality_result.to_csv("normality_result.txt", sep="\t",index=False)

    pass_count = (normality_result["Normality"] == "PASS").sum()
    total_count = len(normality_result)
    pass_ratio = round((pass_count / total_count) * 100, 2)
    if pass_ratio >= 50:
        test_type = "모수/Parametric"
    else:
        test_type = "비모수/Non-parametric"


    summary_msg = f"""
==================================================
              Normality Test Summary
==================================================

Input File        : {input_file}

Recommended Method
  -> {test_type}

Normality Result
  PASS            : {pass_count}
  TOTAL           : {total_count}
  PASS Ratio      : {pass_ratio}%

==================================================
"""

    print(summary_msg)
    with open("normality_summary.txt", "w") as f:
        f.write(f"{test_type}\n")
        f.write(f"Normality : {pass_count} / {total_count} ({pass_ratio}%)")

if __name__ == "__main__":

    import sys
    main(
        sys.argv[1],
        sys.argv[2]
    )
  