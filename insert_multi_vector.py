import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import argparse


from embedding_model.openai_embedding import openai_embedding
from pgvector.pgvector_busan import create_pgvector
from db.busan_db import busan_db
import json

from tqdm import tqdm

# 데이터베이스 및 모델 초기화
db = create_pgvector()
mysql_db = busan_db()
# roberta_model = embedding_model()
openai_model = openai_embedding()
# llm = llm_translator()


with open("./data/language_table_info.json", "r") as f:
    table_mapping = json.load(f)


# 번역 함수
def preprocess_embedding(text):
    ## 2000자 이상이면 2000자로 자르기 --> 500자 단위로 자르기 구현 필요 text 없을 시 None 값 출력
    if text != "":
        processed_text = openai_model.preprocess(text)
        embedding_vector = openai_model.get_chunked_embeddings(processed_text)
        return embedding_vector
    else:
       
        return None

def extract_update_list(lang):
    visit_busan_place_list = []
    for table in table_mapping[lang]["busan_vector_table"]:
        visit_busan_place_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
    current_distance_place_list = [x[0] for x in db.select_place_id_from_table(table_mapping[lang]["pg_vector_table"])]
    
    update_list = list(set(visit_busan_place_list) - set(current_distance_place_list))
    
    if len(update_list) < 1:
        print("No data to update")

    return update_list


def extract_delete_list(lang):
    visit_busan_place_list = []
    for table in table_mapping[lang]["busan_vector_table"]:
        visit_busan_place_list += [x[0] for x in mysql_db.select_place_id_from_table(table)]
    current_distance_place_list = [x[0] for x in db.select_place_id_from_table(table_mapping[lang]["pg_vector_table"])]
    
    delete_list = list(set(current_distance_place_list) - set(visit_busan_place_list))
    
    if len(delete_list) < 1:
        print("No data to delete")

    
    return delete_list
    


def main(mode):
    for lang, tables in tqdm(table_mapping.items(), total=len(table_mapping)):
        if lang == "ko":
            continue
        print(f'current language: {lang}, tables: {tables["busan_vector_table"]}')
        if mode == "all":
            print(f"mode: {mode} --> Inserting all data mode...")
            place_ids = []
            for table in tables["busan_vector_table"]:
                place_ids += [x[0] for x in mysql_db.select_place_id_from_table(table)]
            
            place_ids = list(set(place_ids))
        elif mode == "update":
            print(f"mode: {mode} --> Inserting new data mode...")
            place_ids = extract_update_list(lang)
            
            ## 삭제된 데이터 처리
            delete_list = extract_delete_list(lang)
            
            if len(delete_list) > 0:
                ret = db.delete_place_ids_from_table(table_name=tables["pg_vector_table"], place_id_list=delete_list)
                print(f'lang: {lang}, \ndelete list: {delete_list}, \ndelete result: {ret}')

            if len(place_ids) < 1:
                print("No data to update")
                continue
        
        places_num = 0
        for place_id in place_ids:
            place_info = mysql_db.select_place_info(place_id=place_id, lang = lang, df=True)
            ## hash tag 및 overview 가져오기
            place_hash_tags = place_info["HASH_TAG"][0].replace("#", ' ') if not place_info.empty else ""
            place_overview = place_info["ITEMCNTNTS"][0] if not place_info.empty else ""
            hash_tag_embeddings, overview_embeddings = preprocess_embedding(place_hash_tags), preprocess_embedding(place_overview) 
            ret = db.insert_values(table_name=tables["pg_vector_table"], insert_columns = ["place_id", "meta_vector", "overview_vector", "review_vector"], values=[int(place_id), hash_tag_embeddings, overview_embeddings, None])
            
            print(f'place_id: {place_id} , insert result: {ret}')
            places_num += 1
        print(f'lang: {lang}, places_num: {places_num} ==========')
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, help="all or update")
    
    args = parser.parse_args()
    
    main(args.mode)
    print("Done!")