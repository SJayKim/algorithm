import os, sys
import random
import re

import psycopg2
import numpy as np
from typing import List, Tuple, Dict, Optional
import json
import pandas as pd

# 상위 폴더의 절대 경로를 얻습니다
current_file_path = os.path.abspath(__file__)  
upper_dir_path = os.path.dirname(os.path.dirname(current_file_path))

with open(upper_dir_path + "/data/major_category.json", "r") as f:
    major_cat_dict = json.load(f)
    
with open(upper_dir_path + "/data/theme_category.json", "r") as f:
    theme_category = json.load(f)

db_config = {
    'host': 'local_host',
    'database': 'my_db',
    'user': 'postgres',
    'password': 'planty123net!',
    'port': '5432'
}

class create_pgvector:

    def __init__(self, db_config=db_config, index_param: int = 100):
        assert isinstance(db_config, dict), "db_config must be provided in dictionary type"
        self.db_config = db_config
        self.index_param = index_param
        self.conn = None  # 초기 연결을 설정하지 않음

        with open(upper_dir_path + "/data/language_table_info.json", "r") as f:
            self.language_dict = json.load(f)

    def connect(self):
        if self.conn is None:
            self.conn = psycopg2.connect(**self.db_config)
            # print("Connected to the PostgreSQL database successfully")

    def disconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            # print("Connection closed successfully.")

    def run_queryset(self, sql):
        '''
        쿼리 실행
        sql문 입력
        '''
        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                self.conn.commit()

                if "DELETE" in sql.upper() or "INSERT" in sql.upper() or "UPDATE" in sql.upper() or "DROP" in sql.upper():
                    if "RETURNING" in sql.upper():
                        return cur.fetchall()
                    return True

                return cur.fetchall()

        except Exception as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")
            print(sql)
            return False
        finally:
            self.disconnect()

    def create_vector_table(self, table_name: str = "meta_embeddings_table", columns: List[Tuple[str, str]] = None, index_setting: bool = False):
        table_info = {
            "table_name": table_name,
            "columns": columns,
            "index_setting": index_setting
        }

        columns_name_type = ", ".join([f"{col_name} {col_type}" for col_name, col_type in columns])

        vector_column_name = next((col_name for col_name, col_type in columns if "embedding" in col_name), None)

        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {columns_name_type}
                    );
                """)

                if index_setting and vector_column_name:
                    cur.execute(f"""
                       CREATE INDEX ON {table_name} USING ivfflat ({vector_column_name} vector_cosine_ops) WITH (lists = 200);
                    """)
                    cur.execute(f"SET ivfflat.probes = {self.index_param};")
                    print("Index created successfully")

                self.conn.commit()
                print(f"Table created successfully with vector type embeddings \nIndex Setting: {index_setting}")

        except psycopg2.Error as e:
            print("Error: Failed to create the table.")
            print(e)
            self.conn.rollback()
        finally:
            self.disconnect()

    def update_values(self, table_name: str, update_columns: List[str] = None, update_values: List[str] = None, condition_columns: List[str] = None, condition_values: List[str] = None):
        update_columns_name = ", ".join([f"{col_name} = %s" for col_name in update_columns])
        condition_columns_name = ", ".join([f"{col_name} = %s" for col_name in condition_columns])

        update_query = f"UPDATE {table_name} SET {update_columns_name} WHERE {condition_columns_name};"

        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute(update_query, update_values + condition_values)
                self.conn.commit()
                print(f"Update completed successfully for {update_columns[0]}: {update_values[0]}")

        except psycopg2.Error as e:
            print("Error: Failed to update the table.")
            print(e)
            self.conn.rollback()
        finally:
            self.disconnect()

    def insert_values(self, table_name: str, insert_columns: List[str] = None, values: List[str] = None):
        columns_name = ", ".join(insert_columns)
        formatted_string = ", ".join(["%s"] * len(insert_columns))
        insert_query = f"INSERT INTO {table_name} ({columns_name}) VALUES ({formatted_string});"

        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, values)
                self.conn.commit()
                return True

        except psycopg2.Error as e:
            print("Error: Failed to insert into the table.")
            print(insert_query)
            print(e)
            self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def delete_place_ids_from_table(self, table_name, place_id_list: List[int]):
        id_name = "place_id"
        if "restaurant" in table_name:
            id_name = "restaurant_id"

        sql = f'''DELETE FROM {table_name} WHERE {id_name} in ({','.join([str(x) for x in place_id_list])});'''

        return self.run_queryset(sql)

    def delete_table_data(self, table_name):
        sql = f'''DELETE FROM {table_name};'''

        return self.run_queryset(sql)

    def is_table_exist(self, table_name):
        sql = f'''
        SELECT EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename = '{table_name}');
        '''
        result = self.run_queryset(sql)
        return result[0][0] if result else False

    def drop_table(self, table_name):
        sql = f'''DROP TABLE {table_name};'''

        return self.run_queryset(sql)

    def get_naver_url(self, place_id):
        sql = f'''SELECT description from visit_busan_info WHERE place_id = {place_id};'''
        result = self.run_queryset(sql)

        if result:
            return result[0][0]
        else:
            return None

    def select_theme_id_by_theme_name(self, theme_name):
        sql = f'''SELECT theme_cat_id FROM search_theme_category WHERE theme_cat_ko = '{theme_name}';'''
        result = self.run_queryset(sql)
        return result[0][0] if result else None

    def select_place_id_from_table(self, table_name):
        sql = f'''SELECT DISTINCT place_id FROM {table_name};'''

        if "tour_restaurant_distance" in table_name:
            sql = f'''SELECT DISTINCT restaurant_id FROM {table_name};'''

        return self.run_queryset(sql)

    def select_place_id_list(self, major_cat=None):
        sql = f'''SELECT DISTINCT place_id FROM visit_busan_info'''

        if major_cat:
            sql += f" WHERE major_cat_id = {major_cat};"

        return self.run_queryset(sql)

    def select_all_busan_data(self, table_name='visit_busan_info', major_cat_id=None, place_id=None, df_format=False, place_ids=None):
        sql = f'''
        SELECT DISTINCT * FROM {table_name}
        '''

        conditions = []
        if major_cat_id is not None:
            conditions.append(f"major_cat_id = {major_cat_id}")
        if place_id is not None:
            conditions.append(f"place_id = {place_id}")
        if place_ids is not None:
            conditions.append(f"place_id in ({','.join([str(x) for x in place_ids])})")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += ";"

        self.connect()
        try:
            if df_format:
                return pd.read_sql(sql, self.conn)
            else:
                return self.run_queryset(sql)
        finally:
            self.disconnect()

    def select_all_restaurant_data_by_place_id(self, place_id, distance=5, top_k=5, cat=None, lang=None):
        sql = f'''SELECT DISTINCT * FROM {self.language_dict[lang]["pg_restaurant_table"]}'''

        conditions = []
        if place_id:
            conditions.append(f"tour_place_id = {place_id}")
        if distance:
            conditions.append(f"distance <= {distance}")

        category = list(self.language_dict[lang]["keyword_mapping"].values())[-1]

        if cat == "카페":
            condition = f'''cat in ({','.join([f"'{x}'" for x in category])})'''
            conditions.append(condition)
        elif cat == "식당":
            condition = f'''cat not in ({','.join([f"'{x}'" for x in category])})'''
            conditions.append(condition)
        else:
            raise ValueError("cat 변수는 '카페' 또는 '식당'이어야 합니다.")

        sql += " WHERE " + " AND ".join(conditions)
        sql += f" ORDER BY distance ASC"

        if top_k:
            sql += f" LIMIT {top_k}"

        ret = self.run_queryset(sql)
        return ret

    def check_keywords_and_insert(self, keyword):
        sql = f'''SELECT meta_id FROM meta_info WHERE meta_name = '{keyword}'
        '''
        result = self.run_queryset(sql)
        if result:
            return result[0][0]
        else:
            insert_sql = f'''INSERT INTO meta_info(meta_name) VALUES ('{keyword}') RETURNING meta_id;'''
            result = self.run_queryset(insert_sql)
            print(insert_sql)
            return result[0]

    def remove_duplicates(self, table_name, columns):
        partition_by_columns = ', '.join(columns)

        delete_query = f"""
        DELETE FROM {table_name}
        WHERE ctid IN (
            SELECT ctid FROM (
                SELECT ctid, ROW_NUMBER() OVER (PARTITION BY {partition_by_columns} ORDER BY ctid) as rnum
                FROM {table_name}
            ) t WHERE t.rnum > 1
        );
        """

        ret = self.run_queryset(delete_query)
        return ret

    def select_all_keyword_by_placeid(self, place_id):
        sql = f'''SELECT mi.meta_name
            FROM tour_place_meta tpm
            JOIN meta_info mi ON tpm.meta_id = mi.meta_id
            WHERE tpm.place_id = {place_id};
            '''
        result = self.run_queryset(sql)

        if result:
            result = [x[0] for x in result]
            return result
        else:
            return []

    def select_all_review_by_placeid(self, place_id):
        sql = f'''SELECT r.review
            FROM user_review r
            JOIN visit_busan_info v ON r.place_id = v.place_id
            WHERE r.place_id = {place_id};
            '''
        result = self.run_queryset(sql)
        if result:
            result = [x[0] for x in result]
            return result
        else:
            return []

    def select_vector_data_by_placeid(self, place_id):
        keywords = self.select_all_keyword_by_placeid(place_id=place_id)
        reviews = self.select_all_review_by_placeid(place_id=place_id)
        place_info = self.select_all_busan_data(place_id=place_id)
        if place_info:
            hash_tags = place_info[0][8] or ""
            overview = place_info[0][9] or ""

        output_data = {
            "keywords": ' '.join(keywords),
            "hash_tags": self.process_hash_tags(hash_tags),
            "overview": overview,
            "reviews": ' '.join(reviews)
        }

        return output_data

    def search_by_meta(self, keywords_vector: List[float] = None, theme_vector: List[float] = None, top_k: int = None, lang: str = "ko", gugun_list: List[int] = None):
        if lang not in self.language_dict:
            raise ValueError("Invalid language, please choose one of the following: ko, cn_zh, cn_tw, jp, en")

        sql = f'''
        WITH theme_similarities AS (
            SELECT                          
                place_id,
                GREATEST(
                    CASE WHEN meta_vector IS NOT NULL THEN 1 - (meta_vector <=> %s) ELSE -1 END,
                    CASE WHEN overview_vector IS NOT NULL THEN 1 - (overview_vector <=> %s) ELSE -1 END,
                    CASE WHEN review_vector IS NOT NULL THEN 1 - (review_vector <=> %s) ELSE -1 END
                ) AS max_similarity
            FROM {self.language_dict[lang]["pg_vector_table"]}
        ),
        top_candidates AS (
            SELECT
                place_id,
                max_similarity
            FROM theme_similarities
            WHERE max_similarity >= 0
            ORDER BY max_similarity DESC
        ),
        meta_similarities AS (
            SELECT
                tc.place_id,
                GREATEST(
                    CASE WHEN tbl.meta_vector IS NOT NULL THEN 1 - (tbl.meta_vector <=> %s) ELSE -1 END,
                    CASE WHEN tbl.overview_vector IS NOT NULL THEN 1 - (tbl.overview_vector <=> %s) ELSE -1 END,
                    CASE WHEN tbl.review_vector IS NOT NULL THEN 1 - (tbl.review_vector <=> %s) ELSE -1 END
                ) AS max_meta_similarity
            FROM top_candidates tc
            JOIN {self.language_dict[lang]["pg_vector_table"]} tbl ON tc.place_id = tbl.place_id
        )
        SELECT DISTINCT
            place_id,
            max_meta_similarity AS distance
        FROM meta_similarities
        WHERE max_meta_similarity >= 0
        '''

        if gugun_list:
            gugun_ids = ', '.join(map(str, gugun_list))
            sql += f' AND place_id IN ({gugun_ids})'

        sql += ' ORDER BY distance DESC'
        if top_k:
            sql += f' LIMIT {top_k}'

        query_params = [str(theme_vector)] * 3 + [str(keywords_vector)] * 3

        self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, query_params)
                result = cursor.fetchall()
                self.conn.commit()
                return result

        except psycopg2.Error as e:
            print("Error: Failed to search from the table.")
            print(e)
        finally:
            self.disconnect()

    def search_by_user_input(self, theme_ids: list, keywords_vector: List[float] = None, top_k: int = None, lang: str = "ko"):
        candidate_sql = f'''SELECT DISTINCT place_id FROM theme_tourist_spot WHERE theme_cat_id in ({','.join([str(x) for x in theme_ids])});'''

        candidates = [x[0] for x in self.run_queryset(candidate_sql)]

        if keywords_vector:
            curation_sql = f'''
            WITH vector_similarities AS (
                SELECT
                    place_id,
                    GREATEST(
                        CASE WHEN meta_vector IS NOT NULL THEN 1 - (meta_vector <=> %s) ELSE -1 END,
                        CASE WHEN overview_vector IS NOT NULL THEN 1 - (overview_vector <=> %s) ELSE -1 END,
                        CASE WHEN review_vector IS NOT NULL THEN 1 - (review_vector <=> %s) ELSE -1 END
                    ) AS max_similarity
                FROM {self.language_dict[lang]["pg_vector_table"]}
            )
            SELECT
                place_id,
                max_similarity AS distance
            FROM vector_similarities
            WHERE max_similarity >= 0
            AND place_id IN ({','.join([str(x) for x in candidates])})
            ORDER BY distance DESC
            '''

            if top_k:
                curation_sql += f" LIMIT {top_k};"

            self.connect()
            try:
                with self.conn.cursor() as cursor:
                    cursor.execute(curation_sql, [str(keywords_vector), str(keywords_vector), str(keywords_vector)])
                    result = cursor.fetchall()
                    self.conn.commit()
                    return result

            except psycopg2.Error as e:
                print("Error: Failed to search from the table.")
                print(e)
            finally:
                self.disconnect()
        else:
            if top_k and len(candidates) > top_k:
                result = random.sample(candidates, top_k)
            else:
                result = candidates

            return [(place_id, None) for place_id in result]

    def search_by_vector(self, vector: List[float] = None, top_k: int = None, lang="ko", gugun_list: List[int] = None):
        sql = f'''
        WITH vector_similarities AS (
            SELECT
                place_id,
                GREATEST(
                    CASE WHEN meta_vector IS NOT NULL THEN 1 - (meta_vector <=> %s) ELSE -1 END,
                    CASE WHEN overview_vector IS NOT NULL THEN 1 - (overview_vector <=> %s) ELSE -1 END,
                    CASE WHEN review_vector IS NOT NULL THEN 1 - (review_vector <=> %s) ELSE -1 END
                ) AS max_similarity
            FROM {self.language_dict[lang]["pg_vector_table"]}
        )
        SELECT DISTINCT
            place_id,
            max_similarity AS distance
        FROM vector_similarities
        WHERE max_similarity >= 0
        '''

        if gugun_list:
            gugun_ids = ', '.join(map(str, gugun_list))
            sql += f' AND place_id IN ({gugun_ids})'

        sql += ' ORDER BY distance DESC'
        if top_k:
            sql += f" LIMIT {top_k}"

        query_params = [str(vector)] * 3

        self.connect()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, query_params)
                result = cursor.fetchall()
                self.conn.commit()
                return result

        except psycopg2.Error as e:
            print("Error: Failed to search from the table.")
            print(e)
        finally:
            self.disconnect()

    def process_hash_tags(self, hash_tags):
        clean_string = re.sub(r'[#,]', ' ', hash_tags)
        result_string = ' '.join(clean_string.split())
        return result_string


if __name__ == '__main__':
    print("========connect to db========")
    db = create_pgvector()
    with open("./data/visit_busan_table_dict.json", "r") as f:
        table_dict = json.load(f)

    print(f'''table dict: {table_dict}''')

    sql = f'''select * from visit_busan_info;'''

    df = pd.read_sql(sql, db.conn)
    print(df.head())
