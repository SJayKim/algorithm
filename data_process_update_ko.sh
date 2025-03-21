#!/bin/bash
# 현재 스크립트의 실행 디렉토리 확인
current_dir=$(basename "$PWD")

# 실행 디렉토리가 "algorithm"이 아닌 경우 종료
if [[ "$current_dir" != "algorithm" ]]; then
    echo "This script must be run from the 'algorithm' directory."
    exit 1
fi


# 로그 디렉토리 생성
mkdir -p log/update

# 실행할 Python 스크립트 목록
scripts=("insert_busan_info.py --mode update" "insert_tour_meta.py --mode update" "insert_tour_meta.py --mode error_samples" "insert_review.py --mode update" "insert_tour_vector.py --mode update" "insert_tour_distance.py --mode update"  "delete_duplicate_from_db.py")

# 스크립트 순차 실행
for script in "${scripts[@]}"
do
    # 스크립트 이름 추출
    script_name=$(echo $script | awk '{print $1}')
    log_file="./log/update/${script_name%.py}.txt"
    
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

echo "All scripts have been executed."
