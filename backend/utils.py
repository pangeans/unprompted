#!/usr/bin/env python3
"""
Common utilities for the Unprompted game backend.
"""
import os
import json
import spacy
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

def load_spacy_model(model_name: str = "en_core_web_md") -> Optional[spacy.language.Language]:
    """
    Load a spaCy language model.
    
    Args:
        model_name: Name of the spaCy model to load.
    
    Returns:
        The loaded spaCy model or None if loading fails.
    """
    try:
        nlp = spacy.load(model_name)
        print(f"Loaded spaCy model: {model_name}")
        return nlp
    except Exception as e:
        print(f"Error loading spaCy model: {e}")
        print(f"Please install the model with: python -m spacy download {model_name}")
        return None

def generate_word_embedding(word: str, nlp: spacy.language.Language) -> Optional[np.ndarray]:
    """
    Generate word embedding for a keyword using spaCy.
    
    Args:
        word: The word to generate an embedding for.
        nlp: The loaded spaCy model.
        
    Returns:
        Word vector or None if no vector available.
    """
    doc = nlp(word)
    if not doc or not doc[0].has_vector:
        print(f"Warning: No vector found for word '{word}'")
        return None
    
    return doc[0].vector

def compute_similarity(word1_vec: np.ndarray, word2: str, nlp: spacy.language.Language) -> float:
    """
    Compute similarity between a vector and a word.
    
    Args:
        word1_vec: Vector for the first word.
        word2: Second word as a string.
        nlp: The loaded spaCy model.
    
    Returns:
        Cosine similarity score between 0 and 1.
    """
    if word1_vec is None:
        return 0.0
    
    doc2 = nlp(word2)
    if not doc2 or not doc2[0].has_vector:
        return 0.0
    
    word2_vec = doc2[0].vector
    
    # Compute cosine similarity
    similarity = np.dot(word1_vec, word2_vec) / (np.linalg.norm(word1_vec) * np.linalg.norm(word2_vec))
    return float(similarity)

def generate_embeddings_for_keyword(
    keyword: str, 
    nlp: spacy.language.Language, 
    top_n: int = 1000, 
    common_words_file: Optional[str] = None
) -> Dict[str, float]:
    """
    Generate embeddings for a keyword using spaCy.
    
    Args:
        keyword: The keyword to generate embeddings for.
        nlp: The loaded spaCy model.
        top_n: Number of top similar words to return.
        common_words_file: Optional path to a file containing common words.
    
    Returns:
        Dictionary mapping similar words to their similarity scores.
    """
    # Load common English words if file is provided
    common_words = []
    if common_words_file and os.path.exists(common_words_file):
        with open(common_words_file, 'r') as f:
            common_words = [line.strip().lower() for line in f]
    
    # Generate embedding for the keyword
    keyword_vec = generate_word_embedding(keyword, nlp)
    if keyword_vec is None:
        return {keyword: 1.0}  # Return only the keyword itself with perfect similarity
    
    # Start with the keyword itself having perfect similarity
    results = {keyword: 1.0}
    
    # If we have common words, use those
    if common_words:
        for word in common_words:
            if word == keyword:
                continue
            
            sim = compute_similarity(keyword_vec, word, nlp)
            if sim > 0.5:  # Only include reasonably similar words
                results[word] = sim
    else:
        # Use words from the vocabulary
        words = [w for w in nlp.vocab.strings if w.isalpha() and len(w) > 2]
        for word in words[:10000]:  # Limit to first 10000 words
            if word == keyword:
                continue
            
            sim = compute_similarity(keyword_vec, word, nlp)
            if sim > 0.5:  # Only include reasonably similar words
                results[word] = sim
    
    # Sort by similarity and keep top N
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_results[:top_n])

def generate_nearest_words_optimized(
    keywords: List[str], 
    nlp: spacy.language.Language, 
    top_n: int
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Optimized function that computes the nearest words for multiple keywords 
    in one pass through the vocabulary vectors.
    
    Args:
        keywords: List of keywords to generate embeddings for.
        nlp: The loaded spaCy model.
        top_n: Number of top similar words to return per keyword.
    
    Returns:
        Dictionary mapping each keyword to a list of (word, similarity) tuples.
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

def save_similarity_data(
    keyword: str, 
    similarity_data: Dict[str, float], 
    output_dir: str = "../frontend/public"
) -> str:
    """
    Save similarity data to a JSON file.
    
    Args:
        keyword: The keyword the similarity data is for.
        similarity_data: Dictionary mapping words to similarity scores.
        output_dir: Directory where to save the file.
        
    Returns:
        Path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{keyword.lower()}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(similarity_data, f, ensure_ascii=False, indent=4)
        
    return output_file

def load_json_data(file_path: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Loaded data or None if loading fails.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None