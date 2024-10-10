import networkx as nx
from konlpy.tag import Okt

class TextRank:
    def __init__(self, window_size=2):
        self.tokenizer = Okt()
    
    def textrank(self, text, window_size, num_keywords=5):
        # 한국어 형태소 분석기 초기화

        # 텍스트를 형태소 단위로 토크나이징, 구(phrase) 추출
        words = self.tokenizer.phrases(text)

        graph = nx.Graph()
        
        # 그래프 구성
        total_words = len(words)
        for i in range(total_words - window_size + 1):
            window = words[i:i + window_size]
            for j in range(window_size):
                for k in range(j + 1, window_size):
                    if window[j] != window[k]:
                        # 거리에 반비례하는 가중치 부여
                        distance = abs(j - k)
                        weight = 2 / distance  # 거리가 멀수록 가중치 감소
                        graph.add_edge(window[j], window[k], weight=weight)

        # PageRank 알고리즘을 이용한 중요도 계산, 가중치 반영
        scores = nx.pagerank(graph, weight='weight')

        # 가장 높은 점수를 가진 키워드 추출
        ranked_words = sorted(scores, key=scores.get, reverse=True)

        return ranked_words[:num_keywords]


if __name__ == "__main__":
    rank_model = TextRank()
    print("model loaded..")