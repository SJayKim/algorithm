from pgvector.pgvector_busan import create_pgvector
import argparse
import json


def main(data_type):
    if data_type == "major":
        data_path = "./data/major_category.json"
        table_name = "major_category"
        columns = ["major_cat_id", "major_cat_name"]
        print(f'table info: {table_name}, columns: {columns}')
    elif data_type == "theme":
        data_path = "./data/theme_category.json"
        table_name = "theme_category"
        columns = ["theme_cat_id", "theme_cat_name", "theme_cat_en", "theme_cat_cn_zh", "theme_cat_cn_tw", "theme_cat_jp"]
        print(f'table info: {table_name}, columns: {columns}')
    elif data_type == 'search_theme':
        data_path = "./data/search_theme_category.json"
        
        ## table 이름 설정
        theme_table_name = "search_theme_category"
        keywords_table_name = "search_meta_info"
        
        ## column 이름 설정
        theme_columns = ["theme_cat_ko", "theme_cat_en", "theme_cat_cn_zh", "theme_cat_cn_tw", "theme_cat_jp"]
        keywords_columns = ["meta_ko", "meta_en", "meta_cn_zh", "meta_cn_tw", "meta_jp", "theme_cat_id"]

    
    
    ## pgvector 객체 생성
    db = create_pgvector()
    
    ## major_cat.json 파일 로드
    with open(data_path, "r") as f:
        cat_dict = json.load(f)        
    
    
    if data_type == "theme":
        print("Inserting tour theme category data...")
        # db.delete_table_data(table_name=table_name)
        
        for cat in cat_dict:
            insert_values = list(cat) + cat_dict[cat]
            ret = db.insert_values(table_name=table_name, insert_columns=columns, values=insert_values)
            print(f"Insertion result for {cat}: {ret}")
            
    elif data_type == "major":
        print("Inserting major category data...")
        db.delete_table_data(table_name=table_name)
        
        extracted_data = []
        for key, value in cat_dict.items():
            data = [value["pg_key", value["id"]]]
            
            ret = db.insert_values(table_name=table_name, insert_columns=columns, values=data)
            print(f"Insertion result for {cat}: {ret}") 

    elif data_type == 'search_theme':
        print("Inserting search theme data...")
        # db.delete_table_data(table_name=theme_table_name)
        # db.delete_table_data(table_name=keywords_table_name)
    
        ## 검색 테마 카테고리 삽입
        
        ### 검색 테마 데이터 리스트로 모으기
        category_lists = []
        for lang in cat_dict:
            theme_names = list(cat_dict[lang].keys())
            category_lists.append(theme_names)

        ### 각 언어별로 테마 데이터 리스트로 정리
        inserting_theme_data = []
        for idx in range(len(category_lists[0])):
            data_insert = [x[idx] for x in category_lists]
            inserting_theme_data.append(data_insert)
        
        ### 검색 테마 데이터 삽입 (한글, 영어, 중국어, 일본어)
        
        for data in inserting_theme_data:
            ret = db.insert_values(table_name=theme_table_name, insert_columns= theme_columns, values=data)
            print(f"Insertion result for {data}: {ret}")
        
        ## 검색 메타 키워드 삽입
        
        ### 검색 키워드 데이터 딕셔너리로 모으기
        keywords_dict = {}
        for lang in cat_dict:
            # print(f'{lang}: {list(cat_dict[lang].values())}'
            keywords_dict[lang] = list(cat_dict[lang].values())
        # print(f'debug {keywords_dict}')
        
        ### 각 언어별 키워드 데이터 zip으로 for 구문 돌리기
        for ko, en, cn_zh, cn_tw, jp, cat in zip(*[keywords_dict[lang] for lang in keywords_dict], cat_dict["ko"].keys()):
            # print(f'ko: {ko}, en: {en}, cn_zh: {cn_zh}, cn_tw: {cn_tw}, jp: {jp}, cat: {cat}')
            for idx in range(len(ko)):
                theme_id = db.select_theme_id_by_theme_name(theme_name=cat)
                keyword_insert = [ko[idx], en[idx], cn_zh[idx], cn_tw[idx], jp[idx], theme_id]
                db.insert_values(table_name=keywords_table_name, insert_columns=keywords_columns, values=keyword_insert)
                print(f"Insertion result for {keyword_insert}: {ret}")

    
    print("Insertion of category data is done.")     


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_type", type=str)
    args = parser.parse_args()
    
    if args.data_type not in ["theme", "major", "search_theme"]:
        raise ValueError("data_type must be provided --> available parameter [major, theme, search_theme]")
    
    print(f"Data type: {args.data_type}")
    
    main(data_type=args.data_type)
         