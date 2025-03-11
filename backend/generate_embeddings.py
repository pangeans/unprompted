#!/usr/bin/env python3
"""
This script generates a JSON file per keyword containing a mapping of the top N nearest words (by cosine similarity) to their similarity scores.

Usage:
    python generate_embeddings.py [--num NUM] [--output_dir DIR] [--model MODEL] keyword1 keyword2 ...

Arguments:
    --num: Number of nearest words to include (default: 10000)
    --output_dir: Directory to save output JSON files (default: "../frontend/public")
    --model: spaCy model to use (default: "en_core_web_lg")
    keywords: List of keywords to generate embeddings for

Requires:
    - spaCy with an appropriate model (e.g., en_core_web_md or en_core_web_lg)
      Install with: python -m spacy download en_core_web_lg
"""
import sys
from typing import List
from utils import load_spacy_model, generate_nearest_words_optimized

def generate_embeddings(keywords: List[str], num: int) -> None:
    """
    Generate and save embeddings for the given keywords.
    
    Args:
        keywords: List of keywords to generate embeddings for
        num: Number of nearest words to include
    """
    # Load the spaCy model
    model_name = "en_core_web_lg"
    nlp = load_spacy_model(model_name)
    if nlp is None:
        print(f"Failed to load spaCy model '{model_name}'. Exiting.")
        sys.exit(1)
    
    # Compute nearest words for all keywords in one pass
    print(f"Generating embeddings for {len(keywords)} keywords: {', '.join(keywords)}")
    embeddings_results = generate_nearest_words_optimized(keywords, nlp, num)
    similarity_dict = {}
    # Save a JSON file per keyword
    for keyword in embeddings_results:
        # Convert list of tuples to dictionary
        similarity_data = {word: similarity for word, similarity in embeddings_results[keyword]}
        similarity_dict[keyword] = similarity_data
        
    return similarity_dict

def main():
    """Main entry point for the script."""
    similarity_dict = generate_embeddings(["onion", "test"], 5000)

if __name__ == '__main__':
    main()
