#!/garnet2/Tools/META_Analysis/Tools/miniconda3/bin/python3
import pandas as pd
import xlsxwriter

def parse_input(file,pvalue):
    sheetname = None
    title = None
    subtitle = None
    headers = []
    rows = []
    styles = []
    current_tag = None
    plist=[]

    with open(file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current_tag = line
                continue

            if current_tag == "[sheetname]":
                sheetname = line

            elif current_tag == "[Title]":
                title = line

            elif current_tag == "[SubTitle]":
                subtitle = line

            elif current_tag == "[th]":
                headers.append(line.rstrip().split("\t"))

            elif current_tag == "[td]":
                rows.append(line.rstrip().split("\t"))

            elif current_tag == "[style]":
                styles.append(line)
    with open(pvalue) as f:
        line = f.read().strip() 
    plist = [int(x) for x in line.split(",")]

    return sheetname, title, subtitle, headers, rows, styles,plist


def merge_headers(ws, headers, start_row, fmt):

    nrow = len(headers)
    ncol = len(headers[0])

    for r in range(nrow):
        row = headers[r]
        c = 0
        while c < ncol:
            start = c
            val = row[c]
            if val == "":
                c+=1
                continue
            while c + 1 < ncol and row[c + 1] == val:
                c += 1
            end = c
            if start != end:
                ws.merge_range(start_row+r, start, start_row+r, end, val, fmt)
            else:
                ws.write(start_row+r, start, val, fmt)
            c += 1

    
    for c in range(ncol):
        r = 0
        while r < nrow-1:
            if headers[r][c] == headers[r+1][c]:
                start = r
                val = headers[r][c]
                if val == "":
                    r+=1
                    continue
                while r+1 < nrow and headers[r+1][c] == val:
                    r += 1
                end = r
                ws.merge_range(start_row+start, c, start_row+end, c, val, fmt)
            r += 1


def apply_styles(worksheet, workbook, styles):
    for s in styles:
        eval(s)


def convert_value(x,workbook):
    data1_fmt = workbook.add_format({
        "bold": False,
        "align": "left",
        "valign": "vcenter",
        #"bg_color": "#4F81BD",
        "font_color": "black",
        "font_size": 10,
        #"font_name": "Calibri",
        "border": 1
    })

    data2_fmt = workbook.add_format({
        "bold": False,
        "align": "center",
        "valign": "vcenter",
        #"bg_color": "#4F81BD",
        "font_color": "black",
        "font_size": 10,
        "border": 1
    })

    empty_fmt = workbook.add_format({
        "bold": False,
        "align": "center",
        "valign": "vcenter",
        #"bg_color": "#4F81BD",
        "font_color": "black",
        "font_size": 10,
        #"border": 1
    })

    if x in ["None", ".", "","nan"]:
        return ".",data1_fmt
    elif x=="":
        return "",empty_fmt
    
    try:
        return float(x),data2_fmt
    except:
        return x ,data1_fmt

def write_sheet(workbook, parsed):

    sheetname, title, subtitle, headers, rows, styles ,plist= parsed
    ws = workbook.add_worksheet(sheetname)

    header_fmt = workbook.add_format({
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#dce6f1",
        "font_color": "black",
        "font_size": 10,
        "border": 1
    })

    headers_count=len(headers[0])

    title_fmt = workbook.add_format({
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "bg_color": "#dce6f1",
        "font_size": 16,
        "border": 1
    })

    sub_title_fmt = workbook.add_format({
        "valign": "vcenter",
        "font_size": 9,
    })

    # Title
    ws.merge_range(0, 0, 0, headers_count-1, title, title_fmt)
    ws.set_row(0, 40)
    ws.merge_range(1, headers_count-3, 1, headers_count-1, subtitle, sub_title_fmt)

    # header
    start_row = 3
    merge_headers(ws, headers, start_row, header_fmt)

    # data
    df = pd.DataFrame(rows, columns=headers[-1])

    for i, r in df.iterrows():
        for j, v in enumerate(r):
            v1,fmt=convert_value(v,workbook)
            ws.write(start_row + len(headers) + i, j, v1,fmt)

    # style
    apply_styles(ws, workbook, styles)

    # pvalue
    max_row = len(df)+4
    red_format = workbook.add_format({'font_color': 'red'})

    for pcol in plist:
        ws.conditional_format(start_row+2, pcol, max_row, pcol, {
            'type': 'cell',
            'criteria': '<',
            'value': 0.05,
            'format': red_format
        })

def main_page():
    # get lims

    # make front page
    
    pass

if __name__ == "__main__":

    orderNumber=sys.argv[1]
    dirs = sys.argv[2:]

    if len(dirs) == 0:
        print("Usage: python script.py dir1 dir2 ...")
        sys.exit(1)


    workbook = xlsxwriter.Workbook("output.xlsx")

    for d in dirs:
        file = os.path.join(d, "final.output")
        pval = os.path.join(d, "pvalue.columns")
        parsed = parse_input(file, pval)
        write_sheet(workbook, parsed)

    workbook.close()