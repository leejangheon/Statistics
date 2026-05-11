#!/bin/sh

# 2026.04.29 요약 :  ASV -> 정규성 검사 X 

## 사용방법 
function help() {

    echo ""
    echo "======================================================================"
    echo "                     Normality Test Pipeline"
    echo "======================================================================"
    echo ""

    echo "Usage:"
    echo "  sh $0 [OPTIONS]"
    echo ""

    echo "Required Options:"
    echo "  -m,  --metadata     Metadata file"
    echo "  -ic                 Input abundance table"
    echo ""

    echo "Optional Options:"
    echo "  -c, --config        Config directory"
    echo "                      Default :"
    echo "                      /garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config"
    echo ""

    echo "Output:"
    echo "  ./Normality"
    echo ""

    echo "======================================================================"
    echo ""

  
}


input=""
metadata=""
config=/garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config

while [ $# -gt 0 ]; do
    case "$1" in
       
        -m|--metadata)
            metadata=$2
            shift 2
            ;;
       
        -ic)
            input=$2
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            help
            exit 1
            ;;
    esac
done


## 필수 옵션체크하기 !!! 
[[ -z "$input" ]] && {
    echo "[ERROR] input is required option in Normality pipeline"
    echo
    help
    exit 1
}


[[ -z "$metadata" ]] && {
    echo "[ERROR] metadata is required option in Normality pipeline"
     echo
    help
    exit 1
}


## setting Dir / params
source $config

p_result=./Normality
if [ -d "$p_result" ]; then
    echo "[ERROR] Directory already exists: $p_result" >&2
    help
    exit 1
fi
mkdir -p ${p_result}

num_header=2
cut -f1,${num_header} ${metadata}  > ${p_result}/metadata.txt

function run_Normality(){
    type=$1
    input=$2
    metadata=$3
    num_header=$4
    o_paht=$5
    output=$6

    #for history 
    #Step1. Normality
    #echo "mkdir -p ${o_paht}/$output/"
    #echo "cut -f1,${num_header} ${metadata} > ${o_paht}/${output}/metadata.txt"
    #echo "cp ${input} ${o_paht}/${output}/"
    #echo "cd ${o_paht}/${output}"
#
#
    #echo "${sPath}/${Norm}  ${input} ./metadata.txt "


    #for running
    #Step1. Normality
    mkdir -p ${o_paht}/$output/
    cut -f1,${num_header} ${metadata} > ${o_paht}/${output}/metadata.txt
    cp ${input} ${o_paht}/${output}/
    cd ${o_paht}/${output}
    ${sPath}/${Norm}  ${input}  ./metadata.txt 
    echo "" 
    cd - > /dev/null
}


#  실행할 input list 정리하기 
lists=()

if [ -n "$input" ]; then
    IFS=',' read -ra vals <<< "$input"

    total=${#vals[@]}
    idx=1

    for v in "${vals[@]}"; do

        if [ "$total" -eq 1 ]; then
            sheet_name="Variable"
        else
            sheet_name="Variable${idx}"
        fi
        lists+=("ic,${v},${sheet_name}")
        ((idx++))
    done
fi

# 실제 분석 실행
for item in "${lists[@]}"; do
    IFS=',' read -ra vals <<< "$item"
   # echo "run_Normality  ${vals[0]} ${vals[1]}  ${metadata} ${num_header} ${method} ${p_result}  ${vals[2]}"
    run_Normality  ${vals[0]} ${vals[1]} ${metadata} ${num_header}  ${p_result}  ${vals[2]}

done

