import re
import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


## 필요 모듈 import
from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
from embedding_model.sroberta import embedding_model
from embedding_model.openai_embedding import openai_embedding
from route_optimization.route_optimize import find_shortest_path

import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from pprint import pprint
import time

# from app.api.naver_map_api import get_naver_data

# with open('./data/major_category.json', 'r') as f:
#     major_category = json.load(f)
    
## 각 모듈 초기화
mysql_db = busan_db()
pg_db = create_pgvector()
openai_vectorizer = openai_embedding()
vectorizer = embedding_model()



def parse_themes(input_themes):
    return input_themes.split(',')

# def load_language_table(path):
#     with open(path, "r") as f:
#         return json.load(f)

def load_language_table(path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, "data", "language_table_info.json")
    with open(full_path, "r") as f:
        return json.load(f)

## 관광지, 음식점, 카페 구분 함수
def map_text_to_category(text, keyword_dict):
    for category, keywords in keyword_dict.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None

## 최적화된 경로에 음식점 추가
def add_restaurants_split_schedule(best_path, chunk_size, data):
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

## place_id로 관광지 정보 가져오기
def fetch_place_info(place_id, lang, pg_db, mysql_db):
    ## 언어 매핑 json 파일
    if __name__ == "__main__":
        lang_table = load_language_table("./data/language_table_info.json")
    else:
        # lang_table = load_language_table("/algorithm/data/language_table_info.json")
        lang_table = load_language_table("data/language_table_info.json")

    place_info = mysql_db.select_place_info(place_id=place_id, lang=lang)
    restaurant_info = pg_db.select_all_restaurant_data_by_place_id(place_id=place_id, distance = 20, cat = '식당', lang=lang)
    
    place_name = place_info[0][27]
    cleaned_name = re.sub(r'\(한[^)]*\)', '', place_name)
    cleaned_name = re.sub(r'\s*,\s*', ', ', cleaned_name).strip(', ')
    
    place_type = map_text_to_category(place_info[0][7], lang_table[lang]["keyword_mapping"]) if map_text_to_category(place_info[0][7], lang_table[lang]["keyword_mapping"]) else map_text_to_category(place_info[0][8], lang_table[lang]["keyword_mapping"])
    
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

def festival_formatting(festival_info):
    return_list = []

    for idx, festival_data in enumerate(festival_info, start=1):
        output_dict = {}
        output_dict['order'] = idx
        output_dict['items'] = []
        
    
        try:
            output_dict["items"].append({
        "id": festival_data[0],
        "menu_cd": festival_data[1],
        "name": festival_data[4],
        "type": festival_data[7],
        "lat": festival_data[18],
        "lng": festival_data[19],
        "image_normal": festival_data[-3],
        "image_thumb": festival_data[-2]
    })
        except:
            print(f"Error in fetching festival info for festival id: {festival_data[0]}")
            continue
            ## 연관 음식점 id 데이터 삭제
  
        return_list.append(output_dict)

    return return_list

## 최종 스케줄 포멧팅
def final_schedule_formatting(best_path_with_restaurants, tour_place_dict, lang, pg_db, mysql_db):
    return_list = []

    for day, place_ids in enumerate(best_path_with_restaurants, start=1):
        output_dict = {}
        output_dict['day'] = day
        output_dict['items'] = []
        for idx, place_id in enumerate(place_ids, start=1):
            item_dict = {}
            item_dict['order'] = idx
            try:
                place_name = tour_place_dict[place_id]['name']
                cleaned_name = re.sub(r'\(한[^)]*\)', '', place_name)
                cleaned_name = re.sub(r'\s*,\s*', ', ', cleaned_name).strip(', ')
                tour_place_dict[place_id]['name'] = cleaned_name
                item_dict.update(tour_place_dict[place_id])
            except:
                item_dict.update(fetch_place_info(place_id, lang, pg_db, mysql_db))
            ## 연관 음식점 id 데이터 삭제
            item_dict.pop('related_restaurants_ids')
            output_dict['items'].append(item_dict)
        return_list.append(output_dict)

    return return_list
            

def curation_main(recommended_places, lang, pg_db, mysql_db):
    tour_place_dict = {}
    for idx, item in enumerate(recommended_places, start=1):
        # cafe_info = pg_db.select_all_restaurant_data_by_place_id(place_id=item[0], distance = 5, cat = '카페')
        
        ## 데이터 포멧
        place_info = fetch_place_info(item[0], lang, pg_db, mysql_db)
        if place_info['type'] == '음식점' or place_info['type'] == '카페':
            ## 네이버 지도 api에 접속하여 링크 받아옴
            naver_link = pg_db.get_naver_url(item[0])
            place_info.update(naver_link)
            
        tour_place_dict[item[0]] = place_info
 
    ## 경로 최적화 통한 id 추출
    best_path = find_shortest_path(tour_place_dict)
    # print(f'debug best_path: {best_path}')
    
    ## 추출된 id 연관 식당 추가하여 데이터 구성
    best_path_with_restaurants = add_restaurants_split_schedule(best_path, 3, tour_place_dict)
    # print(f'debug best_path_with_restaurants: {best_path_with_restaurants}')
    
    ## 최종 연관식당 포함된 스케줄 id 데이터 포멧팅
    optimized_schedule = final_schedule_formatting(best_path_with_restaurants, tour_place_dict, lang, pg_db, mysql_db)
    # print(f'debug optimized_schedule: {optimized_schedule}')
    ## 연관 음식점 추가

    ## 연관 음식점 id 데이터 삭제
    # for day in optimized_schedule:
    #     for order in optimized_schedule[day]:
    #         del optimized_schedule[day][order]["related_restaurants_ids"]
        
    
    return optimized_schedule



if __name__ == "__main__":
     ## 언어 매핑 json 파일
    with open('./data/language_table_info.json', 'r') as f:
        lang_table = json.load(f)

    with open('./data/theme_category.json', 'r') as f:
        theme_category = json.load(f)
    
    
    parser = argparse.ArgumentParser()
    ## 사용자 입력값
    parser.add_argument("--theme", type=parse_themes, help=f"Tour place theme for the curation it should be one of in the list {[x[0] for x in list(theme_category.values())]}", required=True)
    parser.add_argument("--keywords", type=parse_themes, help="Keywords for the tour place curation, examples: ['데이트 코스', '힐링 여행', '반려견동반 여행']")
    parser.add_argument("--preferences", type=str, help="Preferences for the tour place curation, examples: '드라이브 하기 좋은 추천 여행지'")
    # parser.add_argument("--place_num", type=int, help="Number of places to visit", default = 5)
    parser.add_argument("--days", type=int, help="Number of days for the trip", required=True)
    parser.add_argument("--debug", type=bool, help="Debug mode", default = False)
    parser.add_argument("--lang", type=str, help="Language for the tour place curation", default = 'ko')
    parser.add_argument("--gugun_ids", nargs='+', help="List of gugun ids to filter the places")

    # parser.add_argument("--month", type=int, help="Month for the tour place curation", required=True)
    

    args = parser.parse_args()
    print(args)
    
   
    
        
    ## 조건 적합성 확인
    # if args.month not in range(1, 13):
    #     raise ValueError("Invalid month")
    if args.days not in [1,2,3]:
        raise ValueError("Invalid days")
    if args.lang not in list(lang_table.keys()):
        print(f'language should be one of in the list ["ko", "cn_zh", "cn_tw", "jp", "en"]')
        raise ValueError("Invalid language")
        
 
    ## 각 모듈 초기화
    mysql_db = busan_db()
    pg_db = create_pgvector()
    openai_vectorizer = openai_embedding()
    vectorizer = embedding_model()
    
    theme = args.theme
    keywords = args.keywords or []
    preferences = args.preferences or ""
    place_num = args.days * 3
    lang = args.lang
    gugun_ids = args.gugun_ids
    # month = args.month

    
    print(f'theme: {theme}, keywords: {keywords}, preferences: {preferences}, place_num: {place_num}, lang: {lang}, gugun_ids: {gugun_ids}')
    
    
    start = time.time()
    ## 키워드 및 선호도 임베딩 처리
    
    ## 한국어 임베딩
    if lang == "ko":
        preferences = vectorizer.preprocess(preferences)
        query_embedding = vectorizer.get_chunked_embeddings(preferences)
        ## 키워드 및 선호도 임베딩
        if keywords or theme:
            processed_wording = vectorizer.preprocess(', '.join(keywords) + ' ' + ' ,'.join(theme))
            processed_embedding = vectorizer.get_chunked_embeddings(processed_wording)
            ## 최종 임베딩 계산 --> 자연어 80%, 키워드 20% 가중치
            query_embedding = [0.8*x + 0.2*y for x, y in zip(query_embedding, processed_embedding)]
            
    ## 영어, 중국어, 일본어 임베딩
    elif lang in ["cn_zh", "cn_tw", "jp", "en"]:
        query_embedding = openai_vectorizer.get_chunked_embeddings(preferences)
        ## 키워드 및 선호도 임베딩
        if keywords or theme:
            processed_wording = ', '.join(keywords) + ' ' + ' ,'.join(theme)
            processed_embedding = openai_vectorizer.get_chunked_embeddings(processed_wording)
            
            query_embedding = [0.8*x + 0.2*y for x, y in zip(query_embedding, processed_embedding)]
    
    
    ## 테마 및 키워드로 관광지 추천 --> 테마 필수 옵션, 키워드 및 선호도 선택 옵션
    ## 테마만 들어올 경우 search_by_vector로 검색
    ## 키워드 및 선호도가 들어올 경우 search_by_meta로 검색
    if gugun_ids:
        gugun_place_ids = mysql_db.select_gugun_place_ids(gugun_ids, lang)
    else:
        gugun_place_ids = None
    
    ret = pg_db.search_by_vector(vector = query_embedding, top_k = place_num, lang = lang, gugun_list = gugun_place_ids)
    
    
    if ret:
        final_schedule = curation_main(ret, lang, pg_db, mysql_db)
    else:
        print("No matching place found")
        sys.exit(0)
    
    print(f'optimized schedule:====================\n')
    pprint(final_schedule, sort_dicts=False)
    
    
    ## 축제 데이터 검색
    # festival_ret = mysql_db.select_month_festival_info(month = month, lang = lang)
    # festival_ret = festival_formatting(festival_ret)
    # print(f"festival for month {month}====================\n")
    # pprint(festival_ret, sort_dicts=False)
    
    end = time.time()
    
    print(f'Running time: {end-start} sec')

    
    
    
  