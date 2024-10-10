import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from db.busan_db import busan_db
from pgvector.pgvector_busan import create_pgvector

import pandas as pd
import json

import argparse


def init_db():
    pg_db = create_pgvector()
    mysql_db = busan_db()
    
    return pg_db, mysql_db


def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error loading JSON file: {e}")

def extract_update_list(pg_db, mysql_db, lang_table):
    
    visit_busan_place_list = [x[0] for x in mysql_db.select_place_id_from_table(lang_table["ko"]["review_table"])]
    current_review_list = [x[0] for x in pg_db.select_place_id_from_table("user_review")]
    update_id_list = list(set(visit_busan_place_list) - set(current_review_list))
    
    if len(update_id_list) < 1:
        print("No data to update")
            
    return update_id_list
        


def insert_main(data, pg_db):
    work_count = 0
    for idx, row in data.iterrows():
        review_id = row["UCMR_SEQ"]
        place_id = row["UC_SEQ"]
        rating = row["STAR_GRADE"]
        review = row["MY_STORY"]
        
        # print(review_id, place_id, rating, review)
        # print(type(review_id), type(place_id), type(rating), type(review))
        
        ret = pg_db.insert_values(table_name = "user_review", insert_columns = ["review_id", "place_id", "rating", "review"], values = [review_id, place_id, rating, review])
        
        if ret:
            work_count += 1
            print(f"work_count: {work_count}")
    
    print(f"work count: {work_count}")
    print(f'total count: {len(data)}')
    
    return True

    
def main(args):
    language_table = load_json("data/language_table_info.json")
    
    pg_db, mysql_db = init_db()
    
    ## 데이터 로드
    insert_data = mysql_db.select_as_dataframe(language_table["ko"]["review_table"])
    insert_data = insert_data[insert_data["UCL_SEQ"] == 7]
    print(insert_data.head())
    
    if args.mode == "update":
        update_list = extract_update_list(pg_db, mysql_db, language_table)
        insert_data = insert_data[insert_data["UC_SEQ"].isin(update_list)]
    
    if insert_data.empty:
        print("No data to insert")
        return True
    
    ## 데이터 삽입
    insert_main(insert_data, pg_db)
    print("Done!")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default="all")
    args = parser.parse_args()
    print(args)
    main(args)
        
    
    
    
    ## 각 데이터 로드
    