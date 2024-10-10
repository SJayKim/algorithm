import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
                
from meta_generator.llm_ner import llm_ner
from pgvector.pgvector_busan import create_pgvector

