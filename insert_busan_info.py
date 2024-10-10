import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

## DB 연결
from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db

import json
import pandas as pd
import argparse


with open("./data/major_category.json", "r") as f:
    major_cat_dict = json.load(f)

with open("./data/creating_table_dict.json", "r") as f:
    table_dict = json.load(f)

with open("./data/language_table_info.json", "r") as f:
    inserting_table_list = json.load(f)

pg_db = create_pgvector()
db = busan_db()


table_name = "visit_busan_info"
table_columns = [x[0] for x in table_dict[table_name] if "foreign" not in x[0]]




'''

부산 관광공사 데이터를 모두 엑셀 파일로 가져와 오투오 Postgres DB에 삽입하는 코드

- data_path: 부산 관광공사 데이터가 있는 폴더 경로 --> ex) "./data/visit_busan_data"
- file_format: 부산 관광공사 데이터 파일 형식 --> 
    ex) ["vw_ubi_attraction_ko.xlsx", "vw_ubi_food_ko.xlsx", "vw_ubi_accommodation_ko.xlsx", "vw_ubi_shopping_ko.xlsx", "vw_ubi_festival_ko.xlsx"]



'''
def extract_update_data(busan_data_frame, major_cat_id):
    current_pg_db_place_ids = [x[0] for x in pg_db.select_place_id_list(major_cat = major_cat_id)]
    output_data = busan_data_frame[~busan_data_frame['UC_SEQ'].isin(current_pg_db_place_ids)]
    return output_data

def remove_deleted_data(table_name):
    ## 삭제된 데이터 제거
    busan_place_ids = []
    for table in inserting_table_list["ko"]["busan_table"]:
        place_ids = [x[0] for x in db.select_place_id_from_table(table)]
        busan_place_ids += place_ids
    current_pg_db_place_ids = [x[0] for x in pg_db.select_place_id_list()]
    
    deleted_place_ids = list(set(current_pg_db_place_ids) - set(busan_place_ids))
    
    if len(deleted_place_ids) < 1:
        print("No data to delete=====================")
        return False
    
    ret = pg_db.delete_place_ids_from_table(table_name=table_name, place_id_list=deleted_place_ids)
    print(f"deleted {table_name} data, deleted count: {len(deleted_place_ids)}")
    
    return True


def main(mode):
    ## 데이터 path 입력 받아 데이터 삽입
    try:    
        table_list = inserting_table_list["ko"]["busan_table"]
    except:
        print("error occured in table_list loading, check the table_list.json file")
        exit()
    
    
    
    table_name = "visit_busan_info"
    
    if mode == "update":
        ## 삭제된 데이터 제거
        remove_deleted_data(table_name)
    
    
    for data_path in table_list:

        ## Dataframe 형식으로 데이터 로드
        major_cat = major_cat_dict[data_path]["pg_key"]
        major_cat_id = major_cat_dict[data_path]["id"]
     
        data = db.select_as_dataframe(data_path)
        print(f'data: {data_path}')
        
        
        ## 업데이트시 기존 데이터와 겹치는 데이터 제거
        if mode == "update":
            print("update mode=====================")
            data = extract_update_data(data, major_cat_id)
            if len(data) < 1:
                print("No data to update=====================")
                continue
        
        print(f'inserting table name: {table_name}, data length: {len(data)}')
        
        work_count = 0
        for idx, row in data.iterrows():
            ## 공통 데이터
            data_id = row["UC_SEQ"]
            title = row["PLACE"]
            gugun_nm = row["GUGUN_NM"]
            cat1 = row["CATE1_NM"]
            cat2 = row["CATE2_NM"]
            lat = row["LAT"]
            lng = row["LNG"]
            hash_tag = row["HASH_TAG"]
            addr = row["ADDR1"]
            
            ## 테이블 별 데이터

            if major_cat == "restaurant":
                desc = row["RPRSNTV_MENU"]
            elif major_cat == "hotel":
                ## 각 숙박업소에 대한 naver url 가져오는 코드 필요
                desc = "naver_URL"
            else:
                desc = row["ITEMCNTNTS"]
            
            ret = pg_db.insert_values(table_name=table_name, insert_columns=table_columns, values=[data_id, title, gugun_nm, cat1, cat2, lat, lng, addr, hash_tag, desc, major_cat_id])
            if ret:
                work_count += 1
            else:
                print(f"error occured in {table_name} data insertion, trying to update")
                update_ret = pg_db.update_values(table_name=table_name, update_columns=table_columns, update_values=[data_id, title, gugun_nm, cat1, cat2, lat, lng, addr, hash_tag, desc, major_cat_id], condition_columns=["place_id"], condition_values=[data_id])
                if update_ret:
                    work_count += 1
                else:
                    print(f"error occured in {table_name} data insertion")

        print(f"inserted {table_name} data, completed count: {work_count} / {len(data)}")
    print("insertion completed")
        
    
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, default = "all", help="'all' or 'update' are available")
    
    args = parser.parse_args()
    print(args)
    
    main(args.mode)
    
   

    

    