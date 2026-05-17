import os
import time
import json
from pathlib import Path
from itertools import combinations
os.environ["HF_HOME"] = "E:/huggingface"
os.environ["HUGGINGFACE_HUB_CACHE"] = "E:/huggingface/hub"
os.environ["TRANSFORMERS_CACHE"] = "E:/huggingface/transformers"

from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
model_name = "vinai/phobert-base"

phrases = [
    "người lao động",
    "người sử dụng lao động",

    "Bộ Công an",
    "cơ quan công an",
    'người lao động nữ',
    'lao động nữ',
    'lao động nước ngoài',
    'người đi làm',
]
tokenizer = AutoTokenizer.from_pretrained(model_name,cache_dir="E:/huggingface")
model = AutoModel.from_pretrained(model_name,cache_dir="E:/huggingface")


def embed(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)

    emb = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return emb


try:
   
    embeddings = {}

    for phrase in phrases:
        embeddings[phrase] = embed(phrase)

    rows = []

   
    for a, b in combinations(phrases, 2):

        sim = cosine_similarity(
            [embeddings[a]],
            [embeddings[b]]
        )[0][0]

        rows.append({
            "Entity A": a,
            "Entity B": b,
            "Similarity": round(float(sim), 4)
        })

    # Sort theo similarity giảm dần
    df = pd.DataFrame(rows)
    df = df.sort_values(
        by="Similarity",
        ascending=False
    )

    print("\nPhoBERT Similarity \n")
    print(df.to_string(index=False))

except Exception as e:
    print("Load model thất bại.")
    print(e)