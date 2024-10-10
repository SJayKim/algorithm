import mysql
import mysql.connector
import os
import json
import pandas as pd
from typing import List, Tuple, Dict, Optional

current_file_path = os.path.abspath(__file__)  
upper_dir_path = os.path.dirname(os.path.dirname(current_file_path))

db_config = {
    'host': '192.168.0.6',    # 데이터베이스 서버 주소
    'port': '3306',           # 데이터베이스 포트 번호
    'user':'o2oai',           # 데이터베이스 사용자 이름
    'password':'O2oai123!',    # 사용자 비밀번호
    'database':'ubismarttour_db'  # 데이터베이스 이름
}

class busan_db:
    def __init__(self):
        self.db_config = db_config
        self.conn = None
        
        self.month_mapping = {
            1: {"ko": "1월", "en": "January", "cn_zh": "1月", "cn_tw": "1月", "jp": "1月"},
            2: {"ko": "2월", "en": "February", "cn_zh": "2月", "cn_tw": "2月", "jp": "2月"},
            3: {"ko": "3월", "en": "March", "cn_zh": "3月", "cn_tw": "3月", "jp": "3月"},
            4: {"ko": "4월", "en": "April", "cn_zh": "4月", "cn_tw": "4月", "jp": "4月"},
            5: {"ko": "5월", "en": "May", "cn_zh": "5月", "cn_tw": "5月", "jp": "5月"},
            6: {"ko": "6월", "en": "June", "cn_zh": "6月", "cn_tw": "6月", "jp": "6月"},
            7: {"ko": "7월", "en": "July", "cn_zh": "7月", "cn_tw": "7月", "jp": "7月"},
            8: {"ko": "8월", "en": "August", "cn_zh": "8月", "cn_tw": "8月", "jp": "8月"},
            9: {"ko": "9월", "en": "September", "cn_zh": "9月", "cn_tw": "9月", "jp": "9月"},
            10: {"ko": "10월", "en": "October", "cn_zh": "10月", "cn_tw": "10月", "jp": "10月"},
            11: {"ko": "11월", "en": "November", "cn_zh": "11月", "cn_tw": "11月", "jp": "11月"},
            12: {"ko": "12월", "en": "December", "cn_zh": "12月", "cn_tw": "12月", "jp": "12月"}
        }
        
        with open(f'{upper_dir_path}/data/language_table_info.json', 'r') as f:
            self.lang_info = json.load(f)
            
    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            return True
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL Platform: {e}")
            return False
        
    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            # print("Disconnected from the database")

    def run_queryset(self, sql):
        if not self.connect():
            return False

        try:
            cur = self.conn.cursor()
            cur.execute(sql)

            if any(word in sql.upper() for word in ["DELETE", "INSERT", "UPDATE", "DROP"]):
                self.conn.commit()
                return True

            val = cur.fetchall()
            self.conn.commit()
            return val

        except Exception as e:
            print(f"An error occurred: {e}")
            print(f"Failed SQL: {sql}")
            self.conn.rollback()
            return False

        finally:
            self.disconnect()

    def show_all_tables(self):
        sql = '''SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'ubismarttour_db';
            '''
        
        try:
            print("show_all_tables for the database")
            if not self.connect():
                return False

            dataframe = pd.read_sql(sql, self.conn)
            print(dataframe)
            return dataframe
        
        except:
            print("Error in show_all_tables")
            return False

        finally:
            self.disconnect()

    def select_as_dataframe(self, table_name):
        sql = f"SELECT * FROM {table_name};"
        
        try:
            print("select_as_dataframe")
            if not self.connect():
                return False

            dataframe = pd.read_sql(sql, self.conn)
            return dataframe
        
        except:
            print("Error in select_as_dataframe")
            print("Failed SQL: ", sql)
            return False

        finally:
            self.disconnect()

    def select_gugun_place_ids(self, gugun_ids, lang="ko"):
        if lang not in list(self.lang_info.keys()):
            raise ValueError("Invalid language")
        
        union_query = f" UNION ".join([f"SELECT * FROM {table}" for table in self.lang_info[lang]["busan_vector_table"]])
        sql = f'''select UC_SEQ from ({union_query}) as combined_table
        WHERE UCG_SEQ in ({",".join([str(x) for x in gugun_ids])})
        '''
        
        ret = self.run_queryset(sql)
        ret = [x[0] for x in ret]
        return ret

    def select_place_id_from_table(self, table_name):
        sql = f"SELECT DISTINCT UC_SEQ FROM {table_name}"
        ret = self.run_queryset(sql)
        return ret

    def select_place_info(self, place_id=None, lang="ko", df=False):
        if lang not in list(self.lang_info.keys()):
            raise ValueError("Invalid language")
            
        union_query = " UNION ".join([f"SELECT * FROM {table}" for table in self.lang_info[lang]["busan_table"]])
        sql = f'''select * from ({union_query}) as combined_table
        '''     
        
        if place_id:
            sql += f" WHERE UC_SEQ = {place_id}"
        
        if df:
            if not self.connect():
                print("Failed to connect to the database")
                return False

            ret = pd.read_sql(sql, self.conn)
            return ret
        
        ret = self.run_queryset(sql)
        return ret

    def select_schedule_place_info(self, place_id=None, lang="ko"):
        if lang not in list(self.lang_info.keys()):
            raise ValueError("Invalid language")
            
        union_query = " UNION ".join([f"SELECT * FROM {table}" for table in self.lang_info[lang]["busan_table"]])
        sql = f'''select MENU_CD, MAIN_TITLE, GUGUN_NM, LAT, LNG, MAIN_IMG_NORMAL, MAIN_IMG_THUMB from ({union_query}) as combined_table
        '''
        
        if place_id:
            sql += f" WHERE UC_SEQ = {place_id}"
        
        sql += ";"

        ret = self.run_queryset(sql)
        return ret[0]
    
    def select_search_place_info(self, place_id=None, lang="ko"):
        if lang not in list(self.lang_info.keys()):
            raise ValueError("Invalid language")
            
        union_query = " UNION ".join([f"SELECT * FROM {table}" for table in self.lang_info[lang]["busan_table"]])
        sql = f'''
        SELECT MENU_CD, TITLE, SUBTITLE, PLACE, LANG_CD, CATE1_NM, GUGUN_SEQ, GUGUN_NM, MAIN_IMG_NORMAL, MAIN_IMG_THUMB 
        FROM ({union_query}) as combined_table
        WHERE UC_SEQ = {place_id};
        '''
        ret = self.run_queryset(sql)
        return ret[0]

    def select_place_image(self, place_id=None, lang="ko"):
        if lang not in list(self.lang_info.keys()):
            raise ValueError("Invalid language")
            
        union_query = " UNION ".join([f"SELECT * FROM {table}" for table in self.lang_info[lang]["busan_table"]])
        sql = f'''SELECT MAIN_IMG_NORMAL, MAIN_IMG_THUMB FROM ({union_query}) as combined_table
        '''
    
        if place_id:
            sql += f" WHERE UC_SEQ = {place_id}"
        sql += ";"
        
        ret = self.run_queryset(sql)
        return ret[0]
    
    def select_month_festival_info(self, month: int = None, lang: str = None):
        assert month in range(1, 13), "Invalid month"
        assert lang in list(self.lang_info.keys()), "Invalid language"
        
        sql = f'''select * from {list(self.lang_info[lang]["busan_table"])[4]} where cate2_nm = '{self.month_mapping[month][lang]}' order by MAIN_TITLE ASC
        '''
        
        ret = self.run_queryset(sql)
        
        return ret

if __name__ == "__main__":
    db = busan_db()
    
    # place_info = db.select_place_info(place_id=255, lang="ko")
    place_info = db.select_search_place_info(place_id=255, lang="cn_zh")
    
    print(place_info)
    
    # db.show_all_tables()
