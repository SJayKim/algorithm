import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import re
from pgvector.pgvector_busan import create_pgvector

from dotenv import load_dotenv
import dotenv

import konlpy
from konlpy import tag
from konlpy.tag import Mecab


dotenv_file = dotenv.find_dotenv()
load_dotenv(dotenv_file)
openai_api_key = os.getenv("openai_api_key")
# print(openai_api_key)

current_file_path = os.path.abspath(__file__)  
upper_dir_path = os.path.dirname(os.path.dirname(current_file_path))


class embedding_model:
   
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        ## 관광지 테마 카테고리 정의 --> json 파일로 정리해놓은 것들을 불러와 활용 
 
        with open(upper_dir_path + "/data/theme_category.json", "r") as f:
            self.categories = json.load(f)

        self.model = SentenceTransformer(model_name)
        # self.category_embeddings = {category: self.get_chunked_embeddings(category + ' ' + ' '.join(keywords["키워드"])) for category, keywords in self.categories.items()}
        self.tokenizer = Mecab(dicpath = '/usr/local/lib/mecab/dic/mecab-ko-dic')
            

    # 텍스트를 128자 단위로 나누는 함수
    def _chunk_text_by_length(self, text, max_length=128, stride=128):
        chunks = [text[i:i+max_length] for i in range(0, len(text), stride)]
        return chunks

    # chunking 방식으로 긴 텍스트의 임베딩을 얻는 함수
    def get_chunked_embeddings(self, text, max_length=128, stride=128):
        chunks = self._chunk_text_by_length(text, max_length, stride)
        
        if chunks == []:
            return None
        
        embeddings = []
        for chunk in chunks:
            embedding = self.model.encode(chunk)
            embeddings.append(embedding)
        # 모든 chunk의 임베딩을 평균냄
        if len(embeddings) > 1:
            mean_embeddings = np.mean(embeddings, axis=0)
            return mean_embeddings.tolist()
        return embeddings[0].tolist()

    def process_hash_tags(self, hash_tags):

        # 특수 문자 제거 (해시태그와 쉼표)
        clean_string = re.sub(r'[#,]', ' ', hash_tags)
        # 단어들을 공백으로 구분하여 하나의 문자열로 변환
        result_string = ' '.join(clean_string.split())
        return result_string
    
    def preprocess(self, text: str):
        if type(text) == str:
            text = text.replace(".", "").strip()
            text = text.replace("·", " ").strip()
            pattern = '[^ ㄱ-ㅣ가-힣|0-9]+'
            text = re.sub(pattern=pattern, repl='', string=text)
            
            # 형태소 분석 및 토크나이징
            tagged = self.tokenizer.pos(text)
            nouns = [s for s, t in tagged if t in ['NNG', 'NNP', 'XR'] and len(s) > 1]
            ## 필요없는 키워드 제거
            nouns = [words for words in nouns if words not in ["부산", "니스", "홈페이지"]]
            
            return ' '.join(nouns)
        else:
            raise ValueError("Input text must be a string")
    
    # 유사도를 계산하고 카테고리를 분류하는 함수
    # def classify_tourist_spot_category(self, text):
    #     text_embedding = self.get_chunked_embeddings(text)
    #     similarities = {category: cosine_similarity([text_embedding], [embedding])[0][0] for category, embedding in self.category_embeddings.items()}
    #     sorted_categories = sorted(similarities.items(), key=lambda item: item[1], reverse=True)
    #     return sorted_categories

    ## 텍스트 전처리 함수
    

if __name__ == '__main__':
    db = create_pgvector()
    embedding = embedding_model()

    print("Getting data from busan.....")
    result = db.select_all_busan_data(major_cat_id = 1)
    print(f'sample data: {result[0]}')
    
    print("Classifying ..... ===========>")
    for sample in result:
        # print(sample[8] + " " + sample[9])
        processed_text = embedding.preprocess(sample[8] + " " + sample[9])
        # print(f'processed_text: {processed_text}')
        category_list = embedding.classify_tourist_spot_category(processed_text)
        
        print(f'place title: {sample[1]}\nplace hash tag: {sample[8]}\nplace description: {sample[9]}')
        print(f'classification result: {category_list}')
        print("=====================================")
    # # 긴 텍스트에 대한 임베딩 얻기
    # embedding_model = embedding_model()
    # embeddings = embedding_model.get_chunked_embeddings(sample_text)

    # # 임베딩 출력
    # print(embeddings)
    # print(len(embeddings))


