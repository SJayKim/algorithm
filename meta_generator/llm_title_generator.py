import os, sys
import pandas as pd
# import streamlit as st
from openai import OpenAI
import argparse
import json
from pprint import pprint

## api key 설정
from dotenv import load_dotenv
import dotenv
import random

dotenv_file = dotenv.find_dotenv()
load_dotenv(dotenv_file)
openai_api_key = os.getenv("openai_api_key")
# print(openai_api_key)

class llm_title:

    ### db_config: dict type 데이터 베이스 연결정보
    ### num_probes: int type index 설정을 위한 probe 개수 --> 높을 수록 정확도는 높지만 속도는 느려짐
    def __init__(self, api_key=openai_api_key, model_name = "gpt-4o"):
        
        ## module parameter setting
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        
    def generate_title(self, keywords):
     
        system = '''
        You are a title generator based on keywords related to tour place in Busan.
        The task is to generate a title based on the given input Korean keywords.
        Output should be in Korean language.
        Output should be short one sentence less than 20 letters.
        
        Generate titles referring to the following output examples.
        '''
                
 

        output_example1 = "아이와 함께하는 부산 역사 소풍: 정거마을과 초량이바구길"
  
        output_example2 = "가족과 함께 부산: 안데르센 극장부터 유네스코 지질공원까지 체험 학습 여행"
        
        output_example3 = "자연과 문화가 어우러진 부산 유네스코 세계지질공원 산책 여행"

        output_example4 = "우정 여행: 송도 스카이워크부터 광안리 해변까지, 부산 인생샷 투어"
        
        
        
        
        
    
    ## input: 판교역 근처 도보 5분 이내 와이파이 잘 터지고 조식 제공 되고 체크아웃 느린 20만원 미만의 호텔  output: {output_example1}
                
    
        main_input = f"""
        Below are some examples. 
        You must consider korean input.

        output example1: {output_example1}
        
        output example2: {output_example2}
        
        output example3: {output_example3}
        
        output example4: {output_example4}
        
        Given keywords: {keywords}

        Generate a short Korean title for the travel schedule based on given keywords.
        Do not print any other text except the title.
        """
        
        prompt = [{
            "role": "system", "content": system,
            "role": "user", "content": main_input
        }]
        
        response = self.client.chat.completions.create(
            model = self.model_name,
            messages=prompt,
            temperature=0,
            top_p = 0
        ).model_dump()
        

        output = response["choices"][0]["message"]["content"]
        
        return output

        
        
if __name__ == '__main__':

    with open("/home/chatbot/visit_busan/algorithm/data/visit_busan_keywords/keywords.json", "r", encoding="utf-8") as f:
        keywords_data = json.load(f)

    o2o_api_key = "sk-proj-KdNd3XRyXakfiaE1vRJHT3BlbkFJLzjuJ7uqhRXtucDY2PEF"
    model_name = 'gpt-4o'
    
    
    result_df = {
        "keywords": [],
        "title": []
    }
    
    for i in range(100):
        random_selection = random.sample(keywords_data, 20)
        llm = llm_title(api_key=o2o_api_key, model_name=model_name)
        ret = llm.generate_title(keywords=random_selection)

        
        result_df["keywords"].append(random_selection)
        result_df["title"].append(ret)
        
        print(ret)
        print(f"{i}th done")
    
    result_df = pd.DataFrame(result_df)
    result_df.to_excel("/home/chatbot/visit_busan/algorithm/data/visit_busan_keywords/title_generation_result.xlsx", index=False, engine='openpyxl')
    
    # json_return = json.loads(ret)
    # pprint(json_return)

