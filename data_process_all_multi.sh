# 현재 스크립트의 실행 디렉토리 확인
current_dir=$(basename "$PWD")

# 실행 디렉토리가 "algorithm"이 아닌 경우 종료
if [[ "$current_dir" != "algorithm" ]]; then
    echo "This script must be run from the 'algorithm' directory."
    exit 1
fi

## 로그 파일 디렉토리 생성
mkdir -p log/all

## 실행할 Python 스크립트 목록
scripts=("insert_multi_vector.py --mode all" "insert_multi_distance.py --mode all")

## 스크립트 순차 실행
for script in "${scripts[@]}"
do
    # 스크립트 이름 추출
    script_name=$(echo $script | awk '{print $1}')
    
    # 로그 파일 설정
    log_file="./log/all/${script_name%.py}.txt"
    
    # 처음 실행하는 경우 기존 로그 파일 삭제
    if [[ ! -f $log_file ]]; then
        echo "Initializing log file for $script_name"
        > "$log_file"
    fi
    
    echo "Running $script... Logging to $log_file"
    
    start_time=$(date +%s)
    
    # 스크립트 실행 및 시간 측정
    { time python $script; } &>> "$log_file"
    
    end_time=$(date +%s)
    elapsed_time=$(($end_time - $start_time))
    
    echo "Elapsed time: $elapsed_time seconds" >> "$log_file"
    
    echo "$script finished. Sleeping for 1 second..."
    sleep 1
done
