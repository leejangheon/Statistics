#!/bin/sh

 
function help(){
    echo -e "[[잘못된 옵션]]"
    echo -e "sh $0  ASV|ReadBased|MAG|Custom|Norm"   
        
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
