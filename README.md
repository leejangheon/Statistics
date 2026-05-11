Metagenome Statistics Pipeline v2.0
이 프로젝트는 앰플리콘(Amplicon) 및 샷건(Shotgun) 메타지놈 데이터의 다그룹 비교 통계 분석을 자동화하는 파이프라인입니다
. 사용자는 제공된 스크립트를 통해 미생물 군집(Taxonomy), 다양성 지수(Diversity Index), 기능 유전자(Functional Abundance)에 대한 그룹 간 유의미한 차이를 손쉽게 발굴할 수 있습니다
.
💡 주요 업데이트 (v2.0)
Python 기반 전환: 기존 R 기반 메인 통계 코드를 Python 기반으로 전환하여 처리 속도와 안정성을 높였습니다
.
데이터 필터링 표준화: Bayesian taxonomy assignment의 NA taxon, Read-based의 unmapped 등 명명에 대한 필터링 기준을 통일하여 작업자별 결과 차이를 최소화했습니다
.
파이프라인 모듈화: 통계 분석 코드를 단일 스크립트에서 기능별 독립 스크립트(ANOVA, Kruskal-Wallis, Wilcoxon, t-test 등)로 분리하여 확장성과 유지보수성을 극대화했습니다
.

--------------------------------------------------------------------------------
📋 분석 전 준비 사항 (Input Data)
통계 분석을 실행하기 위해 다음의 데이터가 필요합니다
.
기본 분석 결과 데이터: Taxonomic Relative Abundance, Diversity Index (사용자 정의 분석 시 Custom abundance 테이블)
.
메타데이터 (metadata.txt): 샘플 별 그룹 정보가 포함된 파일
.
Unpaired 분석: #SampleID 및 Group 컬럼 필요
.
Paired 분석: #SampleID, Group, 그리고 쌍(Pair)을 이루는 개체 식별 정보 컬럼(예: PID) 필수 포함
.

--------------------------------------------------------------------------------
🔬 지원 통계 분석 기법
데이터의 정규성 및 그룹 수에 따라 아래의 통계 기법을 지원하며, 앰플리콘 메타지놈 데이터 특성상 기본적으로 비모수 검정이 주로 사용됩니다
.
비모수 검정 (Non-parametric)
:
2 그룹 (Unpaired): Wilcoxon (Wilcoxon Rank Sum Test)
2 그룹 (Paired): Wilcoxon_pair (Wilcoxon Signed Rank Test)
3 그룹 이상: Kruskal (Kruskal Wallis Test & Dunn's post hoc) - Default 옵션
모수 검정 (Parametric)
:
2 그룹 (Unpaired): t_test
2 그룹 (Paired): paired_t_test
3 그룹 이상: anova (1-way ANOVA & Tukey HSD)

--------------------------------------------------------------------------------
🚀 실행 방법 및 주요 옵션
모든 분석은 run.sh 스크립트를 통해 실행되며, 분석 목적에 맞는 **모드(ASV, ReadBased, Custom, Norm)**를 지정해야 합니다
.
기본 실행 구조:
sh /garnet2/Tools/Amplicon_MetaGenome/Adv_Analysis/Statistics_v2.0.0/run.sh [Mode] [옵션]
1. ASV Mode
앰플리콘 데이터 기반 통계 분석 시 사용합니다
.
필수 옵션: -o / --order (오더 번호), -m / --metadata (메타데이터), -a / --analysis (분석 폴더명)
.
선택 옵션:
--method: 통계 기법 (기본값: Kruskal)
.
--header: 그룹 비교 기준 컬럼명 (기본값: Group)
.
--pair: Paired 분석 시 짝 정보 컬럼명
.
--adiv: Alpha Diversity 분석 여부 (True/False)
.
-it: Taxonomy 레벨 (기본값: phylum,genus,species)
.
2. Read-based Mode
샷건 메타지놈 데이터의 분류 및 기능 유전자 통계 분석 시 사용합니다
.
필수 옵션: -o / --order, -m / --metadata
.
선택 옵션: ASV 옵션과 동일하며, 추가로 기능 유전자 레벨 설정을 위한 -if (기본값: metacyc,gene) 옵션을 지원합니다
.
3. Custom & Norm Mode
Custom Mode: 자동화 파이프라인 결과가 아닌 사용자가 직접 준비한 파일 분석 시 사용. -ic 옵션으로 입력 데이터 경로를 지정합니다
.
Norm Mode: 데이터의 정규성 검사만 단독으로 수행할 때 사용합니다. Normality 폴더에 결과가 생성됩니다
.

--------------------------------------------------------------------------------
💻 사용 예시 (Use Cases)
기본적인 실행 명령어는 아래와 같으며, method 옵션을 명시적으로 지정하여 사용하는 것을 권장합니다
.
[ASV 분석]
# 기본 실행 (Group 컬럼 기준, Kruskal-Wallis, 기본 레벨 분석)
sh .../run.sh ASV --order HN00sample --metadata metadata.statistics.txt --analysis analysis_15ea --method Kruskal

# Paired 분석 실행 (Pair 컬럼 추가 필수)
sh .../run.sh ASV --order HN00sample --header Group --pair Pair --metadata metadata_pair.txt --analysis analysis_135ea_BLAST --method Wilcoxon_pair

# 특정 분류(Family) 추가 및 Alpha Diversity 제외
sh .../run.sh ASV --order HN00sample --metadata metadata.statistics.txt --analysis analysis_15ea -it phylum,family,genus,species --adiv False
(참고: ASV 진행 시 Taxonomy assignment 결과가 두 개 이상이면 스크립트 실행 중 선택 창이 출력됩니다)
[Read-based 분석]
# 기본 실행
sh .../run.sh ReadBased --order HN0KITTEST --metadata metadata.txt

# Functional 분석 항목 추가 (kegg, eggnog)
sh .../run.sh ReadBased --order HN0KITTEST --metadata metadata.txt -if metacyc,gene,kegg,eggnog
[Custom & Norm 분석]
# Custom 다중 파일 분석
sh .../run.sh Custom -ic abundance.txt,abundance2.txt --order HN00274906 --metadata metadata.txt

# Normality(정규성) 검사
sh .../pipeline/Norm.sh -ic abundance.txt -m metadata.txt

--------------------------------------------------------------------------------
📂 결과 파일 구조
정상적으로 스크립트가 실행되면 설정한 output 폴더(기본값: [analysis]_Statistics) 하위에 다음과 같은 구조로 결과 파일이 생성됩니다
.
[analysis]_Statistics/
├── config                     # 실행된 분석 설정 파라미터 로그
├── metadata.txt               # 분석에 사용된 메타데이터 파일
├── AlphaDiversity/            # 다양성 지수 통계 결과 폴더
├── Phylum/                    # Phylum 레벨 통계 결과 폴더
├── Genus/                     # Genus 레벨 통계 결과 폴더
├── Species/                   # Species 레벨 통계 결과 폴더
│   ├── processed.txt
│   ├── kruskal_dunn_summary.tsv / ttest_summary.tsv 등
│   └── Log2FC.tsv
└── output.xlsx                # 모든 통계 결과가 통합된 엑셀 리포트

-----------------------------------------------------------------------------
