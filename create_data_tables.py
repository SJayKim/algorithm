import os
import sys
import json
from pgvector.pgvector_busan import create_pgvector

# 현재 파일의 경로를 기준으로 pgvector 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

def load_table_dict(file_path):
    """JSON 파일에서 테이블 생성 정보를 로드."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} contains invalid JSON.")
        sys.exit(1)


def create_tables(db, table_dict):
    """테이블을 생성하는 함수."""
    for table_name, columns in table_dict.items():
        db.create_vector_table(table_name=table_name, columns=columns)
        print(f'Table created - Name: {table_name}, Columns: {columns}')


def main(json_file_path='./data/creating_table_dict.json'):
    db = create_pgvector()

    table_dict = load_table_dict(json_file_path)
    
    print(f'Table list to create: {list(table_dict.keys())}')
    
    create_tables(db, table_dict)


if __name__ == "__main__":
    # main()을 호출할 때 파일 경로를 전달할 수 있습니다.
    main()
