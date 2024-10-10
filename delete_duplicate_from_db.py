
import json 
from pgvector.pgvector_busan import create_pgvector


def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        print("error occured in loading json file, check the file path")
        exit()

def init_db():
    return create_pgvector()

def main():
    pg_db = init_db()
    
    file_path = "data/creating_table_dict.json"
    table_data = load_json(file_path)
    
    for table, columns in table_data.items():
        column_names = [column[0] for column in columns if not column[0].lower().startswith("foreign key")]
        
        ret = pg_db.remove_duplicates(table, column_names)
        
        print(f"Table {table} data deleted result: {ret}")
        
        
    
    return

if __name__ == "__main__":
    main()
    