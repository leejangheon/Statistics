#!/bin/sh

 
function help() {

    echo ""
    echo "=============================================================="
    echo "                    Statistical Analysis"
    echo "=============================================================="
    echo ""

    echo "Usage:"
    echo "  sh $0 <MODE> <METHOD>"
    echo ""

    echo "Available MODE:"
    echo "  ASV          : ASV abundance table"
    echo "  ReadBased    : Read-based taxonomy/profile"
    echo "  MAG          : MAG-based analysis"
    echo "  Custom       : User custom table"
    echo "  Norm         : Normalized table"
    echo ""

    echo "Available METHOD:"
    echo "  Kruskal          : Kruskal-Wallis test"
    echo "  Wilcoxon         : Wilcoxon rank-sum test"
    echo "  Wilcoxon_pair    : Paired Wilcoxon signed-rank test"
    echo "  t_test           : Welch t-test"
    echo "  paired_t         : Paired t-test"
    echo "  anova            : One-way ANOVA + Tukey HSD"
    echo ""

    echo "Example:"
    echo "  sh $0 ASV --method Kruskal"
    echo "  sh $0 ReadBased --method  anova"
    echo ""

    echo "=============================================================="
    echo ""

    exit 1
}


# default setting 
mode=$1
# mode만 체크 나머지 옵션은 각각에서 필수파라미터 정의 하기 
if [[ ! "$mode" =~ ^(ASV|ReadBased|MAG|Custom|Norm)$ ]]; then
    help
    exit 1
fi


config=/garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/config
shift




## config 호출 
prev=""
for arg in "$@"; do
    if [[ "$prev" == "--config" || "$prev" == "-c" ]]; then
        config="$arg"
    fi
    prev="$arg"
done


source $config


## 분석 파이프라인 실행
case "$mode" in
ASV)
    echo "$pipeline/ASV.sh  $@ "  
    $pipeline/ASV.sh  $@ 
    ;;

ReadBased)
    echo "$pipeline/Read_based.sh $@  "
    $pipeline/Read_based.sh $@
    ;;
MAG)
    echo "$pipeline/MAG.sh $@  "
    $pipeline/MAG.sh $@
    ;;
Norm)
    echo "$pipeline/Norm.sh  $@ "
    $pipeline/Norm.sh  $@ 
    ;; 

Custom)
    echo "$pipeline/Custom.sh  $@ "
    $pipeline/Custom.sh  $@
    ;; 

esac
