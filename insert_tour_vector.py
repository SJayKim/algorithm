import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
from embedding_model.sroberta import embedding_model

import argparse


import json
import pandas as pd

db = create_pgvector()
embeddings = embedding_model()
mysql_db = busan_db()

with open("./data/language_table_info.json", "r") as f:
    inserting_table_list = json.load(f)
inserting_table_list = inserting_table_list["ko"]["busan_vector_table"]

## 삭제된 데이터 삭제 (부산관광공사 데이터 확인 후 postgres tour_vector 삭제)
def delete_removed_data():
    visit_busan_place_list = []
    for table in inserting_table_list:
        visit_busan_place_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
        
    current_vector_place_list = [x[0] for x in db.select_place_id_from_table("tour_vector")]
    
    delete_list = list(set(current_vector_place_list) - set(visit_busan_place_list))
    
    if len(delete_list) < 1:
        print("No data to delete")
        return False
    
    ret = db.delete_place_ids_from_table("tour_vector", delete_list)
    print(f'Deleted rows {delete_list} {ret}')

    return ret

## 업데이트할 데이터 추출 (부산관광공사 데이터 확인 후 postgres로 업데이트)
def extract_update_list():
    visit_busan_place_list = []
    for table in inserting_table_list:
        visit_busan_place_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
        
    current_vector_place_list = [x[0] for x in db.select_place_id_from_table("tour_vector")]
    
    update_list = list(set(visit_busan_place_list) - set(current_vector_place_list))
    
    if len(update_list) < 1:
        print("No data to update")
    
    return update_list

def main(mode):
    ## place_id 리스트 가져오기
    if mode == 'all':
        ## 관광지, 테마, 미식투어, 해양체험 포함
        place_id_list = []
        for table in inserting_table_list:
            place_id_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
        place_id_list = list(set(place_id_list))
        
    elif mode == 'update':
        delete_removed_data()
        place_id_list = extract_update_list()
        
    if len(place_id_list) < 1:
        print("No data to update")
    work_count = 0
    for place_id in place_id_list:
        
        ## 데이터 가져오기
        vector_data = db.select_vector_data_by_placeid(place_id)
        # print(f'before meta_keywords: {meta_keywords}')
        
        ## meta_vector embedding
        if vector_data["keywords"] or vector_data["hash_tags"] != "":
            meta_keywords = vector_data["keywords"] + ' ' + vector_data["hash_tags"]
            keywords_embedding = embeddings.get_chunked_embeddings(meta_keywords)
            keywords_embedding = str(keywords_embedding) if keywords_embedding else None
        else:
            keywords_embedding = None
        # print(f'after meta_keywords: {keywords_embedding}')
        
        ## overview 가져오기 및 임베딩

        # print(f'before overview: {overview}')
        if vector_data["overview"] != "":
            # print(f'overview: {vector_data["overview"]}')
            overview = embeddings.preprocess(vector_data["overview"])
            overview_embedding = embeddings.get_chunked_embeddings(overview)
            overview_embedding = str(overview_embedding) if overview_embedding else None
        else:
            overview_embedding = None
        # print(f'after overview: {overview_embedding}')
            
        ## review 가져오기 및 임
        if vector_data["reviews"]:
            # print(f'reviews: {vector_data["reviews"]}')
            review_data = embeddings.preprocess(vector_data["reviews"])
            reviews_embedding = embeddings.get_chunked_embeddings(review_data)
            reviews_embedding = str(reviews_embedding) if reviews_embedding else None
        else:
            reviews_embedding = None
        # print(f'after reviews: {reviews_embedding}')
        
        ## 임베딩 데이터 삽입
        ret = db.insert_values(table_name = "tour_vector", insert_columns=["place_id", "meta_vector", "overview_vector", "review_vector"], values=[int(place_id), keywords_embedding, overview_embedding, reviews_embedding])
        if ret == True:
            work_count += 1
        print(f'insert result for place_id: {place_id} is {ret}')
    
    print(f'Work done for {work_count} places')
    print(f'Total places: {len(place_id_list)}')
    
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default = 'all', help="'all' or 'update' are available")
    args = parser.parse_args()
    

        
        
        
    main(args.mode) 