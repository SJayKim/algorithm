import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from konlpy.tag import Mecab
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.manifold import TSNE
import seaborn as sns
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os, sys
sys.path.append("../")

from db.busan_db import busan_db

# 텍스트 정리 함수
def clean_text(text):
    text = text.replace(".", "").strip()
    text = text.replace("·", " ").strip()
    pattern = '[^ ㄱ-ㅣ가-힣|0-9]+'
    text = re.sub(pattern=pattern, repl='', string=text)
    return text

# 텍스트 전처리 함수
def preprocess(text: str):
    if type(text) == str:
        text = text.replace(".", "").strip()
        text = text.replace("·", " ").strip()
        pattern = '[^ ㄱ-ㅣ가-힣|0-9]+'
        text = re.sub(pattern=pattern, repl='', string=text)
        
        # 형태소 분석 및 토크나이징
        tagged = tokenizer.pos(text)
        nouns = [s for s, t in tagged if t in ['NNG', 'NNP', 'XR'] and len(s) > 1]
        return ' '.join(nouns)
    else:
        return ""

# 토픽 출력 함수
def print_topics(lda, top_n=10):
    words = vectorizer.get_feature_names_out()
    for idx, topic in enumerate(lda.components_):
        print(f"Topic {idx}:")
        print(" ".join([words[i] for i in topic.argsort()[:-top_n - 1:-1]]))

# 토픽 시각화 함수
def plot_topics(lda, n_top_words=10):
    words = vectorizer.get_feature_names_out()
    for topic_idx, topic in enumerate(lda.components_):
        print(f"Topic {topic_idx}:")
        top_features_ind = topic.argsort()[:-n_top_words - 1:-1]
        top_features = [words[i] for i in top_features_ind]
        top_weights = topic[top_features_ind]
        
        plt.figure(figsize=(10, 5))
        plt.barh(top_features, top_weights, align='center')
        plt.xlabel('Weight')
        plt.title(f'Topics {topic_idx}')
        plt.gca().invert_yaxis()
        plt.show()

# t-SNE를 사용한 시각화 함수
def plot_tsne(lda, doc_term_matrix):
    lda_output = lda.transform(doc_term_matrix)
    tsne_model = TSNE(n_components=2, random_state=0)
    tsne_lda = tsne_model.fit_transform(lda_output)
    
    plt.figure(figsize=(10, 10))
    sns.scatterplot(x=tsne_lda[:, 0], y=tsne_lda[:, 1], hue=np.argmax(lda_output, axis=1), palette=sns.color_palette("hsv", lda.n_components))
    plt.title("t-SNE Clustering of Topics")
    plt.show()

if __name__ == "__main__":
    tokenizer = Mecab(dicpath='/usr/local/lib/mecab/dic/mecab-ko-dic')
    vectorizer = CountVectorizer(max_df=0.5, min_df=1)
    lda = LatentDirichletAllocation(n_components=10, random_state=0)
    db = busan_db()
    
    reviews = db.select_as_dataframe("ubi_cntnts_my_review")
    overviews = db.select_as_dataframe("vw_ubi_attraction_ko")
    
    grouped_df = reviews.groupby('UC_SEQ').agg({'MY_STORY': lambda x: ' '.join(str(s) for s in x)}).reset_index()
    documents = pd.merge(overviews, grouped_df, left_on='UC_SEQ', right_on='UC_SEQ', how='inner')
    
    processed_docs = [preprocess(doc) for doc in documents["MY_STORY"]] + [preprocess(doc) for doc in documents["ITEMCNTNTS"]]
    print(f'Length of processed docs: {len(processed_docs)}')
    
    doc_term_matrix = vectorizer.fit_transform(processed_docs)
    
    lda = LatentDirichletAllocation(random_state=0)
    
    print("Optimize model...")
    search_params = {
        'n_components': [5, 6, 7, 8],
        'learning_decay': [.5, .7, 0.9]
    }
    
    model = GridSearchCV(lda, param_grid=search_params)
    model.fit(doc_term_matrix)
    
    
    best_lda_model = model.best_estimator_

    print("Best Model's Params: ", model.best_params_)
    print("Best Log Likelihood Score: ", model.best_score_)
    print("Model Perplexity: ", best_lda_model.perplexity(doc_term_matrix))

    feature_names = vectorizer.get_feature_names_out()

    ## 각 토픽별 키워드 출력
    print_topics(best_lda_model, 30)
    
    ## 각 토픽별 키워드 시각화
    plot_topics(best_lda_model, 10)
    
    ## 그래프상 클러스터링 시각화 TSNE
    plot_tsne(best_lda_model, doc_term_matrix)
    