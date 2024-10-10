import os, sys

# import streamlit as st
from openai import OpenAI
import argparse
import json
from pprint import pprint

## api key 설정
from dotenv import load_dotenv
import dotenv


dotenv_file = dotenv.find_dotenv()
load_dotenv(dotenv_file)
openai_api_key = os.getenv("openai_api_key")
# print(openai_api_key)

class llm_translator:

    ### db_config: dict type 데이터 베이스 연결정보
    ### num_probes: int type index 설정을 위한 probe 개수 --> 높을 수록 정확도는 높지만 속도는 느려짐
    def __init__(self, api_key=openai_api_key, model_name = "gpt-4o"):
        
        ## module parameter setting
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        
    def ner_query(self, input_query, target_lang):
        if target_lang not in ["simplified chinese", "traditional chinese", "japanese", "english"]:
            raise ValueError("target language must be one of ['simplified chinese', 'traditional chinese', 'japanese', 'english']")
        
        system = '''
        Act as a state-of-the-art model for translator
        The task is to translate the given input text.
        Input text is Korean which is a source language.
        Target language is simlified Chienese, traditional Chinese, and Japanese.
        Do not print any other text except the translated text.
        '''
                
        # 부산에서 만나는 튀르키예!
        output_example1 = "釜山遇见土耳其！土耳其伊斯坦布尔文化院",
                    
        
        # 강아지와 한께 할 수 있는 여행 반려견, 데이트코스, 힐링
        output_example2 = "可以和狗狗一起旅行，寵物犬，約會路線，治癒"    
                        
        
        # 튀르키예의 향기를 더욱 친하게 느끼고 싶다면 소규모로 진행되는 다양한 체험 프로그램에 참여하면 됩니다.
        output_example3 = "トルコの香りをより身近に感じたいなら、小規模で行われるさまざまな体験プログラムに参加すると良いでしょう"         
                        
        
        output_example4 = "海云台 芒草 海滩 广安里 树 美丽 冬天 广安 海水浴场 风景 凉爽 自然 大海 大桥 夏天 顶峰 散步 生态"
        
        output_example5 = "'Musai' is a name derived from the Muses in Greek mythology, the goddesses of art and science, and it means 'to ponder' in Greek. It perfectly matches the space Musai, which evokes thought through various profound books, movies, and art gatherings."
        
        
        
        
    
    ## input: 판교역 근처 도보 5분 이내 와이파이 잘 터지고 조식 제공 되고 체크아웃 느린 20만원 미만의 호텔  output: {output_example1}
                
    
        main_input = f"""
        Below are some examples. 
        You must consider korean input.

        input: "부산에서 만나는 튀르키예!" 
        target lang: simplified chinese
        output: {output_example1}
        
        input: "강아지와 한께 할 수 있는 여행 반려견, 데이트코스, 힐링"
        target lang: traditional chinese
        output: {output_example2}
        
        input: "튀르키예의 향기를 더욱 친하게 느끼고 싶다면 소규모로 진행되는 다양한 체험 프로그램에 참여하면 됩니다.
        target lang: japanese
        output: {output_example3}
        
        input: "해운대 억새 해변 광안리 나무 아름다운 겨울 광안 해수욕장 풍경 시원 자연 바다 대교 여름 정상 산책 생태"
        target lang: simplified chinese
        output: {output_example4}
        
        input: "‘무사이’는 그리스 신화에 나오는 예술과 학문의 여신, 무사이에서 따온 이름으로, 그리스어로 ‘생각에 잠기다’는 뜻을 가진다고 합니다. 여러 진중한 서적과 영화, 예술 모임으로 생각을 불러일으키는 공간 무사이와 잘 어울리죠."
        target lang: english
        output: {output_example5}
        
        input: {input_query}
        target lang: {target_lang}
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_query", type=str, required=True)
    parser.add_argument("--target_lang", type=str, required=True)
    args = parser.parse_args()
    
    print(args)
    
    


    o2o_api_key = "sk-proj-KdNd3XRyXakfiaE1vRJHT3BlbkFJLzjuJ7uqhRXtucDY2PEF"
    model_name = 'gpt-4o'
    llm = llm_translator(api_key=o2o_api_key, model_name=model_name)
    
    ret = llm.ner_query(input_query = args.input_query, target_lang = args.target_lang)

    # print(ret)
    
    print(ret, type(ret))
    
    # json_return = json.loads(ret)
    # pprint(json_return)

