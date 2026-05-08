#!/bin/sh

# 2026.04.29 요약 :  ASV -> 정규성 검사 X 

## 사용방법 
function help(){
    echo -e "sh $0  ASV|ReadBased|Custom"
    echo -e " Kruskal | Wilcoxon | Wilcoxon_pair | anova | t_test | paired_t_test "

    echo -e "\n\nTEST"
}



input=""
metadata=""
orderNumber=""

header="Group"
method="Kruskal" #  Kruskal | Wilcoxon | Wilcoxon_pair | anova | t_test | paired_t_test 
pair=""
pair_boolen="False"
dunnP="0.05"
output_name="Statistics"
config=/garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config
desc=""
while [ $# -gt 0 ]; do
    case "$1" in
       
        -m|--metadata)
            metadata=$2
            shift 2
            ;;
        --method)
            method=$2
            shift 2
            ;;
        -o|--order)
            orderNumber=$2
            shift 2
            ;;
        --output)
            output_name=$2
            shift 2
            ;;
        -c|--config)
            config=$2
            shift 2
            ;;
        --header)
            header=$2
            shift 2
            ;;
        -d|--desc)
            desc=$2
            shift 2
            ;;
        --pair)
            pair=$2
            pair_boolen="True"
            shift  2
            ;;
       
        --clr)
            clr=$2
            shift 2
            ;;
        --dunnP)
            dunnP=$2
            shift 2
            ;;
        -it)
            echo "invalid option it: $1"
            exit 1 ### Custom 에는 function 없음
            ;;
        -if)
            echo "invalid option if: $1"
            exit 1 ### Custom 에는 function 없음
            ;;

        -ic)
            input=$2
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done


## 필수 옵션체크하기 !!! 
[[ -z "$orderNumber" ]] && {
    echo "[ERROR] orderNumber is required option in ASV pipeline"
    exit 1
}


[[ -z "$metadata" ]] && {
    echo "[ERROR] metadata is required option in ASV pipeline"
    exit 1
}

echo ""
echo "=================================================="
echo "         ASV Statistics Pipeline Config"
echo "=================================================="

printf "%-20s : %s\n" "orderNumber" "$orderNumber"
printf "%-20s : %s\n" "metadata" "$metadata"
printf "%-20s : %s\n" "input" "$input"

echo "--------------------------------------------------"

printf "%-20s : %s\n" "header" "$header"
printf "%-20s : %s\n" "method" "$method"
printf "%-20s : %s\n" "pair_boolen" "$pair_boolen"

if [[ "$pair_boolen" == "True" ]]; then
    printf "%-20s : %s\n" "pair_header" "$pair"
fi

if [[ "$method" == "Kruskal" ]]; then
    printf "%-20s : %s\n" "dunnP" "$dunnP"
fi

echo "--------------------------------------------------"

printf "%-20s : %s\n" "output_name" "$output_name"

echo "=================================================="
echo ""


## setting Dir / params
source $config

p_result=./${output_name}


if [ -d "$p_result" ]; then
    echo "[ERROR] Directory already exists: $p_result" >&2
    exit 1
fi

mkdir -p ${p_result}



# Method -> metadata 그룹 수 체크 
if [[ "$pair_boolen" == "True" ]]; then
    num_header=$(head -n1 "$metadata" | tr '\t' '\n' | grep -nE "$header|${pair}" | cut -d: -f1 | paste -sd "," -)
else
    num_header=`head -n1 $metadata | tr "\t" "\n" | grep -n "$header" | cut -d":" -f1`
fi
echo "$num_header"

cut -f1,${num_header} ${metadata}  > ${p_result}/metadata.txt




function run_statistics(){
    type=$1
    input=$2
    metadata=$3
    num_header=$4
    statistics=$5
    o_paht=$6
    output=$7

    # for history 
    #Step1. Preprocessing
    echo "mkdir -p ${o_paht}/$output/"
    echo "cut -f1,${num_header} ${metadata} > ${o_paht}/${output}/metadata.txt"
    echo "cp ${input} ${o_paht}/${output}/"
    echo "cd ${o_paht}/${output}"


    echo "${sPath}/${Preprocessing_Custom} ${input}   processed.txt ./metadata.txt "


    #Step2. Arithmetic_Statistics
    echo "${sPath}/${Arithmetic_Statistics}  processed.txt  ./metadata.txt "

    if [[ "$pair_boolen" == "True" ]]; then
        echo "${sPath}/${Pair_Arithmetic}  processed.txt  ./metadata.txt "
    fi
    
    #Step3.  Statistics
    scripts=$(eval echo \$$statistics)
    read -ra script_arr <<< "$scripts"
    echo "${sPath}/${script_arr[0]}  processed.txt  ./metadata.txt "
    echo "${sPath}/${script_arr[1]} --dunn  ${dunnP} --desc mapping.txt --sheet ${output} --header $header --type ${type}"


    #for running

    #Step1. Preprocessing
    mkdir -p ${o_paht}/$output/
    cut -f1,${num_header} ${metadata} > ${o_paht}/${output}/metadata.txt
    cp ${input} ${o_paht}/${output}/
    cd ${o_paht}/${output}
    
    ${sPath}/${Preprocessing_Custom} ${input}   processed.txt ./metadata.txt 
  
    #Step2. Arithmetic_Statistics
    ${sPath}/${Arithmetic_Statistics}  processed.txt  ./metadata.txt 

    if [[ "$pair_boolen" == "True" ]]; then
        ${sPath}/${Pair_Arithmetic}  processed.txt  ./metadata.txt 
    fi
    #Step3.  Statistics
    ${sPath}/${script_arr[0]}  processed.txt  ./metadata.txt 
    ${sPath}/${script_arr[1]} --dunn  ${dunnP} --desc mapping.txt --sheet ${output} --header $header --type ${type}

    cd -
}



#  실행할 input list 정리하기 
lists=()
merged_sheet=()

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
        merged_sheet+=("${sheet_name}")
        ((idx++))
    done
fi
# 실제 분석 실행
for item in "${lists[@]}"; do
    IFS=',' read -ra vals <<< "$item"
    echo "run_statistics  ${vals[0]} ${vals[1]}  ${metadata} ${num_header} ${method} ${p_result}  ${vals[2]}"
    run_statistics  ${vals[0]} ${vals[1]} ${metadata} ${num_header} ${method} ${p_result}  ${vals[2]}
done



 #Step4.  Export & Make Excel 
cd  ${p_result}
echo $pwd
echo ${sPath}/${MakeExcel} ${orderNumber}  metadata.txt   ${method} "${merged_sheet[@]}"
${sPath}/${MakeExcel} ${orderNumber}  metadata.txt   ${method} "${merged_sheet[@]}"