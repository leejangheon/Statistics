#!/bin/sh

# 2026.04.29 요약 :  ASV -> 정규성 검사 X 

## 사용방법 
function help(){
    echo -e "sh $0  ASV|ReadBased|Custom"
    echo -e " Kruskal | Wilcoxon | Wilcoxon_pair | anova | t_test | paired_t_test "
    echo -e "tax_level  = phylum,genus,species"
    echo -e "func_level = metacyc,kegg,eggnog,gene"
    echo -e "\n\nTEST"
}



orderNumber=""
metadata=""
#analysis=""


header="Group"
method="Kruskal" #  Kruskal | Wilcoxon | Wilcoxon_pair | anova | t_test | paired_t_test 
adiv="True"
tax_level="phylum,genus,species"
pair=""
pair_boolen="False"
clr="False"
dunnP="0.05"
func_level="metacyc,kegg,eggnog,gene"


output_name="Statistics"
config=/garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config

while [ $# -gt 0 ]; do
    case "$1" in
        #-a|--analysis)
        #    analysis=$2
        #    shift 2
        #    ;;
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
            func_level=$2
            shift 2
            ;;

        -ic)
            echo "invalid option ic: $1"
            exit 1 ### ASV 에는 Custom 없음
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

## setting Dir / params
source $config

P_oPath=${read_based}/${orderNumber}/

p_result=$P_oPath/${output_name}


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

    cd -
}


#  실행할 input list 정리하기 
## adiv 
#/garnet2/Analysis/BI/ShotgunMetaGenome/HN00270465/result/MetaPhlAn4/HN00270465_MetaPhlAn4_adiv.tsv
lists=()
merged_sheet=()

if [ -n "$adiv" ]; then
    lists+=("adiv,${read_based}/${orderNumber}/result/MetaPhlAn4/${orderNumber}_MetaPhlAn4_adiv.tsv,AlphaDiversity")
    merged_sheet+=("${p_result}/AlphaDiversity")
fi


## taxonomy
#result/MetaPhlAn4/taxonomy
#MetaPhlAn4.Class.tsv   
#MetaPhlAn4.Family.tsv  
#MetaPhlAn4.Genus.tsv   
#MetaPhlAn4.Kingdom.tsv 
#MetaPhlAn4.Order.tsv   
#MetaPhlAn4.Phylum.tsv  
#MetaPhlAn4.Species.tsv 
if [ -n "$tax_level" ]; then
    IFS=',' read -ra vals <<< "$tax_level"
    for v in "${vals[@]}"; do

        case "$v" in
            phylum)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Phylum.txt,Phylum")
                merged_sheet+=("${p_result}/Phylum")
                ;;


            class)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Class.txt,Class")
                merged_sheet+=("${p_result}/Class")
                ;;

            order)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Order.txt,Order")
                merged_sheet+=("${p_result}/Order")
                ;;

            family)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Family.txt,Family")
                merged_sheet+=("${p_result}/Family")
                ;;

            genus)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Genus.txt,Genus")
                merged_sheet+=("${p_result}/Genus")
                ;;

            species)
                lists+=("it,${read_based}/${orderNumber}/result/MetaPhlAn4/taxonomy/MetaPhlAn4.Species.txt,Species")
                merged_sheet+=("${p_result}/Species")
                ;;

        esac
    done
fi

#func_level="metacyc,kegg,eggnog,gene"
#/garnet2/Analysis/BI/ShotgunMetaGenome/HN00270465/result/HUMAnN4/regroup/HN00270465_uniref90_eggnog_eggnog.tsv
#/garnet2/Analysis/BI/ShotgunMetaGenome/HN00270465/result/HUMAnN4/regroup/HN00270465_uniref90_ko_kegg-orthology.tsv
if [ -n "$func_level" ]; then
    IFS=',' read -ra vals <<< "$func_level"
    for v in "${vals[@]}"; do

        case "$v" in
            metacyc)
                lists+=("it,${read_based}/${orderNumber}/result/HUMAnN4//${orderNumber}_pathabundance.tsv,MetaCyc")
                merged_sheet+=("${p_result}/MetaCyc")
                ;;


            kegg)
                lists+=("it,${read_based}/${orderNumber}/result/HUMAnN4/regroup//${orderNumber}_uniref90_ko_kegg-orthology.tsv,KEGG")
                merged_sheet+=("${p_result}/KEGG")
                ;;

            eggnog)
                lists+=("it,${read_based}/${orderNumber}/result/HUMAnN4/regroup//${orderNumber}_uniref90_eggnog_eggnog.tsv,EggNOG")
                merged_sheet+=("${p_result}/EggNOG")
                ;;

            gene)
                lists+=("it,${read_based}/${orderNumber}/result/HUMAnN4//${orderNumber}_genefamilies.tsv,Gene")
                merged_sheet+=("${p_result}/Gene")
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