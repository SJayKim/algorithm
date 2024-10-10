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
# from app.api.naver_map_api import get_naver_data

def parse_themes(input_themes):
    return input_themes.split(',')

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
        naver_link = pg_db.get_naver_url(place_info[0][0])
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

def main(args):
    # 서비스 초기화
    mysql_db, pg_db, openai_vectorizer, vectorizer = initialize_services()

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
                naver_link = pg_db.get_naver_url(item[0])
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", type=parse_themes, help="Tour place theme for the curation", required=True)
    parser.add_argument("--keywords", type=parse_themes, help="Keywords for the tour place curation")
    parser.add_argument("--preferences", type=str, help="Preferences for the tour place curation")
    parser.add_argument("--days", type=int, help="Number of days for the trip", required=True)
    parser.add_argument("--debug", type=bool, help="Debug mode", default=False)
    parser.add_argument("--lang", type=str, help="Language for the tour place curation", default='ko')
    parser.add_argument("--gugun_ids", nargs='+', help="List of gugun ids to filter the places")
    args = parser.parse_args()

    if args.days not in [1, 2, 3]:
        raise ValueError("Invalid days")

    main(args)
