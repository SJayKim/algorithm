import pandas as pd
import numpy as np
from openai import OpenAI

## api key 설정
import os
from dotenv import load_dotenv
import dotenv



dotenv_file = dotenv.find_dotenv()
load_dotenv(dotenv_file)
openai_api_key = os.getenv("openai_api_key")
# print(openai_api_key)




# OpenAI 클라이언트 초기화
client = OpenAI(api_key = openai_api_key)



# 임베딩을 가져오는 함수, 텍스트가 긴 경우 분할 처리 포함
def get_embedding(text, model="text-embedding-3-small", max_tokens=8192):
    # 개행 문자 제거
    text = text.replace("\n", " ")
    # 토큰화하여 텍스트를 분할
    tokens = client.tokenizer.tokenize([text], model=model).data[0].tokens
    parts = [text[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    
    # 각 부분의 임베딩 계산
    embeddings = []
    for part in parts:
        response = client.embeddings.create(input=[part], model=model, dimensions=500)
        embeddings.append(response.data[0].embedding)
    
    # 평균 임베딩 벡터 계산
    avg_embedding = np.mean(embeddings, axis=0)
    return avg_embedding



if __name__ == "__main__":
    sample_text = '''
    부산의 대표적인 관광지인 해운대 해수욕장은 부산의 대표적인 관광지로 유명하다.
    '''
    
    sample_embedding = get_embedding(sample_text)
    
    print(len(sample_embedding), type(sample_embedding))
