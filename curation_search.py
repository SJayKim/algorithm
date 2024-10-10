import os
import sys
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import argparse
from pprint import pprint
import matplotlib.pyplot as plt
import time

from pgvector.pgvector_busan import create_pgvector
from embedding_model.sroberta import embedding_model
from embedding_model.openai_embedding import openai_embedding
from route_optimization.route_optimize import find_shortest_path
from db.busan_db import busan_db

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# Initialize modules
pg_db = create_pgvector()
mysql_db = busan_db()
sroberta_model = embedding_model()  
openai_model = openai_embedding()

# Define functions

## keyword (관광지, 카페, 음식점 등)에 따라 카테고리 매핑
def map_text_to_category(text, keyword_dict):
    for category, keywords in keyword_dict.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None


## 장소 정보 가져오는 함수 
def fetch_place_info(place_id, lang, lang_table):
    place_info = mysql_db.select_place_info(place_id=place_id, lang=lang)
    if not place_info:
        return None
    
    place_output = {
        "id": place_info[0][0],
        "menu_cd": place_info[0][1],
        "name": place_info[0][4],
        "type": map_text_to_category(place_info[0][7], lang_table[lang]["keyword_mapping"]) or map_text_to_category(place_info[0][8], lang_table[lang]["keyword_mapping"]),
        "lat": place_info[0][18],
        "lng": place_info[0][19],
        "image_normal": place_info[0][-3],
        "image_thumb": place_info[0][-2],
    }
    return place_output

## 최종 결과 포맷팅
def final_formatting(place_ids, lang, lang_table):
    return_list = []

    for idx, place_id in enumerate(place_ids, start=1):
        output_dict = {
            'order': idx,
            'items': []
        }

        place_info = fetch_place_info(place_id, lang, lang_table)
        if place_info:
            output_dict["items"].append(place_info)
            return_list.append(output_dict)
        else:
            print(f"Error in fetching place info for place_id: {place_id}")
    
    return return_list


# def load_language_table(path):
#     with open(path, "r") as f:
#         return json.load(f)

def load_language_table(path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, "data", "language_table_info.json")
    with open(full_path, "r") as f:
        return json.load(f)

def get_embedding_model(lang):
    return sroberta_model if lang == "ko" else openai_model

def generate_embeddings(theme, keywords, query, model):
    
    processed_text = ' '.join([query, keywords, theme])
    output_embedding = model.get_chunked_embeddings(processed_text)
    
    return output_embedding

def main(args):
    if __name__ == "__main__":
        lang_table = load_language_table("./data/language_table_info.json")
        args = vars(args)
    else:
        # lang_table = load_language_table("/algorithm/data/language_table_info.json")
        lang_table = load_language_table("data/language_table_info.json")

    if args['lang']not in lang_table:
        raise ValueError("Invalid language, please choose one of the following: ko, cn_zh, cn_tw, jp, en")
    
    model = get_embedding_model(args['lang'])
    query_embedding = generate_embeddings(args['theme'], args['keywords'], args['query'], model)
    
   
    ret = pg_db.search_by_vector(vector=query_embedding, lang=args['lang'], top_k=args['top_k'])
    
    place_ids = [x[0] for x in ret]
    # print(place_ids)
    search_result = final_formatting(place_ids, args['lang'], lang_table)
    pprint(search_result, sort_dicts=False)
    
    return place_ids
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--theme', type=str, default = "")
    parser.add_argument('--keywords', type=str, default = "")
    parser.add_argument('--query', type=str)
    parser.add_argument('--lang', type=str, default="ko")
    parser.add_argument('--top_k', type=int, default=12)

    args = parser.parse_args()
    search_place_ids = main(args)
    print(search_place_ids)
    
