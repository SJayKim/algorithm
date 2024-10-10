import pandas as pd
import numpy as np
from openai import OpenAI
import re

## api key 설정
import os
from dotenv import load_dotenv
import dotenv

import konlpy
from konlpy import tag
from konlpy.tag import Mecab


dotenv_file = dotenv.find_dotenv()
load_dotenv(dotenv_file)
openai_api_key = os.getenv("openai_api_key")

current_file_path = os.path.abspath(__file__)  
upper_dir_path = os.path.dirname(os.path.dirname(current_file_path))


class openai_embedding:
    def __init__(self, api_key = openai_api_key, model="text-embedding-3-large", max_tokens=8192):
        self.client = OpenAI(api_key = api_key)
        self.model = model
        self.max_tokens = max_tokens
        
        self.tokenizer = Mecab(dicpath = '/usr/local/lib/mecab/dic/mecab-ko-dic')
    
    def get_chunked_embeddings(self, text):
        embeddings = []
        
        # Split the text into chunks of 500 characters
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        
        for chunk in chunks:
            output_embedding = self.client.embeddings.create(input=[chunk], model=self.model, dimensions=500).data[0].embedding
            embeddings.append(output_embedding)
        
        # Calculate the average embedding
        avg_embedding = list(map(float, np.mean(embeddings, axis=0)))
        # print('avg_embedding', type(avg_embedding), avg_embedding[:50])
        return avg_embedding


    def process_hash_tags(self, hash_tags):

        # 특수 문자 제거 (해시태그와 쉼표)
        clean_string = re.sub(r'[#,]', ' ', hash_tags)
        # 단어들을 공백으로 구분하여 하나의 문자열로 변환
        result_string = ' '.join(clean_string.split())
        return result_string
    
    
    def preprocess(self, text):
        # Replace newlines with space
        text = text.replace("\n", " ")

        # Remove special characters but keep letters, numbers, spaces, and CJK characters
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', '', text)
        
        # Collapse multiple spaces into a single space
        text = re.sub(r'\s+', ' ', text)

        # Remove leading and trailing whitespace
        return text.strip()

    
    
if __name__ == "__main__":
    embedding = openai_embedding()
    
    text = "Hello, 世界! こんにちは! 这是一个例子文本。特殊字符：@#$%^&*()"
    
    processed = embedding.preprocess(text)
    
    print(processed)
