import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import argparse
from tqdm import tqdm

import pandas as pd

from haversine import haversine, Unit

from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
import json

from tqdm import tqdm

# 데이터베이스 및 모델 초기화
db = create_pgvector()
mysql_db = busan_db()


with open('./data/language_table_info.json', 'r') as f:
    lang_info = json.load(f)



def extract_restaurant_update_list(lang):
    
    visit_busan_place_list = [x[0] for x in mysql_db.select_place_id_from_table(lang_info[lang]["busan_table"][1])]
    current_distance_place_list = [x[0] for x in db.select_place_id_from_table(lang_info[lang]["pg_restaurant_table"])]
    
    update_list = list(set(visit_busan_place_list) - set(current_distance_place_list))
    
    if len(update_list) < 1:
        print("No data to update")

    
    return update_list

def extract_delete_list(lang):
    visit_busan_place_list = [x[0] for x in mysql_db.select_place_id_from_table(lang_info[lang]["busan_table"][1])]
    current_distance_place_list = [x[0] for x in db.select_place_id_from_table(lang_info[lang]["pg_restaurant_table"])]
    
    delete_list = list(set(current_distance_place_list) - set(visit_busan_place_list))
    
    if len(delete_list) < 1:
        print("No data to delete")

    
    return delete_list

## 메인 함수 --> 모든 데이터 업로드 후 거리 계산 및 적재
def main(mode):
    
    for lang, item in lang_info.items():
        if lang == "ko":
            continue
        
        print(f"Working on {lang}")
        work_count = 0
        
        
        if mode == "update":
            db.delete_table_data(item["pg_restaurant_table"])
            print(f"Deleted all data from tour_restaurant_distance for updating language: {lang}")
        
    
        ## place table에서 데이터 가져오기
        total_tour_df_list = []
        for table in item["busan_vector_table"]:
            df = mysql_db.select_as_dataframe(table)
            total_tour_df_list.append(df)
        total_tour_data = pd.concat(total_tour_df_list, ignore_index=True)
        
        ## restaurant table에서 데이터 가져오기
        total_restaurant_data = mysql_db.select_as_dataframe(item["busan_table"][1])
        
        ## 업데이트 시에만 해당하는 데이터만 가져오기
            
        for place_idx, place_row in tqdm(total_tour_data.iterrows(), total=len(total_tour_data)):
            for restaurant_idx, restaurant_row in total_restaurant_data.iterrows():
                place_coords = (place_row['LAT'], place_row['LNG'])
                restaurant_coords = (restaurant_row['LAT'], restaurant_row['LNG'])
                dist = haversine(place_coords, restaurant_coords, unit=Unit.KILOMETERS)
                # print(f"Distance between {place_row['MAIN_TITLE']} and {restaurant_row['MAIN_TITLE']}: {dist}")
                
                ret = db.insert_values(table_name = item["pg_restaurant_table"], insert_columns=['tour_place_id', 'restaurant_id', 'distance', 'cat'], values = [int(place_row['UC_SEQ']), int(restaurant_row['UC_SEQ']), dist, restaurant_row['CATE2_NM']])
                if ret == True:
                    work_count += 1
                # print(f'Insertion result: {ret}, place_id: {place_row["UC_SEQ"]}, restaurant_id: {restaurant_row["UC_SEQ"]}, distance: {dist}, cat: {restaurant_row["CATE2_NM"]}')
        

        print(f'Work done for {work_count} (places, restaurants) for language: {lang}')
        print(f'Total combination: {len(total_tour_data) * len(total_restaurant_data)}')
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="all", help="all or update")
    
    args = parser.parse_args()
    print(args)
    
    print("Inserting multi distance")
    
    main(args.mode)
    
    