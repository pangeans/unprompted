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
import argparse
from typing import List
from utils import load_spacy_model, generate_nearest_words_optimized, save_similarity_data

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate word embeddings for keywords")
    parser.add_argument("--num", type=int, default=10000, help="Number of nearest words to include")
    parser.add_argument("--output_dir", type=str, default="../frontend/public", help="Directory to save output JSON files")
    parser.add_argument("--model", type=str, default="en_core_web_lg", help="spaCy model to use")
    parser.add_argument("keywords", nargs="*", default=["poster", "mall", "cop", "Segway", "Blart"], 
                        help="Keywords to generate embeddings for")
    return parser.parse_args()

def generate_embeddings(keywords: List[str], num: int, output_dir: str, model_name: str) -> None:
    """
    Generate and save embeddings for the given keywords.
    
    Args:
        keywords: List of keywords to generate embeddings for
        num: Number of nearest words to include
        output_dir: Directory to save output JSON files
        model_name: spaCy model to use
    """
    # Load the spaCy model
    nlp = load_spacy_model(model_name)
    if nlp is None:
        print(f"Failed to load spaCy model '{model_name}'. Exiting.")
        sys.exit(1)
    
    # Compute nearest words for all keywords in one pass
    print(f"Generating embeddings for {len(keywords)} keywords: {', '.join(keywords)}")
    embeddings_results = generate_nearest_words_optimized(keywords, nlp, num)
    
    # Save a JSON file per keyword
    for keyword in embeddings_results:
        # Convert list of tuples to dictionary
        similarity_data = {word: similarity for word, similarity in embeddings_results[keyword]}
        
        # Save to file
        output_file = save_similarity_data(keyword, similarity_data, output_dir)
        print(f"Saved nearest words for '{keyword}' with {len(similarity_data)} entries to {output_file}")

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    generate_embeddings(args.keywords, args.num, args.output_dir, args.model)

if __name__ == '__main__':
    main()
