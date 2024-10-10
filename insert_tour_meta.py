import os, sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

## 키워드 추출 모듈
from meta_generator.llm_keyword import LLM_keyword

##벡터 임베딩 모듈
from embedding_model.sroberta import embedding_model

## DB 관련 모듈
from pgvector.pgvector_busan import create_pgvector

## api key 설정
from dotenv import load_dotenv
import dotenv

## 데이터 전처리 라이브러리
import json
import pandas as pd
from tqdm import tqdm
import re

import argparse


db = create_pgvector()
llm_keyword = LLM_keyword()

def remove_special_characters(text):
    # 정규 표현식을 사용하여 특수문자 제거
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)
    return clean_text

def extract_update_list():
    visit_busan_place_list = [x[0] for x in db.select_place_id_list()]
    current_theme_place_list = [x[0] for x in db.select_place_id_from_table("tour_place_meta")]
    update_id_list = list(set(visit_busan_place_list) - set(current_theme_place_list))
    
    if len(update_id_list) < 1:
        print("No data to update")
        exit() 
    
    return update_id_list


def main(busan_data):

    error_rows = []
    work_count = 0
    for idx, row in tqdm(busan_data.iterrows(), total=len(busan_data)):
        try:
            place_id = row["place_id"]
            title = row["place_title"]
            overview = row["description"]

            keywords = llm_keyword.get_keywords_json(overview, save_path=None)
            print(keywords)
            keywords_json = json.loads(keywords)
            
            all_keywords = set(keywords_json['keywords_extracted'] + keywords_json['keywords_generated'])
            
            ## 각 키워드 매칭 및 insert
            for keyword in all_keywords:
                ## 특수문자 제거
                keyword = remove_special_characters(keyword)

                meta_id = db.check_keywords_and_insert(keyword)
                insert_data = [int(place_id), meta_id]
                ret = db.insert_values(table_name = "tour_place_meta", insert_columns=["place_id", "meta_id"], values=insert_data)
                print(f'inserting result for {place_id} and {meta_id}: {ret}')

            work_count +=1
        except:
            print(f"Error in {idx}")
            print(f'current row: {row}')
            error_rows.append(row)
    
    print(f"Total {work_count}/{len(busan_data)} rows are processed")
    print(f"Error rows: {len(error_rows)}")
    ## 에러난 tour place 저장
    if error_rows:
        error_df = pd.DataFrame(error_rows)
        error_df.to_excel("./data/error_samples/error_rows.xlsx", index=False, engine='openpyxl')
        print(f"Saved error rows to error_rows.xlsx")

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, help="'all' or 'error_samples' are available")
    args = parser.parse_args()
    
    print(args)
    
    if args.mode == "all":
        busan_data = db.select_all_busan_data(major_cat_id=1, df_format=True)
        
    elif args.mode == "error_samples":
        try:
            busan_data = pd.read_excel("./data/error_samples/error_rows.xlsx")
            if len(busan_data) < 1:
                print("No data in error samples file")
                sys.exit(1)
        except:
            print("No error samples file found")
            sys.exit(1)
    elif args.mode == 'update':
        busan_data = db.select_all_busan_data(major_cat_id=1, df_format=True)
        ## update 리스트 들만 필터링
        update_list = extract_update_list()
        busan_data = busan_data[busan_data["place_id"].isin(update_list)]

    else:
        raise ValueError("Invalid mode it should be one of two ['all', 'error_samples']")
    
    main(busan_data)
    print("Done!")