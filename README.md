# VISIT BUSAN

부산 관광 정보 처리 및 추천 시스템

## 목차

- [설치](#설치)
- [환경 설정](#환경-설정)
- [데이터 처리](#데이터-처리)
- [큐레이션 프로세스](#큐레이션-프로세스)
- [기능](#기능)

## 설치

필요한 패키지 설치:

```
pip install -r requirements.txt
```

## 환경 설정

### API 키 설정

1. `.env` 파일 생성:
   ```bash
   touch .env
   ```

2. `.env` 파일에 API 키 입력:
   ```
   openapi_key=YOUR_OPENAPI_KEY
   ```

### Konlpy 및 MeCab 설정

1. Konlpy 설치:
   ```bash
   pip install konlpy
   ```

2. Java 환경 변수 관련 에러 해결 (Linux 기준):
   ```bash
   sudo apt install default-jdk
   ```

3. MeCab 설치:
   ```bash
   sudo apt-get install curl
   bash <(curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh)
   ```

4. MeCab 관련 에러 해결:
   - Mecab-ko 설치
   - mecab-dic 설치
   - mecab-python 설치
   
   자세한 설치 방법은 원본 README 참조

## 데이터 처리

### 1. 데이터베이스 테이블 생성
- 파일: `creating_table_dict.json`
- 프로세스: `create_data_tables.py`
- 생성 테이블: `meta_info`, `major_category`, `visit_busan_info` 등

### 2. 카테고리 데이터 정의 및 적재
- 파일: `major_category.json`, `theme_category.json`
- 프로세스: `insert_category_info.py`
- 사용법: `python insert_category_info.py --data_type [major|theme]`

### 3. 부산관광공사 데이터 분류 및 적재
- 테이블: `visit_busan_info`
- 프로세스: `insert_busan_info.py`
- 사용법: `python insert_busan_info.py --mode [all|update]`

### 4. 관광지 메타 데이터 추출 및 적재
- 테이블: `meta_info`, `tour_place_meta`
- 프로세스: `insert_tour_meta.py`
- 사용법: `python insert_tour_meta.py --mode [all|error_samples|update]`

### 5. 관광지 데이터 벡터화
- 테이블: `tour_vector`
- 프로세스: `insert_tour_vector.py`
- 사용법: `python insert_tour_vector.py --mode [all|update]`

### 6. 관광지-식당 거리 데이터 적재
- 테이블: `tour_restaurant_distance`
- 프로세스: `insert_tour_distance.py`
- 사용법: `python insert_tour_distance.py --mode [all|update]`

### 7. 관광지 리뷰 데이터 적재
- 테이블: `user_review`
- 프로세스: `insert_review.py`
- 사용법: `python insert_review.py --mode [all|update]`

### 전체 데이터 처리 파이프라인
실행 방법:
```bash
./data_process_all.sh    # 전체 데이터 처리
./data_process_update.sh # 업데이트 데이터 처리
```

## 큐레이션 프로세스

### 1. 사용자 입력 기반 큐레이션
- 프로세스: `curation_user_input.py`
- 사용법:
  ```bash
  python curation_user_input.py --theme "테마파크, 문화역사" --place_num 5 --preferences "강아지와 함께 할 수 있는 여행" --keywords "반려견, 데이트코스, 힐링"
  ```

### 2. 자연어 질의 기반 큐레이션
- 프로세스: `curation_natural_language.py`
- 사용법:
  ```bash
  python curation_natural_language.py --input_query "메뉴얼 바이크를 타고 해변도로를 달리는데 차가 별로 없고 운전하기 어렵지 않은 곳으로 코스를 짜줘"
  ```

## 기능

- 관광지 관련 메타 키워드 추출
- 관광지 관련 벡터 데이터베이스 구축
- 선호도 반영 AI 기반 관광지 추천 및 스케줄링
- 사용자 입력 자연어 질의 기반 AI 관광지 추천 및 스케줄링

자세한 내용은 각 섹션을 참조하세요.




