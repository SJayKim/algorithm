import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


## 필요 모듈 import
from pgvector.pgvector_busan import create_pgvector
from embedding_model.sroberta import embedding_model
from route_optimization.route_optimize import find_shortest_path

import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse

from pprint import pprint

import matplotlib.pyplot as plt
import time




def visualize_optimized_path(optimized_place_data):
    fig, ax = plt.subplots()

    # 경로 데이터 추출
    place_ids = list(optimized_place_data.keys())
    latitudes = [optimized_place_data[place_id]['place_coords'][0] for place_id in place_ids]
    longitudes = [optimized_place_data[place_id]['place_coords'][1] for place_id in place_ids]
    place_titles = [optimized_place_data[place_id]['place_title'] for place_id in place_ids]

    # 경로 표시
    ax.plot(longitudes, latitudes, marker='o', linestyle='-', color='b')

    # 각 지점에 텍스트 추가
    for i, title in enumerate(place_titles):
        ax.text(longitudes[i], latitudes[i], title, fontsize=9, ha='right')

    # 그래프 설정
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Optimized Tourist Path')
    plt.grid(True)

    # 이미지 저장
    plt.savefig('./data/images/optimized_tourist_path.png')

    # 그래프 표시
    plt.show()

def curation_main(recommended_places):
    tour_place_dict = {}
    for idx, item in enumerate(recommended_places, start=1):
        print(f'ranking: {idx}, place_id: {item[0]}, similarity: {item[1]}')
        place_info = db.select_all_busan_data(place_id=item[0])
        restaurant_info = db.select_all_restaurant_data_by_place_id(place_id=item[0], distance = 5, cat = '식당')
        cafe_info = db.select_all_restaurant_data_by_place_id(place_id=item[0], distance = 5, cat = '카페')
        
        place_keyword = db.select_all_keyword_by_placeid(place_id=item[0])
        
        if args.debug:
            print(f'place_title: {place_info[0][1]}, \nplace_hash_tag: {place_info[0][8]}, \nplace keyword: {place_keyword} \nplace_description: {place_info[0][9]}')

        tour_place_dict[item[0]] = {
            'place_title': place_info[0][1],
            'place_description': place_info[0][9],
            'place_coords': (place_info[0][5], place_info[0][6]),
            'related_restaurants_ids' : [res[1] for res in restaurant_info] if restaurant_info else None,
            'related_cafes_ids': [cafe[1] for cafe in cafe_info] if cafe_info else None,
        }

        # place_keyword = db.select_all_keyword_by_placeid(place_id=item[0])
        # print(f'place_title: {place_info[0][1]}, \nplace_hash_tag: {place_info[0][8]}, \nplace keyword: {place_keyword} \nplace_description: {place_info[0][9]}') 
    optimized_schedule = find_shortest_path(tour_place_dict)

    return optimized_schedule




if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_query", type=str, help="Query for the tour place curation")
    parser.add_arguement("--debug", type=bool, help="Debug mode", default = False)
    # parser.add_argument("--mode", type = str, help="Mode for the tour place curation", default = "s")
    args = parser.parse_args()
    ## 각 모듈 초기화
    db = create_pgvector()
    vectorizer = embedding_model()
    # llm = llm_ner(model_name='gpt-4o')
    processed_query = vectorizer.preprocess(args.input_query)
    query_vector = vectorizer.get_chunked_embeddings(processed_query)
    
    ## 유저 쿼리로부터 관광지 추천
    ret = db.search_by_vector(vector = query_vector, top_k = 5)
       
    if ret:
       final_schedule = curation_main(ret)
    else:
        print("No matching place found")
        sys.exit(0)
    
   
    ## 스케줄링 최적화
    
    print(f'optimized schedule:=====')
    pprint(final_schedule[0], sort_dicts=False)
    end = time.time()
    print(f'optimized distance: {final_schedule[1]} KM')
    print(f'optimized time: {end-start} sec')
    
    
    # visualize_optimized_path(optimized_schedule[0])
    
    