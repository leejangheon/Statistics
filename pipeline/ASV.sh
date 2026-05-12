#!/bin/sh

# 2026.04.29 요약 :  ASV -> 정규성 검사 X 

## 사용방법 
function help() {

    echo ""
    echo "======================================================================"
    echo "                    Statistical Analysis Pipeline"
    echo "======================================================================"
    echo ""

    echo "Usage:"
    echo "  sh $0 [OPTIONS]"
    echo ""

    echo "Required Options:"
    echo "  -o,  --order        Order number"
    echo "  -a,  --analysis     Analysis directory/path"
    echo "  -m,  --metadata     Metadata file"
    echo ""

    echo "Optional Options:"
    echo "  --method            Statistical method"
    echo "                      Default : Kruskal"
    echo ""
    echo "                      Available:"
    echo "                        Kruskal"
    echo "                        Wilcoxon"
    echo "                        Wilcoxon_pair"
    echo "                        t_test"
    echo "                        paired_t"
    echo "                        anova"
    echo ""

    echo "  --header            Metadata group column name"
    echo "                      Default : Group"
    echo ""

    echo "  --pair              Pair column name for paired test"
    echo "                      Example : Pair"
    echo ""

    echo "  --adiv              Run alpha diversity analysis"
    echo "                      Default : True"
    echo ""



    echo "  --dunnP             Dunn posthoc significance cutoff"
    echo "                      Default : 0.05"
    echo ""

    echo "  -it                 Taxonomy levels"
    echo "                      Default : phylum,genus,species"
    echo ""
    echo "                      Available:"
    echo "                        phylum"
    echo "                        class"
    echo "                        order"
    echo "                        family"
    echo "                        genus"
    echo "                        species"
    echo ""

    echo "  --output            Output directory name"
    echo "                      Default : Statistics"
    echo ""

    echo "  -c, --config        Config directory"
    echo "                      Default :"
    echo "                      /garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config"
    echo ""

    echo "Unavailable Options in ASV mode:"
    echo "  -if                 Function option is not supported"
    echo "  -ic                 Custom category option is not supported"
    echo ""


    echo "======================================================================"
    echo ""

 
}


orderNumber=""
analysis=""
metadata=""


header="Group"
method="Kruskal" #  Kruskal | Wilcoxon | Wilcoxon_pair | anova | t_test | paired_t_test 
adiv="True"
tax_level="phylum,genus,species"
pair=""
pair_boolen="False"
#clr="False"
dunnP="0.05"

output_name="Statistics"
config=/garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config

while [ $# -gt 0 ]; do
    case "$1" in
        -a|--analysis)
            analysis=$2
            shift 2
            ;;
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
        --pair)
            pair=$2
            pair_boolen="True"
            shift  2
            ;;
        --adiv)
            adiv=$2
            shift 2
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
            tax_level=$2
            shift 2
            ;;
        -if)
            echo "#### invalid option if: $1"
            help
            exit 1 ### ASV 에는 function 없음
            ;;

        -ic)
            echo "##### invalid option ic: $1"
            help
            exit 1 ### ASV 에는 Custom 없음
            ;;
        *)
            echo "Unknown option: $1"
            help
            exit 1
            ;;
    esac
done


## 필수 옵션체크하기 !!! 
[[ -z "$orderNumber" ]] && {
    echo "[ERROR] orderNumber is required option in ASV pipeline"
    echo 
    help
    exit 1
}

[[ -z "$analysis" ]] && {
    echo "[ERROR] analysis is required option in ASV pipeline"
    echo 
    help
    exit 1
}

[[ -z "$metadata" ]] && {
    echo "[ERROR] metadata is required option in ASV pipeline"
    echo 
    help
    exit 1
}

if [[ ! " Kruskal Wilcoxon Wilcoxon_pair t_test paired_t anova " =~ " ${method} " ]]; then

    echo "[ERROR] Invalid method: $method"
    help
    exit 1

fi

## setting Dir / params
source $config

P_oPath=$asv/$orderNumber/
p_result=$P_oPath/${analysis}_${output_name}


if [ -d "$p_result" ]; then
    echo "[ERROR] Directory already exists: $p_result" >&2
    exit 1
fi

mkdir -p ${p_result}

{
echo ""
echo "=================================================="
echo "         ASV Statistics Pipeline Config"
echo "=================================================="

printf "%-20s : %s\n" "orderNumber" "$orderNumber"
printf "%-20s : %s\n" "analysis" "$analysis"
printf "%-20s : %s\n" "metadata" "$metadata"

echo "--------------------------------------------------"

printf "%-20s : %s\n" "header" "$header"
printf "%-20s : %s\n" "method" "$method"
printf "%-20s : %s\n" "adiv" "$adiv"
printf "%-20s : %s\n" "tax_level" "$tax_level"
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
} | tee ${p_result}/config
sleep 5

# 프롬프트 : taxnonmy tool이 여러개인경우 선택하도록 
base="${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment"
dirs=( "$base"/*/ )
count=${#dirs[@]}
if (( count == 0 )); then
    echo "[ERROR] No directories found" >&2
    exit 1
elif (( count == 1 )); then
    selected="${dirs[0]}"
    echo "[INFO] Only one directory found: $selected"
else
    echo "[INFO] Multiple directories found:"
    
    for i in "${!dirs[@]}"; do
        echo "[$((i+1))] ${dirs[i]}"
    done
    while true; do
        read -p "Select directory (1-$count): " idx
    
        if [[ "$idx" =~ ^[0-9]+$ ]] && (( idx >= 1 && idx <= count )); then
            selected="${dirs[idx-1]}"
            break
        else
            echo "[ERROR] Invalid selection"
        fi
    done
fi
db_selected=`basename $selected`
echo "[SELECTED] $db_selected"



# Method -> metadata 그룹 수 체크 
if [[ "$pair_boolen" == "True" ]]; then
    num_header=$(head -n1 "$metadata" | tr '\t' '\n' | grep -nE "$header|${pair}" | cut -d: -f1 | paste -sd "," -)
else
    num_header=`head -n1 $metadata | tr "\t" "\n" | grep -n "$header" | cut -d":" -f1`
fi
echo "$num_header"

cut -f1,${num_header} ${metadata}  > ${p_result}/metadata.txt


# 고민중...
#if [[ "$method" == "" ]]; then
    #gcount=`sed '1d' $metadata  | cut -f ${num_header} | sort | uniq | wc -l`
    #if [ "$gcount" -eq 2 ]; then
         #echo "gcount is 2"
    #elif [ "$gcount" -ge 3 ]; then
         #echo "gcount is >= 3"
    #else
         #echo "gcount is less than 2"
    #fi
#fi


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
    echo "${sPath}/${Preprocessing} -t asv -m ./metadata.txt  -${type} ${input}  --output ./"

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
    echo " ${sPath}/${MakePlot}   ${method} "

    #for running

    #Step1. Preprocessing
    mkdir -p ${o_paht}/$output/
    cut -f1,${num_header} ${metadata} > ${o_paht}/${output}/metadata.txt
    cp ${input} ${o_paht}/${output}/
    cd ${o_paht}/${output}
    ${sPath}/${Preprocessing} -t asv -m ./metadata.txt  -${type} ${input}  --output ./
  
    #Step2. Arithmetic_Statistics
    ${sPath}/${Arithmetic_Statistics}  processed.txt  ./metadata.txt 

    if [[ "$pair_boolen" == "True" ]]; then
        ${sPath}/${Pair_Arithmetic}  processed.txt  ./metadata.txt 
    fi
    #Step3.  Statistics
    ${sPath}/${script_arr[0]}  processed.txt  ./metadata.txt 
    ${sPath}/${script_arr[1]} --dunn  ${dunnP} --desc mapping.txt --sheet ${output} --header $header --type ${type}

    ${sPath}/${MakePlot}   ${method} 
    cd -
}

#  실행할 input list 정리하기 
## adiv 
# ${asv}/${orderNumber}/${analysis}/Diversity/alpha_diversity_6.txt
lists=()
merged_sheet=()

if [[ "${adiv,,}" == "true" ]]; then
    lists+=("adiv,${asv}/${orderNumber}/${analysis}/Diversity/alpha_diversity_6.txt,AlphaDiversity")
    merged_sheet+=("${p_result}/AlphaDiversity")
fi


## taxonomy
#${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/Bayesian_NCBI_16S/ASVs_Bayesian_NCBI_16S.biom.summary   ASVs_Bayesian_NCBI_16S_L2.txt
if [[ "${tax_level,,}" != "false" ]]; then
    IFS=',' read -ra vals <<< "$tax_level"
    for v in "${vals[@]}"; do

        case "$v" in
            phylum)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L2.txt,Phylum")
                merged_sheet+=("${p_result}/Phylum")
                ;;


            class)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L3.txt,Class")
                merged_sheet+=("${p_result}/Class")
                ;;

            order)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L4.txt,Order")
                merged_sheet+=("${p_result}/Order")
                ;;

            family)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L5.txt,Family")
                merged_sheet+=("${p_result}/Family")
                ;;

            genus)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L6.txt,Genus")
                merged_sheet+=("${p_result}/Genus")
                ;;

            species)
                lists+=("it,${asv}/${orderNumber}/${analysis}/Taxonomy_Assignment/${db_selected}/ASVs_${db_selected}.biom.summary/ASVs_${db_selected}_L7.txt,Species")
                merged_sheet+=("${p_result}/Species")
                ;;
            *)
                echo "Unknown option: $1"
                help
                exit 1
                ;;
        esac
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
echo ${sPath}/${MakeExcel} ${orderNumber}  metadata.txt   ${method} "${merged_sheet[@]}"
${sPath}/${MakeExcel} ${orderNumber}  metadata.txt   ${method} "${merged_sheet[@]}"
