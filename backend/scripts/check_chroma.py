import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.retriever import Retriever
from pipeline.vector_db import VectorDB

def check():
    vdb = VectorDB()
    count = vdb.get_collection().count()
    print(f"ChromaDB Collection Count: {count}")

if __name__ == "__main__":
    check()
