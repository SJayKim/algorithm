import os, sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from db.busan_db import busan_db
from pgvector.pgvector_busan import create_pgvector

mysql_db = busan_db()
pg_db = create_pgvector()

if __name__ == "__main__":
    
    print('''
    ======================================
            Film: "About Time" 
    ======================================

     Słowo kluczowe: Podróże w czasie
    Wektor osadzeń: 
    [ 0.12, -0.45,  0.34, -0.78,  0.22,  0.09, -0.13, ...,  0.15, -0.37 ]

     Słowo kluczowe: Miłość
    Wektor osadzeń: 
    [-0.25,  0.44, -0.31,  0.21,  0.58, -0.12,  0.04, ..., -0.41,  0.19 ]

     Słowo kluczowe: Rodzina
    Wektor osadzeń: 
    [ 0.32, -0.12,  0.67, -0.43,  0.29,  0.24, -0.17, ...,  0.41,  0.18 ]

     Słowo kluczowe: Małżeństwo
    Wektor osadzeń: 
    [-0.14,  0.37, -0.23,  0.56, -0.38,  0.11,  0.06, ...,  0.42, -0.19 ]

     Słowo kluczowe: Lekcje życia
    Wektor osadzeń: 
    [ 0.49, -0.28,  0.71, -0.35,  0.19,  0.03,  0.58, ..., -0.22,  0.67 ]

    ======================================
          ''')