import os, sys
import random
import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import numpy as np
from typing import List, Tuple, Dict, Optional
import json
import pandas as pd

# ... (이전 코드와 동일)

class create_pgvector:

    def __init__(self, db_config=db_config, index_param: int = 100):
        assert isinstance(db_config, dict), "db_config must be provided in dictionary type"
        self.db_config = db_config
        self.index_param = index_param
        self.engine = None
        self.Session = None

        with open(upper_dir_path + "/data/language_table_info.json", "r") as f:
            self.language_dict = json.load(f)

    def connect(self):
        if self.engine is None:
            db_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
        else:
            print("Connection already exists")

    def disconnect(self):
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None
            self.Session = None
        else:
            print("Connection already closed")

    def run_queryset(self, sql):
        '''
        쿼리 실행
        sql문 입력
        '''
        self.connect()
        try:
            with self.Session() as session:
                result = session.execute(text(sql))
                if "DELETE" in sql.upper() or "INSERT" in sql.upper() or "UPDATE" in sql.upper() or "DROP" in sql.upper():
                    session.commit()
                    if "RETURNING" in sql.upper():
                        return result.fetchall()
                    return True
                return result.fetchall()
        except Exception as e:
            session.rollback()
            print(f"An error occurred: {e}")
            print(sql)
            return False
        finally:
            self.disconnect()

    def create_vector_table(self, table_name: str = "meta_embeddings_table", columns: List[Tuple[str, str]] = None, index_setting: bool = False):
        # ... (이전 코드와 동일)

    def update_values(self, table_name: str, update_columns: List[str] = None, update_values: List[str] = None, condition_columns: List[str] = None, condition_values: List[str] = None):
        update_columns_name = ", ".join([f"{col_name} = :{col_name}" for col_name in update_columns])
        condition_columns_name = " AND ".join([f"{col_name} = :{col_name}_cond" for col_name in condition_columns])

        update_query = f"UPDATE {table_name} SET {update_columns_name} WHERE {condition_columns_name}"

        params = {f"{col}": val for col, val in zip(update_columns, update_values)}
        params.update({f"{col}_cond": val for col, val in zip(condition_columns, condition_values)})

        self.connect()
        try:
            with self.Session() as session:
                session.execute(text(update_query), params)
                session.commit()
                print(f"Update completed successfully for {update_columns[0]}: {update_values[0]}")
        except Exception as e:
            print("Error: Failed to update the table.")
            print(e)
            session.rollback()
        finally:
            self.disconnect()

    def insert_values(self, table_name: str, insert_columns: List[str] = None, values: List[str] = None):
        columns_name = ", ".join(insert_columns)
        formatted_string = ", ".join([f":{col}" for col in insert_columns])
        insert_query = f"INSERT INTO {table_name} ({columns_name}) VALUES ({formatted_string})"

        params = {col: val for col, val in zip(insert_columns, values)}

        self.connect()
        try:
            with self.Session() as session:
                session.execute(text(insert_query), params)
                session.commit()
                return True
        except Exception as e:
            print("Error: Failed to insert into the table.")
            print(insert_query)
            print(e)
            session.rollback()
            return False
        finally:
            self.disconnect()

    # ... (다른 메서드들도 비슷한 방식으로 수정)

    def select_all_busan_data(self, table_name='visit_busan_info', major_cat_id=None, place_id=None, df_format=False, place_ids=None):
        sql = f'''
        SELECT DISTINCT * FROM {table_name}
        '''

        conditions = []
        if major_cat_id is not None:
            conditions.append(f"major_cat_id = :major_cat_id")
        if place_id is not None:
            conditions.append(f"place_id = :place_id")
        if place_ids is not None:
            conditions.append(f"place_id in :place_ids")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += ";"

        params = {}
        if major_cat_id is not None:
            params['major_cat_id'] = major_cat_id
        if place_id is not None:
            params['place_id'] = place_id
        if place_ids is not None:
            params['place_ids'] = tuple(place_ids)

        self.connect()
        try:
            if df_format:
                return pd.read_sql(text(sql), self.engine.connect(), params=params)
            else:
                with self.Session() as session:
                    result = session.execute(text(sql), params)
                    return result.fetchall()
        finally:
            self.disconnect()

    # ... (나머지 메서드들도 비슷한 방식으로 수정)

if __name__ == '__main__':
    print("========connect to db========")
    db = create_pgvector()
    with open("./data/visit_busan_table_dict.json", "r") as f:
        table_dict = json.load(f)

    print(f'''table dict: {table_dict}''')

    sql = f'''select * from visit_busan_info;'''

    db.connect()
    df = pd.read_sql(text(sql), db.engine)
    db.disconnect()
    print(df.head())