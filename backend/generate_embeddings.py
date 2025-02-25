#!/usr/bin/env python3
"""
This script generates a JSON file per keyword containing a mapping of the top N nearest words (by cosine similarity) to their similarity scores.

Usage:
    python generate_embeddings.py --num <number> keyword1 keyword2 ...

Requires:
    - spaCy (make sure to install a medium or larger English model, e.g., en_core_web_md or en_core_web_lg)
       Run: python -m spacy download en_core_web_lg

For each keyword, the script:
    1. Loads the spaCy model and obtains the keyword's vector.
    2. Iterates over the full vocabulary's vector table only once to compute cosine similarity between each candidate word and all keywords.
    3. Filters candidates to include only lowercase alphabetic tokens with vectors.
    4. Selects the top N most similar words for each keyword and saves a JSON file named '<keyword>.json', mapping each nearest word to its similarity score.

Note: Computing similarity over the entire vocab can be time consuming.
"""

import sys
import json
import spacy
import argparse
import numpy as np


def generate_nearest_words_optimized(keywords, nlp, top_n):
    """
    Optimized function that computes the nearest words for multiple keywords in one pass through the vocabulary vectors.
    Returns a dict mapping each keyword to a list of tuples (word, similarity).
    """
    # Precompute keyword vectors and their norms
    keyword_vectors = {}
    keyword_norms = {}
    results = {kw: [(kw, 1.0)] for kw in keywords}
    for kw in keywords:
        doc = nlp(kw)
        if not doc or not doc[0].has_vector:
            continue
        vec = doc[0].vector
        norm = np.linalg.norm(vec)
        if norm == 0:
            continue
        keyword_vectors[kw] = vec
        keyword_norms[kw] = norm

    # Iterate over all keys in the model's full vector table once
    for key in nlp.vocab.vectors.keys():
        word_text = nlp.vocab.strings[key]
        token = nlp.vocab[word_text]
        # Filter candidates: must have vector, be lowercase, and alphabetic
        if not (token.has_vector and token.is_lower and token.is_alpha):
            continue
        candidate_vec = token.vector
        candidate_norm = np.linalg.norm(candidate_vec)
        if candidate_norm == 0:
            continue
        # Compute similarity for each keyword
        for kw, kw_vec in keyword_vectors.items():
            # Skip if token text is the same as the keyword
            if token.text == kw:
                continue
            similarity = float(np.dot(kw_vec, candidate_vec) / (keyword_norms[kw] * candidate_norm))
            results[kw].append((token.text, similarity))

    # For each keyword, sort candidates and select top_n
    for kw in results:
        results[kw] = sorted(results[kw], key=lambda x: x[1], reverse=True)[:top_n]

    return results


def main():
    num = 10000
    keywords = [
        "pizza", "wings", "spicy", "milkshake", "caviar",
        "guide", "harvest", "fry", "egg", "cookbook",
        "onion", "elderly", "knitting", "Jesus", "desert",
        "distressed", "woodcarver", "sculpting", "wooden", "engine"
    ]

    # Load the spaCy model (this may take a few seconds)
    nlp = spacy.load('en_core_web_lg')

    # Compute nearest words for all keywords in one pass
    optimized_results = generate_nearest_words_optimized(keywords, nlp, num)

    # Save a JSON file per keyword
    for kw in optimized_results:
        data = {word: similarity for word, similarity in optimized_results[kw]}
        # Change output file path to place JSON files in the frontend public folder and use lowercase filenames
        const_output_file = f"../frontend/public/{kw.lower()}.json"
        with open(const_output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Saved nearest words for '{kw}' with {len(optimized_results[kw])} entries to {const_output_file}")

if __name__ == '__main__':
    main()
