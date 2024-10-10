import json
import random
import sys
from pgvector.pgvector_busan import create_pgvector
from curation_user_input_schedule_refactor import main
import argparse
import re
import os
import sys
import json
import numpy as np
import pandas as pd
import argparse
import time
from pprint import pprint
from tqdm import tqdm

# 필요한 모듈 임포트
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
from embedding_model.sroberta import embedding_model
from embedding_model.openai_embedding import openai_embedding
from route_optimization.route_optimize import find_shortest_path
from app.api.naver_map_api import get_naver_data

def load_language_table(path):
    with open(path, "r") as f:
        return json.load(f)

def map_text_to_category(text, keyword_dict):
    for category, keywords in keyword_dict.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None

def add_restaurants_split_schedule(best_path, chunk_size, data):
    print(f'best path : {best_path}')
    print(f'chunk size : {chunk_size}')
    print(f'data : {data}')
    def get_chunked_path(best_path, chunk_size):
        return [best_path[i:i + chunk_size] for i in range(0, len(best_path), chunk_size)]

    def insert_restaurants(day_schedule, data):
        start_restaurant = data[day_schedule[0]]["related_restaurants_ids"][0]
        end_restaurant = data[day_schedule[-1]]["related_restaurants_ids"][0]
        day_schedule.insert(1, start_restaurant)
        day_schedule.append(end_restaurant)
        return day_schedule

    chunked_path = get_chunked_path(best_path, chunk_size)
    schedule_with_restaurants = [insert_restaurants(day, data) for day in chunked_path]

    return schedule_with_restaurants

def fetch_place_info(place_id, lang, mysql_db, pg_db):
    
    lang_table = load_language_table("/home/chatbot/visit_busan/algorithm/data/language_table_info.json")

    place_info = mysql_db.select_place_info(place_id=place_id, lang=lang)
    restaurant_info = pg_db.select_all_restaurant_data_by_place_id(place_id=place_id, distance=20, cat='식당', lang=lang)
    
    place_name = place_info[0][27]
    cleaned_name = re.sub(r'\(한[^)]*\)', '', place_name)
    cleaned_name = re.sub(r'\s*,\s*', ', ', cleaned_name).strip(', ')
    
    place_type = map_text_to_category(place_info[0][7], lang_table[lang]["keyword_mapping"]) or \
                 map_text_to_category(place_info[0][8], lang_table[lang]["keyword_mapping"])
    
    place_output = {
        "id": place_info[0][0],
        "menu_cd": place_info[0][1],
        "name": cleaned_name,
        "type": place_type,
        "gugun_nm": place_info[0][6],
        "lat": place_info[0][18],
        "lng": place_info[0][19],
        "image_normal": place_info[0][-3],
        "image_thumb": place_info[0][-2],
        "related_restaurants_ids": [restaurant[1] for restaurant in restaurant_info] if restaurant_info else []
    }
    if lang == 'ko' and (place_type == '음식점' or place_type == '카페'):
        naver_link = get_naver_data(cleaned_name)
        place_output.update({"naver_link": naver_link})
  
    return place_output

def final_schedule_formatting(best_path_with_restaurants, tour_place_dict, lang, mysql_db, pg_db):
    return_list = []

    for day, place_ids in enumerate(best_path_with_restaurants, start=1):
        output_dict = {'day': day, 'items': []}
        for idx, place_id in enumerate(place_ids, start=1):
            item_dict = {'order': idx}
            try:
                place_name = tour_place_dict[place_id]['name']
                cleaned_name = re.sub(r'\(한[^)]*\)', '', place_name)
                cleaned_name = re.sub(r'\s*,\s*', ', ', cleaned_name).strip(', ')
                tour_place_dict[place_id]['name'] = cleaned_name
                item_dict.update(tour_place_dict[place_id])
            except KeyError:
                item_dict.update(fetch_place_info(place_id, lang, mysql_db, pg_db))
            item_dict.pop('related_restaurants_ids', None)
            output_dict['items'].append(item_dict)
        return_list.append(output_dict)

    return return_list

def main(args, mysql_db, pg_db, openai_vectorizer, vectorizer): 
    # 입력 파라미터 처리
    theme = args.theme
    keywords = args.keywords or []
    preferences = args.preferences or ""
    place_num = args.days * 3
    lang = args.lang

    # 임베딩 처리
    if lang == "ko":
        print(f'debug theme : {theme}')
        theme_embedding = vectorizer.get_chunked_embeddings(', '.join(theme))
        processed_embedding = vectorizer.get_chunked_embeddings(vectorizer.preprocess(', '.join(keywords) + ' ' + preferences)) if keywords or preferences else None
    elif lang in ["cn_zh", "cn_tw", "jp", "en"]:
        theme_embedding = openai_vectorizer.get_chunked_embeddings(', '.join(theme))
        processed_embedding = openai_vectorizer.get_chunked_embeddings(', '.join(keywords) + ' ' + preferences) if keywords or preferences else None

    # 관광지 추천
    
    ## 군구별 관광지 필터링 --> args.gugun_ids 리스트로 받아서 해당 군구의 관광지만 필터링
    if args.gugun_ids:
        gugun_place_ids = mysql_db.select_gugun_place_ids(args.gugun_ids, lang)
    else:
        gugun_place_ids = None
    
    ## 관광지 추천 (Theme 있는 경우, 없는 경우)
    ret = pg_db.search_by_meta(theme_vector=theme_embedding, keywords_vector=processed_embedding, top_k=place_num, lang=lang, gugun_list=gugun_place_ids) if processed_embedding else pg_db.search_by_vector(theme_embedding, top_k=place_num, lang=lang, gugun_list=gugun_place_ids)

    ## 관광지 정보 조회 및 포메팅 프로세스
    if ret:
        tour_place_dict = {}
        for item in ret:
            print(f'debug place id : {item[0]}')
            place_info = fetch_place_info(item[0], lang, mysql_db, pg_db)
            if place_info['type'] == '음식점' or place_info['type'] == '카페':
                naver_link = get_naver_data(place_info['name'])
                place_info.update(naver_link)
            tour_place_dict[item[0]] = place_info

        ## 경로 최적화 (최단거리 경로)
        best_path = find_shortest_path(tour_place_dict)
        
        ## 최적 경로에 음식점 추가
        best_path_with_restaurants = add_restaurants_split_schedule(best_path, 3, tour_place_dict)
        
        ## 최종 스케줄 포맷팅
        final_schedule = final_schedule_formatting(best_path_with_restaurants, tour_place_dict, lang, mysql_db, pg_db)

        print(f'optimized schedule:====================\n')
        pprint(final_schedule, sort_dicts=False)
        return final_schedule
    else:
        print("No matching place found")
        sys.exit(0)

## 각 DB , Embedding 모델 초기화
def initialize_services():
    mysql_db = busan_db()
    pg_db = create_pgvector()
    openai_vectorizer = openai_embedding()
    vectorizer = embedding_model()
    return mysql_db, pg_db, openai_vectorizer, vectorizer


def call_main(theme, keywords, days, lang, mysql_db, pg_db, openai_vectorizer, vectorizer):
    
    # 필요한 파라미터를 직접 설정
    args = argparse.Namespace(
        theme= theme,  # 테마를 리스트 형태로 설정
        keywords= keywords,  # 키워드를 리스트 형태로 설정 (옵션)
        preferences= None,  # 선호도 (옵션)
        days=days,  # 여행 일수를 설정
        debug=False,  # 디버그 모드 설정 (옵션)
        lang=lang,  # 언어 설정
        gugun_ids=None  # 필터링할 군구 ID 리스트 (옵션)
    )

    ret = main(args, mysql_db, pg_db, openai_vectorizer, vectorizer)
    
    return ret


with open("./data/language_table_info.json", "r") as f:
    lang_table_info = json.load(f)



if __name__ == "__main__":
    mysql_db, pg_db, openai_vectorizer, vectorizer = initialize_services()

    count = 0
    for i in range(40):
        num_meta = random.randint(3, 5)
        num_theme = random.randint(1, 3)
        days = random.randint(2, 3)
        
        for lang in lang_table_info:
            if lang == "ko":
                col_meta = "meta_ko"
                col_theme = "theme_cat_name"
            else:
                col_meta = f'meta_{lang}'
                col_theme = f'theme_cat_{lang}'
                
            meta_sql = f'''select meta_id, {col_meta} from search_meta_info order by random() limit {num_meta}'''
            theme_sql = f'''select theme_cat_id, {col_theme} from theme_category order by random() limit {num_theme}'''
            
            meta_result = pg_db.run_queryset(meta_sql)
            theme_result = pg_db.run_queryset(theme_sql)
            
            ## id, keyword 분리
            meta_ids = [x[0] for x in meta_result]
            theme_ids = [x[0] for x in theme_result]
            meta_keywords = [x[1] for x in meta_result]
            theme_keywords = [x[1] for x in theme_result]
            
            print(f'lang: {lang}, meta: {meta_keywords}, theme: {theme_keywords}') 
            try:
                schedule = call_main(theme_keywords, meta_keywords, days, lang, mysql_db, pg_db, openai_vectorizer, vectorizer)
            except:
                print("curation error")
                continue
            
            
            ## insert 작업
            if schedule:
                
                ## example schedule 넣기
                print("===================================== insert schedule example =====================================")
                sql = f'''insert into example_schedules (created_at, updated_at, duration_id, travel_type_id, lang) values (now(), now(), {days}, 3, '{lang}') returning id'''
                schedule_id = pg_db.run_queryset(sql)[0][0]
                
                print("===================================== insert schedule example meta theme =====================================")

                ## schedule theme, meta  넣기
                for theme_id in theme_ids:
                    sql = f'''insert into example_schedule_theme_category (theme_cat_id, example_schedule_id) values ({theme_id}, '{schedule_id}')'''
                    ret = pg_db.run_queryset(sql)
                    print(f'theme insert: {ret}, theme_id: {theme_id}')
                
                for meta_id in meta_ids:
                    sql = f'''insert into example_schedule_meta (meta_id, example_schedule_id) values ({meta_id}, '{schedule_id}')'''
                    ret = pg_db.run_queryset(sql)
                    print(f'meta insert: {ret}, meta_id: {meta_id}')
                    
                ## schedlue details 넣기
                print("===================================== insert schedule details =====================================")

                for schedule_data in schedule:
                    day_order = schedule_data["day"]
                    
                    for tour_place in schedule_data["items"]:
                        place_order = tour_place["order"]
                        place_id = tour_place["id"]
                        category = tour_place["type"]
                        
                        sql = f'''insert into schedule_details (place_id, day, "order", schedule_id, example_schedule_id, category) values ({place_id}, {day_order}, {place_order}, NULL, '{schedule_id}', '{category}')'''
                        
                        ret = pg_db.run_queryset(sql)
                        print(f'detail insert: {ret}, place_id: {place_id}')
                        
                    
                