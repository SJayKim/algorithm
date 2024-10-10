import os, sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

## DB 관련 모듈
from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
from haversine import haversine, Unit
# from route_optimization.place_matching import find_places_by_distance


from tqdm import tqdm

## 데이터 전처리 라이브러리
import json
import pandas as pd


import argparse


## 데이터베이스 및 모델 초기화
pg_db = create_pgvector()
mysql_db = busan_db()

with open("./data/language_table_info.json", "r") as f:
    inserting_table_list = json.load(f)

inserting_table_list = inserting_table_list["ko"]

with open("./data/major_category.json", "r") as f:
    major_category = json.load(f)
    
    
def extract_tour_place_update_list():
    visit_busan_place_list = []
    for table in inserting_table_list["busan_vector_table"]:
        visit_busan_place_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
    
    current_distance_place_list = [x[0] for x in pg_db.select_place_id_from_table(inserting_table_list["pg_vector_table"])]
    
    update_list = list(set(visit_busan_place_list) - set(current_distance_place_list))
    
    return update_list



def extract_restaurant_update_list():
   
    visit_busan_place_list = [x[0] for x in mysql_db.select_place_id_from_table(inserting_table_list["busan_table"][1])]
    current_distance_place_list = [x[0] for x in pg_db.select_place_id_from_table(inserting_table_list["pg_restaurant_table"])]
    
    update_list = list(set(visit_busan_place_list) - set(current_distance_place_list))
    
    if len(update_list) < 1:
        print("No data to update")
    
    return update_list

def extract_delete_list():
    visit_busan_place_list = [x[0] for x in mysql_db.select_place_id_from_table(inserting_table_list["busan_table"][1])]
    current_distance_place_list = [x[0] for x in pg_db.select_place_id_from_table(inserting_table_list["pg_restaurant_table"])]
    
    delete_list = list(set(current_distance_place_list) - set(visit_busan_place_list))
    
    if len(delete_list) < 1:
        print("No data to delete")
    
    return delete_list


def insert_main(tour_place_data, restaurant_place_data):
    work_count = 0
    for place_idx, place_row in tqdm(tour_place_data.iterrows(), total=len(tour_place_data)):
        for restaurant_idx, restaurant_row in restaurant_place_data.iterrows():
            place_coords = (place_row['lat'], place_row['lng'])
            restaurant_coords = (restaurant_row['lat'], restaurant_row['lng'])
            dist = haversine(place_coords, restaurant_coords, unit=Unit.KILOMETERS)
            # print(f"Distance between {place_row['place_title']} and {restaurant_row['place_title']}: {dist}")
            
            ret = pg_db.insert_values(table_name = 'tour_restaurant_distance', insert_columns=['tour_place_id', 'restaurant_id', 'distance', 'cat'], values = [int(place_row['place_id']), int(restaurant_row['place_id']), dist, restaurant_row['cat2']])
            if ret == True:
                work_count += 1
            # print(f'Insertion result: {ret}, place_id: {place_row["place_id"]}, restaurant_id: {restaurant_row["place_id"]}, distance: {dist}, cat: {restaurant_row["cat2"]}')
    
    print(f'Work done for {work_count} (places, restaurants)')
    print(f'Total combination: {len(tour_place_data) * len(restaurant_place_data)}')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default="all")
    
    args = parser.parse_args()
    print(args)
    
    if args.mode == "update":
        pg_db.delete_table_data("tour_restaurant_distance")
        print("Deleted all data from tour_restaurant_distance for updating")
    
    
    ## 관광지, 미식투어, 테마여행, 체험 데이터 가져와 합치기
    data_to_concat = []
    for table_name in  inserting_table_list["busan_vector_table"]:
        tour_place = pg_db.select_all_busan_data(major_cat_id=major_category[table_name]["id"], df_format=True)
        data_to_concat.append(tour_place)
        
    tour_place_data = pd.concat(data_to_concat, axis=0, ignore_index=True)

    
    restaurant_place_data = pg_db.select_all_busan_data(major_cat_id=2, df_format=True)
    
    if restaurant_place_data.empty or tour_place_data.empty:
        print("No data to insert==> Check the data")
        sys.exit(0)
    
    # print(tour_place_data.head())
    # print(restaurant_place_data.head())

    
    if not tour_place_data.empty and not restaurant_place_data.empty:
        insert_main(tour_place_data, restaurant_place_data)
   
    print("Done!")
            
    
    