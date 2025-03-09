#!/usr/bin/env python3
"""
Similarity data loader script for Unprompted game.

This script provides a dedicated function for loading word similarity data into Redis.
It can be used independently or imported by other modules.

Usage:
    # Load similarity data for a specific game
    python load_similarity_data.py --game-file random-0.json
    
    # Load similarity data for a specific keyword
    python load_similarity_data.py --keyword Giant
    
    # Load similarity data for all game files
    python load_similarity_data.py --all
    
    # Regenerate similarity data even if it exists
    python load_similarity_data.py --all --regenerate
"""
import os
import argparse
import redis
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Set

from utils import (
    load_spacy_model,
    generate_embeddings_for_keyword,
    load_json_data
)

# Load environment variables from .env file
load_dotenv()

def connect_to_redis() -> Optional[redis.Redis]:
    """
    Connect to Redis database using environment variables.
    
    Returns:
        Redis client object or None if connection fails.
    """
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        print("Connected to Redis database")
        return redis_client
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return None

def store_similarity_data_in_redis(
    redis_client: redis.Redis,
    keyword: str,
    similarity_data: Dict[str, float],
    prompt_id: Optional[str] = None
) -> bool:
    """
    Store similarity data for a keyword in Redis.
    
    Args:
        redis_client: Redis client object.
        keyword: The keyword for which to store similarity data.
        similarity_data: Dictionary mapping words to similarity scores.
        prompt_id: Optional ID of the game this keyword belongs to.
        
    Returns:
        True if data was stored successfully, False otherwise.
    """
    try:
        # Keys for Redis
        keyword_lower = keyword.lower()
        similarity_key = f"similarity:{keyword_lower}"
        
        # Clear existing data for this keyword
        redis_client.delete(similarity_key)
        
        # Store new similarity data
        if len(similarity_data) > 0:
            # Use pipeline for better performance
            pipeline = redis_client.pipeline()
            for word, score in similarity_data.items():
                pipeline.hset(similarity_key, word, score)
            pipeline.execute()
            
            # If prompt ID is provided, create a reference
            if prompt_id:
                # Add this keyword to the game's keywords set
                redis_client.sadd(f"game:{prompt_id}:keywords", keyword_lower)
                
                # Set expiration for auto-cleanup (optional, 30 days)
                # redis_client.expire(similarity_key, 60 * 60 * 24 * 30)
        
        return True
    except Exception as e:
        print(f"Error storing similarity data in Redis for keyword '{keyword}': {e}")
        return False

def load_keyword_similarity(
    keyword: str,
    redis_client: Optional[redis.Redis] = None,
    regenerate: bool = False,
    base_dir: str = "../frontend/public",
    prompt_id: Optional[str] = None
) -> bool:
    """
    Load similarity data for a single keyword into Redis.
    
    Args:
        keyword: The keyword to process.
        redis_client: Optional Redis client (if None, will create one).
        regenerate: Whether to regenerate similarity data even if it exists.
        base_dir: Base directory for searching similarity files.
        prompt_id: Optional ID of the game this keyword belongs to.
    
    Returns:
        True if similarity data was loaded successfully, False otherwise.
    """
    close_redis = False
    try:
        # Create Redis connection if not provided
        if redis_client is None:
            redis_client = connect_to_redis()
            close_redis = True
            if not redis_client:
                return False
        
        keyword_lower = keyword.lower()
        redis_key = f"similarity:{keyword_lower}"
        
        # Check if data already exists
        if not regenerate and redis_client.exists(redis_key):
            count = redis_client.hlen(redis_key)
            print(f"Similarity data for '{keyword}' already exists in Redis with {count} entries")
            
            # Link to prompt if provided
            if prompt_id:
                redis_client.sadd(f"game:{prompt_id}:keywords", keyword_lower)
                print(f"Linked '{keyword}' to game '{prompt_id}'")
                
            return True
        
        # Look for a JSON file with similarity data
        similarity_file = os.path.join(
            os.path.dirname(__file__),
            base_dir,
            f"{keyword_lower}.json"
        )
        
        similarity_data = {}
        if os.path.exists(similarity_file) and not regenerate:
            # Load from file
            print(f"Loading similarity data from file for '{keyword}'")
            similarity_data = load_json_data(similarity_file)
        else:
            # Generate using spaCy
            print(f"Generating similarity data for '{keyword}' using spaCy")
            nlp = load_spacy_model()
            if not nlp:
                print("Failed to load spaCy model")
                return False
                
            similarity_data = generate_embeddings_for_keyword(keyword, nlp)
        
        if not similarity_data:
            print(f"Empty similarity data for '{keyword}'")
            return False
        
        # Store in Redis
        print(f"Storing {len(similarity_data)} similarity entries in Redis for '{keyword}'")
        success = store_similarity_data_in_redis(redis_client, keyword, similarity_data, prompt_id)
        
        if success:
            print(f"Successfully processed similarity data for '{keyword}'")
        else:
            print(f"Failed to store similarity data for '{keyword}' in Redis")
            
        return success
    
    except Exception as e:
        print(f"Error loading similarity data for '{keyword}': {e}")
        return False
    finally:
        if close_redis and redis_client:
            redis_client.close()

def load_game_similarity_data(
    game_file: str,
    redis_client: Optional[redis.Redis] = None,
    regenerate: bool = False,
    base_dir: str = "../frontend/public"
) -> Set[str]:
    """
    Load similarity data for all keywords in a game file.
    
    Args:
        game_file: Path to the game JSON file.
        redis_client: Optional Redis client (if None, will create one).
        regenerate: Whether to regenerate similarity data even if it exists.
        base_dir: Base directory for game files.
    
    Returns:
        Set of keywords that were successfully processed.
    """
    close_redis = False
    successful_keywords = set()
    try:
        # Create Redis connection if not provided
        if redis_client is None:
            redis_client = connect_to_redis()
            close_redis = True
            if not redis_client:
                return successful_keywords
        
        # Load game data from file
        full_path = os.path.join(os.path.dirname(__file__), base_dir, game_file.lstrip('/'))
        game_data = load_json_data(full_path)
        if not game_data:
            print(f"Failed to load game data from {game_file}")
            return successful_keywords
        
        # Extract prompt ID from filename
        prompt_id = os.path.basename(game_file).replace(".json", "")
        
        # Extract keywords
        keywords = game_data.get('keywords', [])
        if not keywords:
            print(f"No keywords found in game data for {game_file}")
            return successful_keywords
        
        print(f"Processing similarity data for {len(keywords)} keywords from {prompt_id}")
        
        # Process each keyword
        for keyword in keywords:
            success = load_keyword_similarity(
                keyword,
                redis_client,
                regenerate,
                base_dir,
                prompt_id
            )
            
            if success:
                successful_keywords.add(keyword)
        
        # Store a reference to this game's keywords count
        redis_client.set(f"game:{prompt_id}:count", len(keywords))
        
        print(f"Successfully processed {len(successful_keywords)} of {len(keywords)} keywords for {prompt_id}")
        return successful_keywords
    
    except Exception as e:
        print(f"Error loading game similarity data: {e}")
        return successful_keywords
    finally:
        if close_redis and redis_client:
            redis_client.close()

def find_game_files(files_dir: str = "../frontend/public") -> List[str]:
    """
    Find all random-*.json game files in the specified directory.
    
    Args:
        files_dir: Directory to search for game files.
    
    Returns:
        List of paths to game files.
    """
    import glob
    
    base_path = os.path.join(os.path.dirname(__file__), files_dir)
    game_files = glob.glob(os.path.join(base_path, "random-*.json"))
    
    if not game_files:
        print(f"No game files found in {base_path}")
    else:
        print(f"Found {len(game_files)} game files in {base_path}")
    
    # Sort by index number
    game_files.sort(key=lambda f: int(os.path.basename(f).replace("random-", "").replace(".json", "")))
    
    return game_files

def get_keyword_similarity_stats(
    keyword: str,
    redis_client: Optional[redis.Redis] = None
) -> Dict[str, Any]:
    """
    Get statistics about a keyword's similarity data in Redis.
    
    Args:
        keyword: The keyword to check.
        redis_client: Optional Redis client (if None, will create one).
    
    Returns:
        Dictionary with similarity statistics.
    """
    close_redis = False
    try:
        # Create Redis connection if not provided
        if redis_client is None:
            redis_client = connect_to_redis()
            close_redis = True
            if not redis_client:
                return {"error": "Failed to connect to Redis"}
        
        keyword_lower = keyword.lower()
        redis_key = f"similarity:{keyword_lower}"
        
        result = {
            "keyword": keyword,
            "exists": redis_client.exists(redis_key) > 0
        }
        
        if result["exists"]:
            # Get count
            result["count"] = redis_client.hlen(redis_key)
            
            # Get some sample entries (top 5 by score)
            all_entries = redis_client.hgetall(redis_key)
            sorted_entries = sorted(
                [(k, float(v)) for k, v in all_entries.items()],
                key=lambda x: x[1],
                reverse=True
            )
            result["samples"] = sorted_entries[:5]
            
            # Get games this keyword is linked to
            games = []
            for key in redis_client.keys("game:*:keywords"):
                game_id = key.split(":")[1]
                if redis_client.sismember(key, keyword_lower):
                    games.append(game_id)
            result["games"] = games
        
        return result
    
    except Exception as e:
        print(f"Error getting similarity stats: {e}")
        return {"error": str(e)}
    finally:
        if close_redis and redis_client:
            redis_client.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Load similarity data into Redis")
    
    # Main operation modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--game-file", help="Process a specific game file")
    group.add_argument("--keyword", help="Process a specific keyword")
    group.add_argument("--all", action="store_true", help="Process all game files")
    group.add_argument("--stats", help="Get stats for a keyword")
    
    # Common arguments
    parser.add_argument("--regenerate", action="store_true", help="Regenerate similarity data even if it exists")
    parser.add_argument("--files-dir", default="../frontend/public", help="Directory containing game files")
    
    args = parser.parse_args()
    
    if args.stats:
        # Get and display stats for a keyword
        stats = get_keyword_similarity_stats(args.stats)
        import json
        print(json.dumps(stats, indent=2))
        return
    
    if args.keyword:
        # Process a single keyword
        success = load_keyword_similarity(args.keyword, None, args.regenerate, args.files_dir)
        print(f"Keyword processing {'succeeded' if success else 'failed'}")
    
    elif args.game_file:
        # Process a specific game file
        keywords = load_game_similarity_data(args.game_file, None, args.regenerate, args.files_dir)
        print(f"Processed {len(keywords)} keywords")
    
    else:  # args.all
        # Process all game files
        game_files = find_game_files(args.files_dir)
        if not game_files:
            return
        
        # Process each game file
        total_keywords = 0
        for game_file in game_files:
            print(f"\nProcessing {os.path.basename(game_file)}")
            keywords = load_game_similarity_data(
                os.path.basename(game_file), 
                None, 
                args.regenerate, 
                args.files_dir
            )
            total_keywords += len(keywords)
        
        print(f"\nProcessing complete. Loaded similarity data for {total_keywords} keywords.")

if __name__ == "__main__":
    main()